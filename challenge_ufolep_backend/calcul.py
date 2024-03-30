from pathlib import Path
import pandas as pd
from challenge_ufolep_backend.analyseur import AnalyseurUCPG, AnalyseurVCT
import json
from datetime import date
import numpy as np

POINTS_RESULTAT = [5, 4, 3, 2, 1]
POINTS_PARTICIPATION = 1
ANALYSEUR={
    "UC PONTCHARRA GRESIVAUDAN": AnalyseurUCPG,
    "VC TURRIPINOIS": AnalyseurVCT
}


if __name__ == "__main__":
    root = Path(__file__).parent
    coureurs = pd.read_csv(root / "coureurs.csv")
    courses = pd.read_csv(root / "courses/courses.csv", index_col="NOM")
    courses["PASSE"] = courses["DOSSIER"].str.len() > 0
    courses["NOM"] = courses.index.str.upper()
    resultats = { "courses": courses[["NOM","DATE","CLUB","PASSE"]].to_dict("records")}
    tous_points = []
    for course in courses.index.values:
        print(course)
        
        if not courses.loc[course, "PASSE"]:
            continue
        print(courses.loc[course, "DOSSIER"])
        analyseur = ANALYSEUR[courses.loc[course, "CLUB"]](coureurs, POINTS_RESULTAT, POINTS_PARTICIPATION)
        for chemin in (root / "courses" / courses.loc[course, "DOSSIER"]).rglob(f"*.{analyseur.EXTENSION}"):
            points = analyseur.calcul_points(str(chemin))
            tous_points.extend(points)
            print(points)
    tous_points = pd.concat(tous_points)
    somme_points = tous_points.groupby("LICENCE").agg({"NOM": "min", "CLUB":"min", "POINTS": "sum", "FEMME": "max", "JEUNE": "max",  "PARTICIPATION": "sum" })
    somme_points["TOTAL"] = somme_points.POINTS + somme_points.PARTICIPATION
    somme_points = somme_points[somme_points.TOTAL > 0]
    classement = somme_points.sort_values("TOTAL", ascending=False)


    classements = {
        "homme": classement[(~classement["FEMME"])&(~classement["JEUNE"])],
        "femme": classement[(classement["FEMME"])&(~classement["JEUNE"])],
        "jeune": classement[classement["JEUNE"]]
    }
    
    for k, df in classements.items():
        df.insert(0, "RANG", 0)
        df.loc[:, "RANG"] = df["TOTAL"].rank(method='min', ascending=False)
        classements[k] = df
        resultats[k] = df.to_dict('records')

    resultats["date"] = date.today().isoformat()
    
    json_str = json.dumps(resultats, ensure_ascii=False, indent=4).encode("utf-8")
    with open(root.parent / "data" / "resultats_indiv.json", "wb") as f:
        f.write(json_str)
