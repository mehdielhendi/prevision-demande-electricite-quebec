# Prévision de la demande d'électricité au Québec à partir de la météo

Peut-on prévoir la demande d'électricité horaire du Québec à partir de la température ?
Ce projet relie cinq ans de données ouvertes d'Hydro-Québec à la météo d'Environnement Canada,
puis compare un modèle d'apprentissage automatique à une méthode simple.

**Démo en ligne : [demande-electricite-quebec.streamlit.app](https://demande-electricite-quebec.streamlit.app/)**

## Résultat

Testé sur toute l'année 2023 (8 760 heures jamais vues pendant l'entraînement) :

| Méthode | Erreur absolue moyenne | En % de la demande |
| --- | --- | --- |
| Méthode simple (même heure, semaine précédente) | 1 763 MW | 7,4 % |
| Régression linéaire | 1 061 MW | 5,2 % |
| **Gradient boosting** | **740 MW** | **3,3 %** |

Le modèle réduit l'erreur de 58 % par rapport à la méthode simple.

## Ce que montrent les données

- La demande est la plus basse vers 15 °C (environ 16 900 MW). Sous 10 °C, chaque degré
  de moins ajoute à peu près 530 MW : c'est le chauffage électrique.
- Les pointes annuelles suivent le froid. Le record de la période est de 42 473 MW,
  le 3 février 2023 à 17 h, par −27 °C.
- À froid comparable, la pointe de 2022 dépasse celle de 2019 de 2 300 MW : la demande
  de base augmente d'une année à l'autre.
- La fin de semaine, la pointe du matin baisse d'environ 1 500 MW ; celle du soir change peu.

## Données

| Source | Contenu | Période |
| --- | --- | --- |
| [Hydro-Québec, données ouvertes](https://www.hydroquebec.com/documents-donnees/donnees-ouvertes/) | Demande horaire moyenne (MW) | 2019 – 2023 |
| [Environnement et Changement climatique Canada](https://climate.weather.gc.ca/) | Température, humidité, vent horaires | 2019 – 2023 |

Stations météo : Montréal (YUL), Québec (YQB) et Sherbrooke. Leurs températures sont combinées
en une moyenne pondérée par la population de chaque région métropolitaine (recensement 2021),
pour représenter la température « vue » par l'ensemble des consommateurs.

## Choix de nettoyage

- **Heures en UTC.** Les fichiers d'Hydro-Québec sont en heure locale, avec une heure en double
  à l'automne et une heure manquante au printemps. Toutes les séries sont converties en UTC
  avant d'être jointes.
- **Erreur dans un fichier source.** La dernière ligne du fichier 2021 est datée de 2023 au lieu
  de 2022. Le script reconstruit l'horaire à partir de la position des lignes, vérifie chaque
  heure, et signale cette seule correction.
- **Trous.** Les trous de 6 heures ou moins sont interpolés et marqués dans une colonne
  `interpolee`. Les trous plus longs restent vides (41 heures en juin 2019).
- **Base de données.** Les tables nettoyées sont stockées dans DuckDB et jointes dans une vue
  `donnees`.

## Modèle

Variables : degrés-jours de chauffage et de climatisation (base 18 °C), température pondérée,
heure, jour de la semaine, jours fériés du Québec et tendance annuelle.
Modèle : `HistGradientBoostingRegressor` de scikit-learn, entraîné sur 2019 – 2022, testé sur 2023.

**Limite.** Le modèle utilise la température observée. En conditions réelles, il faudrait
une prévision météo, qui comporte sa propre erreur : les résultats ci-dessus sont donc optimistes.

## Lancer le projet

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate    macOS / Linux : source .venv/bin/activate
pip install -r requirements.txt

python src/ingest_demande.py     # télécharge la demande Hydro-Québec
python src/ingest_meteo.py       # télécharge la météo (3 stations, 61 mois)
python -m src.build_db           # nettoie et construit data/projet.duckdb
python -m src.models             # entraîne le modèle et écrit data/app/previsions_2023.csv
streamlit run app/dashboard.py   # lance le tableau de bord
```

## Structure

```
src/         téléchargement, nettoyage, base DuckDB, modèle
notebooks/   01_exploration (analyse) · 02_modele (comparaison des modèles)
app/         tableau de bord Streamlit
data/app/    prévisions 2023 utilisées par l'application
```

## Stack

Python · pandas · DuckDB · scikit-learn · Altair · Streamlit

## Licences des données

Données de demande : Hydro-Québec, licence CC BY-NC 4.0.
Données météo : Environnement et Changement climatique Canada, Licence du gouvernement ouvert – Canada.

---

Projet réalisé par **El Hendi Mohamed Mehdi**, maîtrise en informatique (IA et science des données),
Université de Sherbrooke.
