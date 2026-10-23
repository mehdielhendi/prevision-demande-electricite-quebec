"""Télécharge l'historique de la demande d'électricité d'Hydro-Québec (2019 à 2023)."""

from pathlib import Path

import requests

BASE_URL = (
    "https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/"
    "xlsx/historique-demande/{annee}-demande-electricite-quebec.xlsx"
)
ANNEES = range(2019, 2024)  # 2019, 2020, 2021, 2022, 2023
DOSSIER = Path("data/raw/demande")


def telecharger(annee: int) -> Path:
    """Télécharge le fichier d'une année et renvoie son chemin."""
    url = BASE_URL.format(annee=annee)
    chemin = DOSSIER / f"{annee}-demande.xlsx"
    if chemin.exists():
        print(f"{annee} : déjà là, je passe")
        return chemin
    reponse = requests.get(url, timeout=60)
    reponse.raise_for_status()  # arrête le script si le serveur renvoie une erreur
    chemin.write_bytes(reponse.content)
    print(f"{annee} : {len(reponse.content) / 1024:.0f} Ko téléchargés")
    return chemin


def main() -> None:
    DOSSIER.mkdir(parents=True, exist_ok=True)
    for annee in ANNEES:
        telecharger(annee)


if __name__ == "__main__":
    main()