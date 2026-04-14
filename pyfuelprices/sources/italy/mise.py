"""Italy MIMIT Open Data CSV source per pyfuelprices.

Come funziona:
  Il MIMIT pubblica ogni mattina alle 8 due file CSV pubblici:
    1. anagrafica_impianti_attivi.csv  ->  posizione e dati di ogni distributore
    2. prezzo_alle_8.csv               ->  prezzi comunicati dai gestori

  Questo modulo scarica entrambi i file, li unisce tramite l'ID impianto,
  e costruisce la lista di FuelLocation compatibile con pyfuelprices.
"""

import logging
import io
import csv
import math
from datetime import timedelta, datetime

from pyfuelprices.const import (
    PROP_FUEL_LOCATION_SOURCE,
    PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP,
    PROP_FUEL_LOCATION_SOURCE_ID,
)
from pyfuelprices.sources import Source
from pyfuelprices.fuel_locations import Fuel, FuelLocation

from .const import (
    MISE_PRICES_CSV_URL,
    MISE_STATIONS_CSV_URL,
    MISE_CSV_SEPARATOR,
    MISE_HEADERS,
    MISE_FUEL_MAPPING,
)

_LOGGER = logging.getLogger(__name__)


class MISESource(Source):
    """Sorgente dati carburanti Italia - MIMIT Open Data CSV.

    Utilizza i file CSV ufficiali pubblicati ogni giorno dal Ministero
    delle Imprese e del Made in Italy (MIMIT).

    Documentazione:
      https://www.mimit.gov.it/it/open-data/elenco-dataset/
      carburanti-prezzi-praticati-e-anagrafica-degli-impianti
    """

    country_code = "IT"
    provider_name = "mise_italy"

    _headers = MISE_HEADERS
    update_interval = timedelta(hours=12)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIX: location_cache come attributo di istanza, non di classe,
        # per evitare che due istanze condividano la stessa cache.
        self.location_cache: dict[str, FuelLocation] = {}

    # ------------------------------------------------------------------
    # Download CSV
    # ------------------------------------------------------------------

    async def _download_csv(self, url: str) -> str | None:
        """Scarica un file CSV dall'URL indicato e restituisce il testo."""
        _LOGGER.debug("MISE Italy: scarico CSV da %s", url)
        async with self._client_session.get(url, headers=self._headers) as resp:
            if resp.ok:
                raw_bytes = await resp.read()
                # FIX: prova prima UTF-8 (encoding piu' moderno e sicuro),
                # poi latin-1 come fallback. latin-1 non fallisce mai quindi
                # deve stare per secondo.
                try:
                    return raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    return raw_bytes.decode("latin-1", errors="replace")
            _LOGGER.error(
                "MISE Italy: errore HTTP %s scaricando %s", resp.status, url
            )
            return None

    # ------------------------------------------------------------------
    # Parsing CSV
    # ------------------------------------------------------------------

    def _parse_stations_csv(self, text: str) -> dict[str, dict]:
        """Legge il CSV anagrafica e restituisce un dizionario id->dati.

        Il CSV inizia con una riga di metadati tipo 'Estrazione del 2026-04-12'
        che viene saltata con next(f) prima di passare al DictReader.
        """
        stations = {}
        # FIX: uso un iteratore StringIO invece di splitlines()+join(),
        # evitando di duplicare l'intero CSV in memoria.
        f = io.StringIO(text)
        next(f)  # salta la riga "Estrazione del ..."
        reader = csv.DictReader(f, delimiter=MISE_CSV_SEPARATOR)
        for row in reader:
            sid = row.get("idImpianto", "").strip()
            if not sid:
                continue
            try:
                lat = float(row.get("Latitudine", "0").replace(",", "."))
                lon = float(row.get("Longitudine", "0").replace(",", "."))
            except ValueError:
                lat, lon = 0.0, 0.0
            if lat == 0.0 and lon == 0.0:
                continue
            stations[sid] = {
                "id":        sid,
                "gestore":   row.get("Gestore", "").strip(),
                "bandiera":  row.get("Bandiera", "").strip(),
                "nome":      row.get("Nome Impianto", "").strip(),
                "indirizzo": row.get("Indirizzo", "").strip(),
                "comune":    row.get("Comune", "").strip(),
                "provincia": row.get("Provincia", "").strip(),
                "lat":       lat,
                "lon":       lon,
            }
        _LOGGER.debug("MISE Italy: lette %d stazioni dall'anagrafica", len(stations))
        return stations

    def _parse_prices_csv(self, text: str) -> dict[str, list]:
        """Legge il CSV prezzi e restituisce un dizionario id->lista prezzi.

        Il CSV inizia con una riga di metadati tipo 'Estrazione del 2026-04-12'
        che viene saltata con next(f) prima di passare al DictReader.
        """
        prices: dict[str, list] = {}
        # FIX: stessa ottimizzazione memoria del parser anagrafica.
        f = io.StringIO(text)
        next(f)  # salta la riga "Estrazione del ..."
        reader = csv.DictReader(f, delimiter=MISE_CSV_SEPARATOR)
        for row in reader:
            sid = row.get("idImpianto", "").strip()
            if not sid:
                continue
            try:
                price = float(row.get("prezzo", "0").replace(",", "."))
            except ValueError:
                continue
            if price <= 0:
                continue
            prices.setdefault(sid, []).append({
                "descCarburante": row.get("descCarburante", "").strip(),
                "prezzo":         price,
                "isSelf":         row.get("isSelf", "0").strip() == "1",
            })
        _LOGGER.debug("MISE Italy: letti prezzi per %d stazioni", len(prices))
        return prices

    # ------------------------------------------------------------------
    # pyfuelprices Source interface
    # ------------------------------------------------------------------

    async def update(self, areas=None, force=False) -> list[FuelLocation]:
        """Scarica i due CSV e aggiorna la cache completa."""
        if self.next_update > datetime.now() and not force:
            _LOGGER.debug("MISE Italy: aggiornamento non necessario")
            return list(self.location_cache.values())

        _LOGGER.debug("MISE Italy: avvio aggiornamento dati")

        stations_text = await self._download_csv(MISE_STATIONS_CSV_URL)
        prices_text   = await self._download_csv(MISE_PRICES_CSV_URL)

        if stations_text is None or prices_text is None:
            _LOGGER.error(
                "MISE Italy: impossibile scaricare i CSV, aggiornamento saltato"
            )
            return list(self.location_cache.values())

        stations_raw = self._parse_stations_csv(stations_text)
        prices_raw   = self._parse_prices_csv(prices_text)

        for sid, station in stations_raw.items():
            if sid not in prices_raw:
                continue

            loc = self._build_location(station, prices_raw[sid])
            if loc.id not in self.location_cache:
                self.location_cache[loc.id] = loc
            else:
                await self.location_cache[loc.id].update(loc)

        self.next_update = datetime.now() + self.update_interval
        _LOGGER.debug(
            "MISE Italy: cache aggiornata con %d stazioni", len(self.location_cache)
        )
        return list(self.location_cache.values())

    # FIX: rimosso search_sites personalizzato — la classe base Source
    # gestisce gia' la ricerca per distanza usando geopy, che e' gia'
    # una dipendenza del progetto. Sovrascriverlo era ridondante.

    async def update_area(self, area: dict) -> bool:
        """Richiesto dalla classe base; deleghiamo tutto a update()."""
        await self.update()
        return True

    async def parse_response(self, response) -> list[FuelLocation]:
        """Non usato in questa implementazione."""
        return list(self.location_cache.values())

    # ------------------------------------------------------------------
    # Costruzione FuelLocation
    # ------------------------------------------------------------------

    def _build_location(self, station: dict, raw_prices: list) -> FuelLocation:
        """Crea un oggetto FuelLocation dai dati di una stazione."""
        site_id = f"{self.provider_name}_{station['id']}"
        brand   = station["bandiera"] or station["gestore"]
        name    = station["nome"] or brand
        address = ", ".join(filter(None, [
            station["indirizzo"],
            station["comune"],
            station["provincia"],
        ]))

        loc = FuelLocation.create(
            site_id=site_id,
            name=name,
            address=address,
            lat=station["lat"],
            long=station["lon"],
            brand=brand,
            available_fuels=self.parse_fuels(raw_prices),
            postal_code="",
            currency="EUR",
            props={
                PROP_FUEL_LOCATION_SOURCE:                self.provider_name,
                PROP_FUEL_LOCATION_SOURCE_ID:             station["id"],
                PROP_FUEL_LOCATION_PREVENT_CACHE_CLEANUP: True,
            },
        )
        loc.next_update = (
            self.next_update
            if self.next_update > datetime.now()
            else self.next_update + self.update_interval
        )
        return loc

    def parse_fuels(self, raw_prices: list) -> list[Fuel]:
        """Converte la lista prezzi in oggetti Fuel, preferendo il self-service."""
        best: dict[str, float] = {}
        for entry in raw_prices:
            raw_name = entry.get("descCarburante", "")
            fuel_key = MISE_FUEL_MAPPING.get(raw_name, raw_name.upper())
            price    = entry.get("prezzo", 0.0)
            is_self  = entry.get("isSelf", False)
            if fuel_key not in best or is_self:
                best[fuel_key] = price
        return [Fuel(fuel_type=k, cost=v, props={}) for k, v in best.items()]

