"""Application : prévision de la demande d'électricité au Québec (2023)."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

FICHIER = Path(__file__).resolve().parents[1] / "data" / "app" / "previsions_2023.csv"

st.set_page_config(page_title="Demande d'électricité au Québec", layout="wide")


@st.cache_data
def charger() -> pd.DataFrame:
    df = pd.read_csv(FICHIER, parse_dates=["debut_utc"])
    df["heure_locale"] = df["debut_utc"].dt.tz_convert("America/Toronto").dt.tz_localize(None)
    return df


df = charger()

st.title("Prévoir la demande d'électricité du Québec à partir de la météo")
st.write(
    "Un modèle de gradient boosting entraîné sur 2019 à 2022, testé sur toute l'année 2023, "
    "qu'il n'a jamais vue. Il est comparé à une méthode simple : "
    "« même heure, même jour, la semaine passée »."
)

# Indicateurs sur toute l'année 2023
err_modele = (df["demande_mw"] - df["prevision_modele"]).abs()
err_base = (df["demande_mw"] - df["prevision_base"]).abs()
col1, col2, col3 = st.columns(3)
col1.metric("Erreur moyenne du modèle",
            f"{err_modele.mean():.0f} MW ({(err_modele / df['demande_mw']).mean() * 100:.1f} %)")
col2.metric("Erreur de la méthode simple",
            f"{err_base.mean():.0f} MW ({(err_base / df['demande_mw']).mean() * 100:.1f} %)")
col3.metric("Réduction de l'erreur", f"{(1 - err_modele.mean() / err_base.mean()) * 100:.0f} %")

# Choix de la semaine
st.subheader("Choisis une semaine de 2023")
debut = st.date_input(
    "Premier jour",
    value=pd.Timestamp("2023-02-01"),
    min_value=pd.Timestamp("2023-01-01"),
    max_value=pd.Timestamp("2023-12-24"),
)
debut = pd.Timestamp(debut)
semaine = df[(df["heure_locale"] >= debut) & (df["heure_locale"] < debut + pd.Timedelta(days=7))]

courbes = semaine.melt(
    id_vars="heure_locale",
    value_vars=["demande_mw", "prevision_modele", "prevision_base"],
    var_name="serie", value_name="mw",
)
courbes["serie"] = courbes["serie"].map({
    "demande_mw": "Réalité", "prevision_modele": "Modèle", "prevision_base": "Méthode simple",
})
graphe_demande = (
    alt.Chart(courbes)
    .mark_line()
    .encode(
        x=alt.X("heure_locale:T", title=None),
        y=alt.Y("mw:Q", title="Demande (MW)", scale=alt.Scale(zero=False)),
        color=alt.Color("serie:N", title=None,
                        scale=alt.Scale(domain=["Réalité", "Modèle", "Méthode simple"],
                                        range=["#e4572e", "#4c9be8", "#9aa5b1"])),
        strokeDash=alt.StrokeDash("serie:N", legend=None,
                                  scale=alt.Scale(domain=["Réalité", "Modèle", "Méthode simple"],
                                                  range=[[1, 0], [1, 0], [4, 4]])),
        tooltip=[alt.Tooltip("heure_locale:T", title="Heure", format="%d %b %H:%M"),
                 "serie:N", alt.Tooltip("mw:Q", title="MW", format=",.0f")],
    )
    .properties(height=380)
)
st.altair_chart(graphe_demande, width="stretch")

graphe_temp = (
    alt.Chart(semaine)
    .mark_line(color="#f2a541")
    .encode(
        x=alt.X("heure_locale:T", title=None),
        y=alt.Y("temp_ponderee:Q", title="Température pondérée (°C)", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("heure_locale:T", title="Heure", format="%d %b %H:%M"),
                 alt.Tooltip("temp_ponderee:Q", title="°C", format=".1f")],
    )
    .properties(height=200)
)
st.altair_chart(graphe_temp, width="stretch")

e = (semaine["demande_mw"] - semaine["prevision_modele"]).abs()
st.write(f"Cette semaine, le modèle se trompe en moyenne de **{e.mean():.0f} MW**.")

st.caption(
    "Données : Hydro-Québec (demande d'électricité, licence CC BY-NC 4.0) et "
    "Environnement et Changement climatique Canada (météo). "
    "Le modèle utilise la température observée, pas une prévision météo : "
    "les résultats sont donc un peu optimistes. "
    "Projet d'El Hendi Mohamed Mehdi."
)
