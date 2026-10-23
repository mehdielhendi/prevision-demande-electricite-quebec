"""Construit la base DuckDB : tables demande et meteo, et la vue jointe."""

from pathlib import Path

import duckdb
import pandas as pd

from src import clean_demande, clean_meteo

BASE = Path("data/projet.duckdb")


def main() -> None:
    demande = clean_demande.nettoyer(Path("data/raw/demande"))
    meteo = clean_meteo.nettoyer(demande["debut_utc"].min(), demande["debut_utc"].max())

    con = duckdb.connect(str(BASE))
    con.execute("SET TimeZone = 'UTC'")
    con.register("demande_df", demande)
    con.register("meteo_df", meteo)

    con.execute("CREATE OR REPLACE TABLE demande AS SELECT * FROM demande_df")
    con.execute("CREATE OR REPLACE TABLE meteo AS SELECT * FROM meteo_df")

    # La vue qui servira à l'analyse et au modèle : une ligne par heure.
    con.execute("""
        CREATE OR REPLACE VIEW donnees AS
        SELECT d.debut_utc,
               d.demande_mw,
               d.interpolee,
               m.temp_ponderee,
               m.temp_montreal, m.temp_quebec, m.temp_sherbrooke,
               m.humidite_montreal,
               m.vent_montreal
        FROM demande AS d
        LEFT JOIN meteo AS m USING (debut_utc)
    """)

    print(con.execute("SELECT COUNT(*) AS heures FROM donnees").df())

    # Premier aperçu : demande moyenne selon la température (tranches de 5 °C).
    print(con.execute("""
        SELECT FLOOR(temp_ponderee / 5) * 5 AS tranche_temp_c,
               COUNT(*)                     AS heures,
               ROUND(AVG(demande_mw))       AS demande_moyenne_mw
        FROM donnees
        WHERE demande_mw IS NOT NULL AND temp_ponderee IS NOT NULL
        GROUP BY tranche_temp_c
        ORDER BY tranche_temp_c
    """).df())

    con.close()
    print("Base écrite dans", BASE)


if __name__ == "__main__":
    main()