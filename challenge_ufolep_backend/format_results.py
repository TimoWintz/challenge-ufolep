from abc import ABC, abstractmethod
import pdfplumber
from typing import List, Optional
import pandas as pd
import difflib
import unicodedata
from pathlib import Path
import re
from datetime import datetime
import numpy as np

STR_NAME = "NOM"
STR_ALL_NAMES = "LISTE_NOMS"
STR_RANK = "RANG"
STR_CLUB = "CLUB"
STR_CAT = "CAT"

STR_RACE_NAME = "NOM"
STR_RACE_FOLDER = "DOSSIER"
STR_RACE_TYPE = "TYPE"
STR_RACE_TYPE_HILL = "Grimpée"

STR_WOMAN = "FEMME"
STR_YOUNG = "JEUNE"
STR_ID = "COUREUR"
STR_DATE = "DATE"
STR_DNS = "DNS"
STR_DNF = "DNF"
STR_NC = "NC"

PATH_RESULTS = "resultats"
PATH_RIDERS = "coureurs.csv"
PATH_RACES = "courses/courses.csv"

def get_output_file(race: str, path: Path) -> Path:
    return path.parent.parent / PATH_RESULTS / f"{race}_{path.with_suffix('.csv').name}"

def normalize_string(input_str :str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def find_rider(name: str, riders: pd.DataFrame) -> int:
    name = normalize_string(name).upper()
    all_names = riders[STR_ALL_NAMES]
    max_num_names = max(len(x) for x in all_names)
    
    for i in range(max_num_names):
        query = all_names.map(lambda x: x[i] if len(x) > i else "")
        x = difflib.get_close_matches(name.upper(), query, 1, 0.9)
        if len(x) > 0:
            break
    
    if len(x) == 0:
        print(f"{name} -> NOT FOUND")
        return -1
    if len(x)  > 1:
        print(x)
    rider_name = x[0]
    rider_idx = riders[query == rider_name].first_valid_index()
    print(f"{name} -> {rider_name} -> {riders.iloc[rider_idx][STR_NAME]}")
    
    return rider_idx

class ResultsFormatter(ABC):
    COLS = [STR_RANK, STR_NAME, STR_CLUB, STR_CAT]

    def __init__(self, riders_db: pd.DataFrame):
        self.riders_db = riders_db

    def match_riders(self, df: pd.DataFrame):
        df.insert(0, STR_ID, None)
        df[STR_ID] = df[STR_NAME].map(lambda nom: find_rider(nom, self.riders_db))

        df.insert(0, STR_WOMAN, False)
        df.insert(0, STR_YOUNG, False)
        df.insert(0, STR_DATE, pd.to_datetime("2023-01-01"))
        for idx in df.index.values:
            idx_coureur = df.loc[idx, STR_ID]
            if idx_coureur < 0:
                continue
            df.loc[idx, STR_NAME] = self.riders_db.loc[idx_coureur, STR_NAME]
            df.loc[idx, STR_CLUB] = self.riders_db.loc[idx_coureur, STR_CLUB]
            df.loc[idx, STR_DATE] = self.riders_db.loc[idx_coureur, STR_DATE]
            age = self.riders_db.loc[idx_coureur, "AGE"]
            if "Féminin" in age:
                df.loc[idx, STR_WOMAN] = True
            if "15/16" in age or "13/14" in age:
                df.loc[idx, STR_YOUNG] = True
        df[STR_WOMAN] = df[STR_WOMAN].astype(bool)
        df[STR_YOUNG] = df[STR_YOUNG].astype(bool)
        return df

    def format_results(self, path: Path) -> pd.DataFrame:
        df = self.parse_file(path=path)
        df = df[self.COLS]
        df = self.match_riders(df)
        return df

    @abstractmethod
    def parse_file(self, path: Path) -> pd.DataFrame:
        return NotImplemented


class GenericCSVFormatter(ResultsFormatter):
    COLS_NAME = ["NOM", "Nom", "Nom complet"]
    COLS_SURNAME = ["Prénom", "Prenom"]
    COLS_PLACE = ["Place", "Rang", "Arrivée", "Clst", "Class."]
    COLS_CAT = ["Caté. UFOLEP", "Catégorie", "Catégorie Age"]
    COLS_CLUB = ["Club", "CLUB", "Club Ufolep 38"]

    VALUES_DNF = ["Abandon", "Ab", "AB" "DNF"]
    VALUES_DNS = ["Non partant", "Np", "NP", "DNS"]
    VALUES_REM = ["Rem"]

    def rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        col_surname = None
        for col in self.COLS_SURNAME:
            if col in df.columns:
                col_surname = col

        for col in self.COLS_NAME:
            if col in df.columns:
                df.rename(columns={col: STR_NAME}, inplace=True)
        
        if col_surname is not None and not df[col_surname].isna().any():
            df[STR_NAME] = (df[STR_NAME].str.strip() + " " + df[col_surname].astype(str)).str.strip()

        for col in self.COLS_PLACE:
            if col in df.columns:
                df.rename(columns={col: STR_RANK}, inplace=True)
                break
        for col in self.COLS_CAT:
            if col in df.columns:
                df.rename(columns={col: STR_CAT}, inplace=True)
                break
        for col in self.COLS_CLUB:
            if col in df.columns:
                df.rename(columns={col: STR_CLUB}, inplace=True)
                break

        return df

    def format_values(self, df: pd.DataFrame) -> pd.DataFrame:
        for val in self.VALUES_DNF:
            df[STR_RANK] = df[STR_RANK].replace(val, STR_DNF)
        for val in self.VALUES_DNS:
            df[STR_RANK] = df[STR_RANK].replace(val, STR_DNS)
        for col_rem in self.VALUES_REM:
            if col_rem in df.columns:
                for val in self.VALUES_DNS:
                    df.loc[df[col_rem] == val, STR_RANK] = STR_DNS
                for val in self.VALUES_DNF:
                    df.loc[df[col_rem] == val, STR_RANK] = STR_DNF

        return df

    def parse_file(self, path: Path) -> pd.DataFrame:

        df = pd.read_csv(path)
        df = self.rename_columns(df)
        df = self.format_values(df)
        if not STR_CAT in df.columns:
            df[STR_CAT] = path.stem

        return df[self.COLS]


def format_all_results(
    race: str,
    race_type: str,
    date: datetime.date,
    root_path: Path,
    riders: pd.DataFrame,
) -> List[pd.DataFrame]:

    res = []
    formatter = GenericCSVFormatter(riders)
    for path in root_path.glob("*"):
        out_path = get_output_file(race, path)
        points = formatter.format_results(path)
        if race == 'Cyclocross du Mouillat':
            res.append(points)
        else:
            too_late = np.logical_and(points[STR_ID] > 0, points[STR_DATE] > date + pd.Timedelta("7 days"))
            if race_type == STR_RACE_TYPE_HILL and too_late.sum() > 0:
                points.loc[too_late, STR_ID] = -2
                points.loc[too_late, STR_CLUB] = ""
            res.append(points)
        points.to_csv(out_path)
    return res


if __name__ == "__main__":
    root = Path(__file__).parent
    riders = pd.read_csv(root / PATH_RIDERS)
    riders[STR_ALL_NAMES] = riders[STR_NAME].map(normalize_string).str.upper().str.split(",")
    riders[STR_NAME] = riders[STR_ALL_NAMES].map(lambda x: x[0])
    riders[STR_DATE] = pd.to_datetime(riders[STR_DATE], dayfirst=True)
    races = pd.read_csv(root / PATH_RACES, index_col=STR_RACE_NAME)
    races.loc[races[STR_RACE_FOLDER].isna(), STR_RACE_FOLDER] = ""
    races[STR_DATE] = pd.to_datetime(races[STR_DATE], dayfirst=False)
    race_folder = (root / PATH_RACES).parent

    for race in races.index.values:
        if len(races.loc[race, STR_RACE_FOLDER]) == 0:
            continue
        date = races.loc[race, STR_DATE]
        race_type = races.loc[race, STR_RACE_TYPE]
        format_all_results(race, race_type, date, race_folder / races.loc[race, STR_RACE_FOLDER], riders)
