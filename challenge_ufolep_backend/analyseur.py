from abc import ABC, abstractmethod
import pdfplumber
from typing import List, Optional
import pandas as pd
import difflib
import unicodedata
def enlever_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def nom_vers_licence(nom: str, coureurs: pd.DataFrame) -> int:
    nom = enlever_accents(nom).upper()
    coureurs["NOM"] = coureurs["NOM"].map(enlever_accents).str.upper()

    x = difflib.get_close_matches(nom.upper(), coureurs["NOM"], 1, 0.9)
    if len(x) == 0:
        print(f"{nom} -> PAS UFO")
        return -1
    if len(x)  > 1:
        print(x)
    nom_coureur = x[0]
    idx_coureur = coureurs[coureurs.NOM == nom_coureur].first_valid_index()
    print(f"{nom} -> {nom_coureur} -> {coureurs.iloc[idx_coureur].NOM}")
    return idx_coureur

class AnalyseurResultats(ABC):
    EXTENSION: str
    COLS = ["CLASSEMENT", "DOSSARD", "NOM", "CLUB", "CAT"]

    def __init__(self, coureurs: pd.DataFrame, points_resultats: List[int], points_participation: int):
        self.coureurs = coureurs
        self.points_resultats = points_resultats
        self.points_participation = points_participation

    def lire_coureur(self, df: pd.DataFrame):
        df.insert(0, "IDX_COUREUR", None)
        df["IDX_COUREUR"] = df.NOM.map(lambda nom: nom_vers_licence(nom, self.coureurs))
        df.insert(0, "LICENCE", "")
        df.insert(0, "FEMME", False)
        df.insert(0, "JEUNE", False)
        for idx in df.index.values:
            idx_coureur = df.loc[idx, "IDX_COUREUR"]
            if idx_coureur < 0:
                continue
            df.loc[idx, "LICENCE"] = self.coureurs.loc[idx_coureur, "LICENCE"]
            df.loc[idx, "NOM"] = self.coureurs.loc[idx_coureur, "NOM"]
            df.loc[idx, "CLUB"] = self.coureurs.loc[idx_coureur, "CLUB"]
            age = self.coureurs.loc[idx_coureur, "AGE"]
            if "Féminin" in age:
                df.loc[idx, "FEMME"] = True
            if "15/16" in age or "13/14" in age:
                df.loc[idx, "JEUNE"] = True
        df.LICENCE = df.LICENCE.astype(str)
        df.FEMME = df.FEMME.astype(bool)
        df.JEUNE = df.JEUNE.astype(bool)
        return df

    def calcul_points(self, chemin: str) -> List[pd.DataFrame]:
        df = self.implem_analyser(chemin)
        df = self.lire_coureur(df)

        categories = df["CAT"].unique().tolist()
        ret = []
        for cat in categories:
            df_cat = df[df.CAT == cat]
            classement_ufolep = df_cat[df_cat.LICENCE.str.len() > 0]
            if len(classement_ufolep) == 0:
                continue
            classement_ufolep.insert(6, 'POINTS', 0)
            classement_ufolep.insert(7, 'PARTICIPATION', 0)

            rang_ufolep = -1
            prev_classement = None
            for i, idx in enumerate(classement_ufolep.index.values):
                classement = classement_ufolep.loc[idx, "CLASSEMENT"]
                if classement == "DNS":
                    continue
                classement_ufolep.loc[idx, "PARTICIPATION"] = self.points_participation
                if classement == "DNF":
                    continue
                if prev_classement != classement:
                    rang_ufolep += 1
                if rang_ufolep < len(self.points_resultats):
                    classement_ufolep.loc[idx, "POINTS"] = self.points_resultats[rang_ufolep]
                
                prev_classement = classement
            ret.append(classement_ufolep)
        return ret
    
    @abstractmethod
    def implem_analyser(self, chemin: str) -> pd.DataFrame:
        raise NotImplementedError()
    

    
    
class AnalyseurUCPG(AnalyseurResultats):
    COLS_REMAPPING = {'Clst':'CLASSEMENT',
            'DOS':'DOSSARD',
            'NOM':'NOM',
            'Club':'CLUB',
            'Catégorie':'CAT',
            'Rem':'REM'}
    EXTENSION = "pdf"
    DUPLICATE_COLS = [0, 3, 5]
    

    def implem_analyser(self, path: str) -> pd.DataFrame:
        pdf = pdfplumber.open(path)
        tables = pdf.pages[0].find_tables(table_settings={})
        table = tables[0].extract()
        df = pd.DataFrame(table[1:], columns=table[0])
        if len(table[0]) == 15: # cas de colonnes dupliquées par pdfplumber
            for j in self.DUPLICATE_COLS:
                for idx in df.index.values:
                    if not df.iloc[idx, j]:
                        df.iloc[idx, j] = df.iloc[idx, j+1]
          

        df =df.rename(columns=self.COLS_REMAPPING)
        df.loc[df.REM == "DNS", "CLASSEMENT"] = "DNS"
        df.loc[df.REM == "DNF", "CLASSEMENT"] = "DNF"
        df = df[self.COLS]

        return df
    
class AnalyseurVCT(AnalyseurResultats):
    EXTENSION = "pdf"
    COLS_REMAPPING = {'Clst':'CLASSEMENT',
            'DOS':'DOSSARD',
            'NOM':'NOM',
            'Club':'CLUB',
            'Catégorie':'CAT',
            'Rem':'REM'}
    
    def implem_analyser(self, path: str) -> pd.DataFrame:
        pdf = pdfplumber.open(path)
        table = pdf.pages[0].extract_table(table_settings={"horizontal_strategy": "text", "vertical_strategy": "text", "text_x_tolerance": 10})
        table = table[2:]
        for i in range(len(table)):
            table[i][2:4] = [" ".join(table[i][2:4])]
            table[i][4:6] = ["".join(table[i][4:6])]
            table[i][5:7] = ["".join(table[i][5:7])]
        table
        df = pd.DataFrame(table[1:], columns=["CLASSEMENT", "DOSSARD", "NOM", "LICENCE", "CAT", "CLUB"])
        df.CLASSEMENT.str.replace("Abandon", "DNF")
        df.CLASSEMENT.str.replace("Non partant", "DNS")
        return df[["CLASSEMENT", "DOSSARD", "NOM", "CAT", "CLUB"]]