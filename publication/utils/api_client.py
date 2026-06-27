"""HTTP API client with exponential backoff retry."""

from __future__ import annotations

import time
from typing import Any

import requests
from loguru import logger


class APIClient:
    """Base REST client with retry logic."""

    def __init__(
        self,
        base_url: str = "",
        token: str | None = None,
        token_header: str = "Authorization",
        token_prefix: str = "Bearer ",
        max_retries: int = 5,
        backoff_factor: float = 1.0,
        timeout: int = 60,
        mock_mode: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.token_header = token_header
        self.token_prefix = token_prefix
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.mock_mode = mock_mode
        self.session = requests.Session()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers[self.token_header] = f"{self.token_prefix}{self.token}".strip()
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        expected_status: tuple[int, ...] = (200, 201, 202),
    ) -> dict[str, Any] | list[Any] | None:
        if self.mock_mode:
            logger.debug("Mock mode: skipping HTTP {} {}", method, path)
            return None

        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=self._headers(),
                    json=json,
                    data=data,
                    files=files,
                    params=params,
                    timeout=self.timeout,
                )
                if response.status_code in expected_status:
                    if response.content:
                        return response.json()
                    return {}
                if response.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(
                        f"{response.status_code}: {response.text[:200]}",
                        response=response,
                    )
                response.raise_for_status()
                return response.json() if response.content else {}
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                wait = self.backoff_factor * (2**attempt)
                logger.warning(
                    "Request failed (attempt {}/{}): {} — retry in {:.1f}s",
                    attempt + 1,
                    self.max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)

        raise RuntimeError(f"API request failed after {self.max_retries} retries: {last_error}")

    def poll_status(
        self,
        path: str,
        *,
        status_key: str = "status",
        success_values: tuple[str, ...] = ("published", "done", "complete"),
        pending_values: tuple[str, ...] = ("pending", "processing", "submitted", "in_review"),
        interval: float = 5.0,
        max_attempts: int = 12,
    ) -> dict[str, Any]:
        """Poll an endpoint until success or timeout."""
        if self.mock_mode:
            return {"status": success_values[0], "mock": True}

        for attempt in range(max_attempts):
            result = self.request("GET", path)
            if not isinstance(result, dict):
                time.sleep(interval)
                continue
            status = str(result.get(status_key, "")).lower()
            if status in success_values:
                return result
            if status not in pending_values:
                logger.warning("Unexpected status '{}': {}", status, result)
            logger.info("Polling {} — status={} ({}/{})", path, status, attempt + 1, max_attempts)
            time.sleep(interval)

        raise TimeoutError(f"Polling timed out for {path}")
