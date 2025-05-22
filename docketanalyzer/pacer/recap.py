import logging
import time
from typing import Any
from urllib.parse import urlencode

import requests
from tqdm import tqdm

from docketanalyzer import env, parse_docket_id

PACER_TO_CL_COURT = {
    "azb": "arb",
    "cofc": "uscfc",
    "neb": "nebraskab",
    "nysb-mega": "nysb",
}


class RecapResponse:
    """Represents a response from the CourtListener API.

    Attributes:
        recap: The Recap instance that made the request.
        count: The total number of results.
        results: A list of results.
        next: The URL for the next page of results.
        previous: The URL for the previous page of results.
    """

    def __init__(
        self,
        recap: "RecapAPI",
        count: int,
        results: list[dict],
        next: str | None = None,
        previous: str | None = None,
    ):
        """Initialize the RecapResponse instance."""
        self.recap = recap
        self.count = count
        self.results = results
        self.next = next
        self.previous = previous

    def previous_page(self) -> "RecapResponse":
        """Get the previous page of results."""
        if self.previous:
            return self.recap.get(self.previous)
        return None

    def next_page(self) -> "RecapResponse":
        """Get the next page of results."""
        if self.next:
            return self.recap.get(self.next)
        return None

    def all_pages(self) -> "RecapResponse":
        """Get all results across all pages."""
        data = self.results.copy()
        r = self
        results_per_page = len(data)
        total_pages = 0
        if isinstance(self.count, int):
            total_pages = self.count // results_per_page + (
                1 if self.count % results_per_page else 0
            )
        pbar = tqdm(
            total=total_pages,
            desc="Accumulating results",
            initial=1,
        )
        while r.next:
            pbar.update(1)
            r = r.next_page()
            data += r.results
        return RecapResponse(self.recap, count=self.count, results=data)


class RecapAPI:
    """A class to interact with the RECAP API.

    This class provides methods to access and retrieve data from the RECAP API.
    It allows users to get information about courts, dockets, docket entries,
    parties, and attorneys.

    Attributes:
        base_url (str): The base URL for the RECAP API.
        api_key (str | None): The API key for authentication.
        sleep (int): The number of seconds to wait between requests.
        headers (dict): The headers to include in the API requests.
        docket_id_map (dict): A mapping of Docket Analyzer docket IDs to RECAP IDs.
    """

    def __init__(self, api_key: str | None = None, sleep: int = 0):
        """Initialize the Recap instance."""
        self.base_url = "https://www.courtlistener.com/api/rest/v4/"
        self.api_key = api_key or env.COURTLISTENER_TOKEN
        self.sleep = sleep

        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Token {self.api_key}"

        self.docket_id_map = {}

    def get(self, endpoint: str, **params) -> RecapResponse:
        """Make a GET request to the RECAP API."""
        if self.sleep:
            time.sleep(self.sleep)
        url = endpoint
        if self.base_url not in endpoint:
            url = f"{self.base_url}{endpoint}"
        if params:
            url = f"{url}/?{urlencode(params, doseq=True)}"
        logging.info(f"making request to {url}")
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        data = r.json()
        if "resource_uri" in data:
            data = {
                "count": 1,
                "results": [data],
            }
        return RecapResponse(self, **data)

    def courts(self):
        """Returns the courts in RECAP."""
        return self.get("courts")

    def get_recap_ids(
        self, docket_or_recap_id: str | int
    ) -> tuple[list[int], RecapResponse | None]:
        """Get the RECAP IDs and docket data (if collected) for a given docket_id."""
        if isinstance(docket_or_recap_id, int) or docket_or_recap_id.isdigit():
            return [int(docket_or_recap_id)], None
        elif docket_or_recap_id in self.docket_id_map:
            return self.docket_id_map[docket_or_recap_id], None
        else:
            court, docket_number = parse_docket_id(docket_or_recap_id)
            court = PACER_TO_CL_COURT.get(court, court)
            r = self.get(
                "dockets",
                court=court,
                docket_number=docket_number,
            )
            recap_ids = [result["id"] for result in r.results]
            self.docket_id_map[docket_or_recap_id] = recap_ids
            return recap_ids, r

    def dockets(
        self, docket_or_recap_id: str | int | None = None, **kwargs: Any
    ) -> RecapResponse:
        """Download docket data from RECAP.

        You can with either pass a Docket Analyzer docket_id or a RECAP ID.

        Args:
            docket_or_recap_id (str | int | None): The docket ID to search for.
            **kwargs: Additional query arguments to pass to the API.

        Returns:
            RecapResponse: A response object containing the results.
        """
        if docket_or_recap_id is not None:
            recap_ids, r = self.get_recap_ids(docket_or_recap_id)
            if r is not None:
                return r
            results = []
            for recap_id in recap_ids:
                results += self.get(f"dockets/{recap_id}").results
            return RecapResponse(self, count=len(results), results=results)
        return self.get("dockets", **kwargs)

    def entries(
        self, docket_or_recap_id: str | int | None = None, **kwargs: Any
    ) -> RecapResponse:
        """Download docket entries from RECAP.

        You can with either pass a Docket Analyzer docket_id or a RECAP ID.

        Args:
            docket_or_recap_id (str | int | None): The docket ID to search for.
            **kwargs: Additional query arguments to pass to the API.

        Returns:
            RecapResponse: A response object containing the results.
        """
        if docket_or_recap_id:
            recap_ids, _ = self.get_recap_ids(docket_or_recap_id)
            results = []
            for recap_id in recap_ids:
                r = self.get(
                    "docket-entries",
                    docket=recap_id,
                    order_by="recap_sequence_number",
                ).all_pages()
                for result in r.results:
                    result["docket_id"] = recap_id
                    results.append(result)
            return RecapResponse(self, count=len(results), results=results)
        return self.get("docket_entries", **kwargs)

    def parties(
        self,
        docket_or_recap_id: str | int | None = None,
        filter_nested_results: bool = True,
        **kwargs: Any,
    ) -> RecapResponse:
        """Download parties from RECAP.

        You can with either pass a Docket Analyzer docket_id or a RECAP ID.

        Args:
            docket_or_recap_id (str | int | None): The docket ID to search for.
            filter_nested_results (bool): Whether to apply filters to nested attorneys.
            **kwargs: Additional query arguments to pass to the API.

        Returns:
            RecapResponse: A response object containing the results.
        """
        if docket_or_recap_id:
            recap_ids, _ = self.get_recap_ids(docket_or_recap_id)
            results = []
            for recap_id in recap_ids:
                r = self.get(
                    "parties",
                    docket=recap_id,
                    filter_nested_results=filter_nested_results,
                ).all_pages()
                for result in r.results:
                    result["docket_id"] = recap_id
                    results.append(result)
            return RecapResponse(self, count=len(results), results=results)
        return self.get(
            "parties", filter_nested_results=filter_nested_results, **kwargs
        )

    def attorneys(
        self, docket_or_recap_id: str | int | None = None, **kwargs: Any
    ) -> RecapResponse:
        """Download attorneys from RECAP.

        You can with either pass a Docket Analyzer docket_id or a RECAP ID.

        Args:
            docket_or_recap_id (str | int | None): The docket ID to search for.
            **kwargs: Additional query arguments to pass to the API.

        Returns:
            RecapResponse: A response object containing the results.
        """
        if docket_or_recap_id:
            recap_ids, _ = self.get_recap_ids(docket_or_recap_id)
            results = []
            for recap_id in recap_ids:
                r = self.get("attorneys", docket=recap_id).all_pages()
                for result in r.results:
                    result["docket_id"] = recap_id
                    results.append(result)
            return RecapResponse(self, count=len(results), results=results)
        return self.get("attorneys", **kwargs)

    def consolidated_docket(
        self, docket_or_recap_id: str | int | None = None
    ) -> RecapResponse:
        """Download consolidated data for a case from RECAP.

        You can with either pass a Docket Analyzer docket_id or a RECAP ID.

        Args:
            docket_or_recap_id (str | int | None): The docket ID to search for.

        Returns:
            RecapResponse: A response object containing the results.
        """
        dockets = self.dockets(docket_or_recap_id).results
        data = []
        for docket in dockets:
            docket["docket_entries"] = self.entries(docket["id"]).results
            docket["parties"] = self.parties(docket["id"]).results
            attorneys = self.attorneys(docket["id"]).results
            attorneys = {x["id"]: x for x in attorneys}
            for party in docket["parties"]:
                for i in range(len(party["attorneys"])):
                    party["attorneys"][i].update(
                        attorneys[party["attorneys"][i]["attorney_id"]]
                    )
            data.append(docket)
        return RecapResponse(
            self,
            count=len(data),
            results=data,
        )
