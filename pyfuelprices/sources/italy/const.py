"""Italy (MIMIT Open Data CSV) constants.

Il MIMIT pubblica ogni giorno due file CSV pubblici aggiornati alle ore 8:
  - anagrafica: contiene i dati di ogni distributore (posizione, nome, ecc.)
  - prezzi:     contiene i prezzi comunicati dai gestori

Fonte: https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti
"""

# URL del file CSV con i prezzi del giorno (aggiornato ogni mattina alle 8)
MISE_PRICES_CSV_URL = (
    "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
)

# URL del file CSV con l'anagrafica di tutti gli impianti attivi
MISE_STATIONS_CSV_URL = (
    "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
)

# Dal 10 febbraio 2026 il separatore di campo è "|" (pipe)
MISE_CSV_SEPARATOR = "|"

# Header HTTP per sembrare un browser normale
MISE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Referer": "https://www.mimit.gov.it/",
}

# Mapping dai nomi carburante del MISE ai codici standard di pyfuelprices
MISE_FUEL_MAPPING = {
    "Benzina":          "BENZINA",   # SP95 / E10
    "Gasolio":          "GASOLIO",   # Diesel B7
    "GPL":              "GPL",       # Autogas LPG
    "Metano":           "METANO",    # CNG
    "Metano L-GNC":     "LGNC",      # Metano liquefatto rigassificato
    "GNL":              "GNL",       # Gas Naturale Liquefatto
    "HVO":              "HVO",       # Olio vegetale idrotrattato
}
