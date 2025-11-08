"""Shell UK dataprovider."""

import logging
import json

from datetime import datetime
from pyfuelprices.const import DESKTOP_USER_AGENT
from pyfuelprices.sources import UpdateFailedError
from pyfuelprices.sources.uk import CMAParser, FuelLocation

_LOGGER = logging.getLogger(__name__)

class ShellUKSource(CMAParser):
    """Shell UK uses the CMA parser although requires custom request handlers."""

    _url = ("https://prodpricinghubstrgacct.blob.core.windows.net/ukcma/fuel-prices-data.json"
            "?sp=r&st=2025-11-07T06:00:49Z&se=2026-11-07T14:07:49Z&spr=https&"
            "sv=2024-11-04&sr=b&sig=V1o+ZNwZT9KEvmvLuCv25ittu9Hh90JwtfE+tc1PAtA=")
    provider_name = "shelluk"
    _headers = {
        "User-Agent": DESKTOP_USER_AGENT
    }
    location_cache: dict[str, FuelLocation] = {}
    location_tree = None

    async def update(self, areas=None, force=False) -> list[FuelLocation]:
        """Update hooks for the data source."""
        if datetime.now() > self.next_update or force:
            _LOGGER.debug("Starting update hook for %s to url %s", self.provider_name, self._url)
            async with self._client_session.request(
                url=self._url,
                method=self._method,
                json=self._request_body,
                headers=self._headers
            ) as response:
                _LOGGER.debug("Update request completed for %s with status %s",
                              self.provider_name, response.status)
                if response.status == 200:
                    self.next_update += self.update_interval
                    # convert octet stream to json
                    try:
                        js = json.loads(await response.text())
                        return await self.parse_response(
                            response=js
                        )
                    except Exception as exc:
                        raise UpdateFailedError(
                            status=response.status,
                            response="Invalid response provided.",
                            headers=response.headers,
                            service=self.provider_name
                        ) from exc
                raise UpdateFailedError(
                    status=response.status,
                    response=await response.text(),
                    headers=response.headers,
                    service=self.provider_name
                )
