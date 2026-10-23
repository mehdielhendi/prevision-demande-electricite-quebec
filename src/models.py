"""Entraîne le modèle et enregistre les prévisions 2023 pour l'application."""

from pathlib import Path

import duckdb
import holidays
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

BASE = Path("data/projet.duckdb")
SORTIE = Path("data/app/previsions_2023.csv")
VARIABLES = ["chauffage", "climatisation", "temp_ponderee", "ferie",
             "tendance", "heure", "jour_semaine"]


def charger() -> pd.DataFrame:
    con = duckdb.connect(str(BASE), read_only=True)
    con.execute("SET TimeZone = 'UTC'")
    df = con.execute("SELECT * FROM donnees ORDER BY debut_utc").df()
    con.close()
    return df


def ajouter_variables(df: pd.DataFrame) -> pd.DataFrame:
    locale = df["debut_utc"].dt.tz_convert("America/Toronto")
    feries = holidays.Canada(prov="QC", years=range(2019, 2025))
    df["annee"] = locale.dt.year
    df["chauffage"] = (18 - df["temp_ponderee"]).clip(lower=0)
    df["climatisation"] = (df["temp_ponderee"] - 18).clip(lower=0)
    df["heure"] = locale.dt.hour
    df["jour_semaine"] = locale.dt.dayofweek
    df["ferie"] = locale.dt.date.map(lambda d: d in feries).astype(int)
    df["tendance"] = df["annee"] - 2019
    df["prevision_base"] = df["demande_mw"].shift(168)
    return df


def main() -> None:
    df = ajouter_variables(charger())
    ok = df["demande_mw"].notna() & df[VARIABLES].notna().all(axis=1)
    entrainement = ok & (df["annee"] <= 2022)
    test = ok & (df["annee"] == 2023)

    modele = HistGradientBoostingRegressor(max_iter=500, learning_rate=0.05, random_state=0)
    modele.fit(df.loc[entrainement, VARIABLES], df.loc[entrainement, "demande_mw"])

    resultat = df.loc[test, ["debut_utc", "demande_mw", "prevision_base", "temp_ponderee"]].copy()
    resultat["prevision_modele"] = modele.predict(df.loc[test, VARIABLES]).round(0)

    for nom in ["prevision_base", "prevision_modele"]:
        erreur = (resultat["demande_mw"] - resultat[nom]).abs()
        print(f"{nom} : {erreur.mean():.0f} MW, {(erreur / resultat['demande_mw']).mean() * 100:.1f} %")

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    resultat.to_csv(SORTIE, index=False)
    print(f"{len(resultat)} heures enregistrées dans {SORTIE}")


if __name__ == "__main__":
    main()