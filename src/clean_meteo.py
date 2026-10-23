"""Assemble et nettoie la météo horaire (UTC) des 3 stations."""

from pathlib import Path

import pandas as pd

DOSSIER = Path("data/raw/meteo")
TROU_MAX = 6  # heures : au-delà, on ne comble pas

# Colonnes gardées : nom dans le fichier -> nom court
COLONNES = {
    "Temp (°C)": "temp",
    "Rel Hum (%)": "humidite",
    "Wind Spd (km/h)": "vent",
}

# Poids de chaque ville = population de sa région métropolitaine
# (recensement 2021, Statistique Canada), pour une température « du Québec ».
POIDS = {"montreal": 4_291_732, "quebec": 839_311, "sherbrooke": 227_398}


def lire_station(ville: str) -> pd.DataFrame:
    """Tous les mois d'une station -> une ligne par heure UTC."""
    fichiers = sorted((DOSSIER / ville).glob("*.csv"))
    df = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in fichiers], ignore_index=True)
    df["debut_utc"] = pd.to_datetime(df["Date/Time (UTC)"], utc=True)
    df = df.set_index("debut_utc")[list(COLONNES)].rename(columns=COLONNES)
    return df[~df.index.duplicated()]  # sécurité si deux fichiers se chevauchent


def combler_trous_courts(serie: pd.Series) -> pd.Series:
    """Interpole uniquement les trous de TROU_MAX heures ou moins."""
    vide = serie.isna()
    bloc = (vide != vide.shift()).cumsum()
    taille_trou = vide.groupby(bloc).transform("sum")
    a_combler = vide & (taille_trou <= TROU_MAX)
    return serie.where(~a_combler, serie.interpolate(limit_area="inside"))


def nettoyer(debut: pd.Timestamp, fin: pd.Timestamp) -> pd.DataFrame:
    """Une ligne par heure entre debut et fin, une colonne par variable et par ville."""
    grille = pd.date_range(debut, fin, freq="h")
    resultat = pd.DataFrame(index=grille)
    for ville in POIDS:
        station = lire_station(ville).reindex(grille)
        for col in COLONNES.values():
            resultat[f"{col}_{ville}"] = combler_trous_courts(station[col])

    # Température moyenne pondérée par la population.
    total = sum(POIDS.values())
    resultat["temp_ponderee"] = sum(
        resultat[f"temp_{ville}"] * poids / total for ville, poids in POIDS.items()
    )
    resultat.index.name = "debut_utc"
    return resultat.reset_index()


if __name__ == "__main__":
    meteo = nettoyer(
        pd.Timestamp("2019-01-01 05:00", tz="UTC"),
        pd.Timestamp("2024-01-01 04:00", tz="UTC"),
    )
    print(meteo.head())
    print(len(meteo), "heures")
    print("valeurs encore vides par colonne :")
    print(meteo.isna().sum())