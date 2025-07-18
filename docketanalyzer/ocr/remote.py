import base64
import json
import time
from collections.abc import Generator
from typing import Any

import requests

from docketanalyzer import env


class RemoteClient:
    """Client for making API calls to remote endpoints.

    This class handles communication with remote serverless endpoints, including
    authentication, request formatting, and streaming response handling.
    """

    def __init__(self, api_key: str | None = None, endpoint_url: str | None = None):
        """Initialize the remote client.

        Args:
            api_key: API key for authentication. If None, uses RUNPOD_API_KEY
                from environment.
            endpoint_url: Full endpoint URL. If None, constructs URL from
                RUNPOD_OCR_ENDPOINT_ID or defaults to localhost.
        """
        self.api_key = api_key or env.RUNPOD_API_KEY

        if endpoint_url:
            self.base_url = endpoint_url
        elif env.RUNPOD_OCR_ENDPOINT_ID:
            self.base_url = f"https://api.runpod.ai/v2/{env.RUNPOD_OCR_ENDPOINT_ID}"
        else:
            self.base_url = "http://localhost:8000"

        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def __call__(
        self,
        s3_key: str | None = None,
        file: bytes | None = None,
        filename: str | None = None,
        batch_size: int = 1,
        stream: bool = True,
        timeout: int = 300,
        poll_interval: float = 1.0,
        **kwargs: Any,
    ) -> list[dict[str, Any]] | Generator[dict[str, Any], None, None]:
        """Make a request to the remote endpoint.

        Args:
            s3_key: S3 key to the PDF file. Either s3_key or file must be provided.
            file: Binary PDF data or base64-encoded string. Either s3_key or
                file must be provided.
            filename: Optional filename for the PDF.
            batch_size: Batch size for processing. Defaults to 1.
            stream: Whether to stream the response. Defaults to True.
            timeout: Request timeout in seconds. Defaults to 600 (10 minutes).
            poll_interval: Interval in seconds between status checks. Defaults to 1.0.
            **kwargs: Additional parameters to include in the input payload.

        Returns:
            If stream=True, returns a generator yielding response chunks.
            If stream=False, returns a list of all response chunks.

        Raises:
            ValueError: If neither s3_key nor file is provided.
            TimeoutError: If the request times out.
        """
        if not s3_key and not file:
            raise ValueError("Either s3_key or file must be provided")

        input_data = {"batch_size": batch_size}

        if s3_key:
            input_data["s3_key"] = s3_key
        if file:
            if isinstance(file, bytes):
                file = base64.b64encode(file).decode("utf-8")
            input_data["file"] = file
        if filename:
            input_data["filename"] = filename

        input_data.update(kwargs)

        payload = {"input": input_data}

        job_id = self._submit_job(payload, timeout)

        if stream:
            return self._stream_results(job_id, timeout, poll_interval)
        else:
            results = []
            for chunk in self._stream_results(job_id, timeout, poll_interval):
                results.append(chunk)
                if chunk.get("status") == "COMPLETED":
                    break
            return results

    def _submit_job(self, payload: dict[str, Any], timeout: int) -> str:
        """Submit a job to the remote endpoint.

        Args:
            payload: The request payload.
            timeout: Request timeout in seconds.

        Returns:
            str: The job ID.

        Raises:
            requests.RequestException: If the request fails.
            ValueError: If the response format is invalid or cannot be parsed.
        """
        url = f"{self.base_url}/run"

        response = requests.post(
            url, headers=self.headers, json=payload, timeout=timeout
        )
        response.raise_for_status()

        result = response.json()
        if "id" not in result:
            raise ValueError(f"Invalid response format, missing 'id': {result}")
        return result["id"]

    def _stream_results(
        self, job_id: str, timeout: int, poll_interval: float
    ) -> Generator[dict[str, Any], None, None]:
        """Stream results from a job.

        Args:
            job_id: The job ID.
            timeout: Maximum time to wait for results in seconds.
            poll_interval: Interval between status checks in seconds.

        Yields:
            Dict[str, Any]: Each chunk of the streaming response.

        Raises:
            requests.RequestException: If the request fails.
            ValueError: If the response format is invalid.
            TimeoutError: If the request times out.
        """
        url = f"{self.base_url}/stream/{job_id}"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                with requests.post(
                    url, headers=self.headers, stream=True, timeout=timeout
                ) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if not line:
                                continue

                            data = json.loads(line.decode("utf-8"))
                            yield data

                            if data.get("status") in [
                                "COMPLETED",
                                "FAILED",
                                "CANCELLED",
                            ]:
                                return
                    elif response.status_code == 404:
                        time.sleep(poll_interval)
                    else:
                        response.raise_for_status()

            except requests.exceptions.ChunkedEncodingError:
                time.sleep(poll_interval)
                continue

        raise TimeoutError(f"Streaming results timed out after {timeout} seconds")

    def get_status(self, job_id: str, timeout: int = 30) -> dict[str, Any]:
        """Get the status of a job.

        Args:
            job_id: The job ID.
            timeout: Request timeout in seconds.

        Returns:
            Dict[str, Any]: The job status.

        Raises:
            requests.RequestException: If the request fails.
            ValueError: If the response format is invalid.
        """
        url = f"{self.base_url}/status/{job_id}"

        response = requests.post(url, headers=self.headers, timeout=timeout)
        response.raise_for_status()

        return response.json()

    def cancel_job(self, job_id: str, timeout: int = 30) -> dict[str, Any]:
        """Cancel a job.

        Args:
            job_id: The job ID.
            timeout: Request timeout in seconds.

        Returns:
            Dict[str, Any]: The cancellation response.

        Raises:
            requests.RequestException: If the request fails.
            ValueError: If the response format is invalid.
        """
        url = f"{self.base_url}/cancel/{job_id}"

        response = requests.post(url, headers=self.headers, timeout=timeout)
        response.raise_for_status()

        return response.json()

    def purge_queue(self, timeout: int = 30) -> dict[str, Any]:
        """Purge all queued jobs.

        Args:
            timeout: Request timeout in seconds.

        Returns:
            Dict[str, Any]: The purge response.

        Raises:
            requests.RequestException: If the request fails.
            ValueError: If the response format is invalid.
        """
        url = f"{self.base_url}/purge-queue"

        response = requests.post(url, headers=self.headers, timeout=timeout)
        response.raise_for_status()

        return response.json()

    def get_health(self, timeout: int = 30) -> dict[str, Any]:
        """Get endpoint health information.

        Args:
            timeout: Request timeout in seconds.

        Returns:
            Dict[str, Any]: The health information.

        Raises:
            requests.RequestException: If the request fails.
            ValueError: If the response format is invalid.
        """
        url = f"{self.base_url}/health"

        response = requests.get(url, headers=self.headers, timeout=timeout)
        response.raise_for_status()

        return response.json()
