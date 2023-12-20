"""Data sources and translators for pyfuelprices."""

import logging
import json

from datetime import timedelta, datetime

import aiohttp

from pyfuelprices.fuel_locations import FuelLocation, Fuel

_LOGGER = logging.getLogger(__name__)

class Source:
    """Base source, all instances inherit this."""

    _url: str = ""
    _method: str = "GET"
    _request_body: dict | None = None
    _headers: dict = {}
    _location_ids: list[int] = []
    _raw_data = None
    _timeout: int = 30
    update_interval: timedelta | None = None
    next_update: datetime | None = None
    provider_name: str = ""

    def __init__(self, update_interval: timedelta = timedelta(days=1)) -> None:
        """Start a new instance of a source."""
        self.update_interval = update_interval
        self._client_session: aiohttp.ClientSession = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._timeout),
            headers=self._headers
        )
        if self.next_update is None:
            self.next_update = datetime.now()

    async def update(self) -> list[FuelLocation]:
        """Update hooks for the data source."""
        _LOGGER.debug("Starting update hook for %s to url %s", self.provider_name, self._url)
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._timeout),
            headers=self._headers
        ) as session:
            response = await session.request(
                method=self._method,
                url=self._url,
                json=self._request_body
            )
            _LOGGER.debug("Update request completed for %s with status %s",
                        self.provider_name, response.status)
            if response.status == 200:
                self.next_update += self.update_interval
                if "application/json" not in response.content_type:
                    return self.parse_response(
                        response=json.loads(await response.text())
                    )
                return self.parse_response(
                    response=await response.json()
                )
            raise UpdateFailedError(
                status=response.status,
                response=await response.text(),
                headers=response.headers
            )

    def parse_response(self, response) -> list[FuelLocation]:
        """Parses the response from the update hook."""
        raise NotImplementedError("This function is not available for this module.")

    def parse_fuels(self, fuels) -> list[Fuel]:
        """Parses the fuels response from the update hook.
        This is used as part of parse_response."""
        raise NotImplementedError("This function is not available for this module.")


class UpdateFailedError(Exception):
    """Update failure exception."""

    def __init__(self, status: int, response: str, headers: dict) -> None:
        self.status = status
        self.response = response
        self.headers = headers
