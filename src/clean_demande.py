"""Charge et nettoie l'historique de demande d'Hydro-Québec."""

from pathlib import Path

import pandas as pd

TROU_MAX = 6  # heures : au-delà, on ne comble pas


def convertir_en_utc(brut: pd.DataFrame) -> pd.DataFrame:
    """Un fichier annuel -> colonnes debut_utc et demande_mw.

    Les dates du fichier sont des FINS d'heure en heure locale du Québec.
    On place la première en UTC, puis on avance d'une heure par ligne.
    """
    df = brut.rename(columns={"Date": "fin_locale", "Moyenne (MW)": "demande_mw"})

    premiere = df["fin_locale"].iloc[0].tz_localize("America/Toronto").tz_convert("UTC")
    fin_utc = pd.date_range(premiere, periods=len(df), freq="h")

    # Vérification : en revenant à l'heure du Québec, on doit retrouver le fichier.
    reconstruit = fin_utc.tz_convert("America/Toronto").tz_localize(None)
    ecarts = reconstruit != df["fin_locale"].to_numpy()
    if ecarts.any():
        position = int(ecarts.argmax())  # index de la première ligne fautive
        derniere_seule = ecarts.sum() == 1 and position == len(df) - 1
        if derniere_seule:
            # Erreur connue : le fichier 2021 date sa dernière heure de 2023 au lieu de 2022.
            # L'ordre des lignes fait foi : on garde la date reconstruite.
            print(f"  correction : {df['fin_locale'].iloc[-1]} -> {reconstruit[-1]}")
        else:
            debut, fin = max(0, position - 2), position + 3
            print("ligne :", position)
            print("dans le fichier :", [str(d) for d in df["fin_locale"].iloc[debut:fin]])
            print("attendu         :", [str(d) for d in reconstruit[debut:fin]])
            raise ValueError(f"{ecarts.sum()} heures ne suivent pas la suite attendue")

    df["debut_utc"] = fin_utc - pd.Timedelta(hours=1)  # fin d'heure -> début d'heure
    return df[["debut_utc", "demande_mw"]]


def nettoyer(dossier: Path) -> pd.DataFrame:
    """Une ligne par heure UTC : debut_utc, demande_mw, interpolee."""
    fichiers = sorted(dossier.glob("*-demande.xlsx"))
    morceaux = []
    for f in fichiers:
        print("lecture de", f.name)
        morceaux.append(convertir_en_utc(pd.read_excel(f)))
    serie = pd.concat(morceaux).set_index("debut_utc")["demande_mw"]

    # Grille complète d'heures : un trou devient une valeur vide visible.
    grille = pd.date_range(serie.index.min(), serie.index.max(), freq="h")
    serie = serie.reindex(grille)

    # Ne combler que les trous de TROU_MAX heures ou moins.
    vide = serie.isna()
    bloc = (vide != vide.shift()).cumsum()
    taille_trou = vide.groupby(bloc).transform("sum")
    a_combler = vide & (taille_trou <= TROU_MAX)
    serie = serie.where(~a_combler, serie.interpolate(limit_area="inside"))

    return pd.DataFrame(
        {"debut_utc": grille, "demande_mw": serie.to_numpy(), "interpolee": a_combler.to_numpy()}
    )


if __name__ == "__main__":
    propre = nettoyer(Path("data/raw/demande"))
    print(propre.head())
    print(len(propre), "heures")
    print("interpolées :", propre["interpolee"].sum())
    print("encore vides :", propre["demande_mw"].isna().sum())