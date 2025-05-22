from contextlib import suppress
from datetime import date
from typing import Any

import regex as re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from docketanalyzer import construct_docket_id, env, parse_docket_id


class Pacer:
    """Utility for downloading PACER data.

    Convenience wrapper around
        [Free Law Project's juriscraper](https://github.com/freelawproject/juriscraper)
        for downloading dockets and documents from PACER.

    Args:
        pacer_username (str, optional): PACER account username.
            If not provided, will use saved config or PACER_USERNAME from environment.
        pacer_password (str, optional): PACER account password.
            If not provided, will use saved config or PACER_PASSWORD from environment.

    Attributes:
        pacer_username (str): The PACER account username
        pacer_password (str): The PACER account password
        cache (dict): Internal cache for storing session and driver instances
    """

    def __init__(
        self, pacer_username: str | None = None, pacer_password: str | None = None
    ):
        """Initializes the Pacer class with the provided PACER credentials."""
        self.pacer_username = pacer_username or env.PACER_USERNAME
        self.pacer_password = pacer_password or env.PACER_PASSWORD
        self.cache = {}

    @property
    def driver(self) -> webdriver:
        """Returns a Selenium WebDriver instance ."""
        if "driver" not in self.cache:
            options = Options()
            options.add_argument("--headless")
            service = Service()
            self.cache["driver"] = webdriver.Firefox(options=options, service=service)
        return self.cache["driver"]

    @property
    def session(self) -> "PacerSession":  # noqa: F821
        """Returns a PacerSession instance."""
        from juriscraper.pacer import PacerSession

        if "session" not in self.cache:
            self.cache["session"] = PacerSession(
                username=self.pacer_username, password=self.pacer_password
            )
            self.cache["session"].selenium = self.driver
        return self.cache["session"]

    def __del__(self):
        """Destructor to clean up the session and driver instances."""
        if self.cache.get("driver") is not None:
            with suppress(Exception):
                self.driver.quit()

    def find_candidate_cases(self, docket_id: str) -> list[dict[str, str]]:
        """Finds candidate PACER cases for a given docket ID.

        Args:
            docket_id (str): The docket ID to search for.

        Returns:
            list: A list of candidate cases.
        """
        from juriscraper.lib.string_utils import force_unicode
        from juriscraper.pacer import PossibleCaseNumberApi

        court, docket_number = parse_docket_id(docket_id)
        case_numbers = PossibleCaseNumberApi(court, self.session)
        case_numbers.query(docket_number)

        return [
            {
                "docket_number": force_unicode(node.xpath("./@number")[0]),
                "pacer_case_id": force_unicode(node.xpath("./@id")[0]),
                "title": force_unicode(node.xpath("./@title")[0]),
            }
            for node in case_numbers.tree.xpath("//case")
        ]

    def purchase_docket(self, docket_id: str, **kwargs: Any) -> tuple[str, dict]:
        """Purchases a docket for a given docket ID.

        Args:
            docket_id (str): The docket ID to purchase.
            **kwargs: Additional query arguments to pass to juriscraper.

        Returns:
            tuple: A tuple containing the raw HTML and the parsed docket JSON.
        """
        court, _ = parse_docket_id(docket_id)
        pacer_case_id = self.find_candidate_cases(docket_id)[0]["pacer_case_id"]
        return self.purchase_docket_with_pacer_case_id(court, pacer_case_id, **kwargs)

    def purchase_docket_with_pacer_case_id(
        self,
        court: str,
        pacer_case_id: str,
        date_start: date | None = None,
        date_end: date | None = None,
        show_parties_and_counsel: bool = True,
        show_terminated_parties: bool = True,
        show_list_of_member_cases: bool = True,
        **kwargs: Any,
    ) -> tuple[str, dict]:
        """Purchases a docket for a given PACER case ID.

        Args:
            court (str): The court to purchase the docket from.
            pacer_case_id (str): The PACER case ID to purchase.
            date_start (date, optional): The start date for the docket search.
            date_end (date, optional): The end date for the docket search.
            show_parties_and_counsel (bool, optional): Whether to show parties
                and counsel.
            show_terminated_parties (bool, optional): Whether to show
                terminated parties.
            show_list_of_member_cases (bool, optional): Whether to show
                list of member cases.
            **kwargs: Additional query arguments to pass to juriscraper.

        Returns:
            tuple: A tuple containing the raw HTML and the parsed docket JSON.
        """
        from juriscraper.pacer import DocketReport

        docket_report = DocketReport(court, self.session)
        docket_report.query(
            pacer_case_id,
            date_start=date_start,
            date_end=date_end,
            show_parties_and_counsel=show_parties_and_counsel,
            show_terminated_parties=show_terminated_parties,
            show_list_of_member_cases=show_list_of_member_cases,
            **kwargs,
        )
        docket_html = docket_report.response.text
        docket_html = self.add_pacer_case_id_to_docket_html(docket_html, pacer_case_id)
        docket_json = docket_report.data
        docket_json["docket_id"] = construct_docket_id(
            court, docket_json["docket_number"]
        )
        docket_json["pacer_case_id"] = pacer_case_id
        return docket_html, docket_json

    def parse(self, docket_html: str, court: str) -> dict:
        """Parses the raw HTML of a docket and returns the parsed docket JSON.

        Args:
            docket_html (str): The raw HTML of the docket.
            court (str): The court to parse the docket from.

        Returns:
            dict: The parsed docket JSON.
        """
        from juriscraper.pacer import DocketReport

        parser = DocketReport(court)
        parser._parse_text(docket_html)
        docket_json = parser.data
        docket_json["docket_id"] = construct_docket_id(
            court, docket_json["docket_number"]
        )
        match = re.search(r"<!--PACER CASE ID: (.*?)-->", docket_html)
        if match:
            docket_json["pacer_case_id"] = match.group(1)
        return docket_json

    def get_attachments(self, pacer_doc_id: str, court: str) -> dict:
        """Retrieves the attachments for a given PACER document ID."""
        from juriscraper.pacer import AttachmentPage

        attachment_report = AttachmentPage(court, self.session)
        attachment_report.query(pacer_doc_id)
        return attachment_report.data

    def purchase_document(
        self, pacer_case_id: str, pacer_doc_id: str, court: str
    ) -> tuple[bytes, str]:
        """Purchases a document for a given PACER case ID and document ID.

        Args:
            pacer_case_id (str): The PACER case ID to purchase the document from.
            pacer_doc_id (str): The PACER document ID to purchase.
            court (str): The court to purchase the document from.

        Returns:
            tuple: A tuple containing the PDF content and the status of the purchase.
        """
        from juriscraper.pacer import DocketReport

        docket_report = DocketReport(court, self.session)
        r, status = docket_report.download_pdf(pacer_case_id, pacer_doc_id)
        pdf = r.content if r else None
        status = status if status else "success"
        return pdf, status

    def purchase_attachment(
        self, pacer_case_id: str, pacer_doc_id: str, attachment_number: str, court: str
    ) -> tuple[bytes, str]:
        """Purchases an attachment for a given PACER case ID and document ID.

        Args:
            pacer_case_id (str): The PACER case ID to purchase the attachment from.
            pacer_doc_id (str): The PACER document ID to purchase the attachment from.
            attachment_number (str): The attachment number to purchase.
            court (str): The court to purchase the attachment from.

        Returns:
            tuple: A tuple containing the PDF content and the status of the purchase.
        """
        from juriscraper.pacer import AttachmentPage

        attachments = AttachmentPage(court, self.session)
        attachments.query(pacer_doc_id)
        attachments = attachments.data["attachments"]
        for attachment in attachments:
            if int(attachment["attachment_number"]) == int(attachment_number):
                return self.purchase_document(
                    pacer_case_id, attachment["pacer_doc_id"], court
                )
        return None, "error"

    def add_pacer_case_id_to_docket_html(
        self, docket_html: str, pacer_case_id: str
    ) -> str:
        """Adds the PACER case ID to the docket HTML if it is not already present.

        Args:
            docket_html (str): The raw HTML of the docket.
            pacer_case_id (str): The PACER case ID to add to the docket HTML.

        Returns:
            str: The docket HTML with the PACER case ID added.
        """
        if not re.search(r"<!--PACER CASE ID: (.*?)-->", docket_html):
            docket_html += f"<!--PACER CASE ID: {pacer_case_id}-->"
        return docket_html
