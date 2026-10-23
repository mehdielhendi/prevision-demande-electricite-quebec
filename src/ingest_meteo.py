"""Télécharge la météo horaire (UTC) d'Environnement Canada pour 3 stations."""

import time
from pathlib import Path

import requests

URL = "https://climate.weather.gc.ca/climate_data/bulk_data_e.html"
STATIONS = {
    "montreal": "7025251",
    "quebec": "7016293",
    "sherbrooke": "7028123",
}
DOSSIER = Path("data/raw/meteo")

# La demande va du 1er janv. 2019 au 1er janv. 2024 (en UTC) : on prend tous ces mois.
MOIS = [(annee, mois) for annee in range(2019, 2024) for mois in range(1, 13)] + [(2024, 1)]


def telecharger(ville: str, climate_id: str, annee: int, mois: int) -> None:
    """Télécharge un mois de données horaires d'une station en CSV."""
    chemin = DOSSIER / ville / f"{annee}-{mois:02d}.csv"
    if chemin.exists():
        return
    params = {
        "format": "csv",
        "climate_id": climate_id,
        "Year": annee,
        "Month": mois,
        "Day": 1,
        "time": "UTC",  # heures en UTC, sans changement d'heure
        "timeframe": 1,  # 1 = horaire
        "submit": "Download Data",
    }
    reponse = requests.get(URL, params=params, timeout=60)
    reponse.raise_for_status()
    chemin.write_bytes(reponse.content)
    time.sleep(0.5)  # politesse envers le serveur public


def main() -> None:
    for ville, climate_id in STATIONS.items():
        (DOSSIER / ville).mkdir(parents=True, exist_ok=True)
        for annee, mois in MOIS:
            telecharger(ville, climate_id, annee, mois)
        print(f"{ville} : {len(MOIS)} mois téléchargés")


if __name__ == "__main__":
    main()