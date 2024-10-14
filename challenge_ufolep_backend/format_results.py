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
        try:
            df = df[self.COLS]
        except:
            breakpoint()
        df = self.match_riders(df)
        return df

    @abstractmethod
    def parse_file(self, path: Path) -> pd.DataFrame:
        return NotImplemented


class AlpespaceResultsFormatter(ResultsFormatter):
    COLS_REMAPPING = {'Clst':STR_RANK,
            'NOM':STR_NAME,
            'Nom':STR_NAME,
            'Club':STR_CLUB,
            'Catégorie':STR_CAT,
            'Rem.': "Rem"}

    DUPLICATE_COLS = [0, 3, 5]
    

    def parse_file(self, path: Path) -> pd.DataFrame:
        cat = path.with_suffix("").name.split("_")[-1]
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
        
        if "Rem" in df.columns:
            df.loc[df.Rem == STR_DNS, STR_RANK] = STR_DNS
            df.loc[df.Rem == STR_DNF, STR_RANK] = STR_DNF
            df.loc[:, STR_CAT] = cat
        
        if "Caté. UFOLEP" in df.columns:
            df.loc[:, STR_CAT] = df.loc[:, "Caté. UFOLEP"]
        df = df[self.COLS]

        return df[~df.NOM.isnull()]

class MouillatResultsFormatter(ResultsFormatter):
    COLS_REMAPPING = {'Clst':STR_RANK,
            'NOM':STR_NAME,
            'Club':STR_CLUB,
            'Catégorie':STR_CAT}
    
    def parse_file(self, path: Path) -> pd.DataFrame:
        pdf = pdfplumber.open(path)
        table = pdf.pages[0].extract_table(table_settings={"horizontal_strategy": "text", "vertical_strategy": "text", "text_x_tolerance": 10})
        table = table[2:]
        for i in range(len(table)):
            table[i][2:4] = [" ".join(table[i][2:4])]
            table[i][4:6] = ["".join(table[i][4:6])]
            table[i][5:7] = ["".join(table[i][5:7])]
        table
        df = pd.DataFrame(table[1:], columns=[STR_RANK, "DOSSARD", STR_NAME, "LICENCE", STR_CAT, STR_CLUB])
        df[STR_RANK] = df[STR_RANK].str.replace("Abandon", STR_DNF)
        df[STR_RANK] = df[STR_RANK].str.replace("Non partant", STR_DNS)
        return df[self.COLS]

class MorteResultsFormatter(ResultsFormatter):
    COLS_REMAPPING = {'Clst':STR_RANK,
            'NOM':STR_NAME,
            'Club':STR_CLUB,
            'Catégorie':STR_CAT}

    def parse_file(self, path: Path) -> pd.DataFrame:
        cat = path.with_suffix("").name.split("_")[-1]
        pdf = pdfplumber.open(path)
        tables = pdf.pages[0].find_tables(table_settings={})
        table = tables[0].extract()
        df = pd.DataFrame(table, columns=["Dossard", STR_NAME, STR_CAT, "Temps"])
        df.loc[:, STR_CLUB] = ""
        df.loc[:, STR_RANK] = df.index + 1

        return df[self.COLS]


class PeuilResultsFormatter(ResultsFormatter):
    def parse_file(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path)
        df[STR_NAME] = (
            df["Nom"] + " " + df["Prénom"]
        )
        df[STR_CLUB] = df["Club"]
        df[STR_CAT] = df["Catégorie UFOLEP"]
        df[STR_RANK] = df["Classement Scratch"]

        return df[self.COLS]


class ArzelierResultsFormatter(ResultsFormatter):
    def parse_file(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path)
        df[STR_NAME] = df["NOM"] + " " + df["PRENOM"]
        df[STR_CLUB] = df["CLUB"]
        df[STR_CAT] = df["Catégorie UFOLEP"]
        df[STR_RANK] = df["Classement scratch"]

        return df[self.COLS]


class CCGResultsFromatter(ResultsFormatter):
    COLS_REMAPPING = {'Rang':STR_RANK,
            'NOM':STR_NAME,
            'Club':STR_CLUB}

    def parse_file(self, path: Path) -> pd.DataFrame:
        cat = path.stem
        df = pd.read_csv(path, skiprows=0)
        if "Fédération / catégorie" in df.columns:
            cat = df["Fédération / catégorie"]
        df[STR_NAME] = df.Nom + " " + df.Prénom
        df = df[~df[STR_NAME].isna()]
        df[STR_NAME] = df[STR_NAME].map(lambda x: re.sub(' +', ' ', x))
        df =df.rename(columns=self.COLS_REMAPPING)
        df[STR_RANK] = df[STR_RANK].astype(str)
        df[STR_RANK] = df[STR_RANK].str.replace("AB", STR_DNF)
        df[STR_RANK] = df[STR_RANK].str.replace("AB", STR_DNF)
        df[STR_RANK] = df[STR_RANK].str.replace("NP", STR_DNS)
        df[STR_CAT] = cat
        return df[self.COLS]

class NDResultsFromatter(ResultsFormatter):
    COLS_REMAPPING = {'Arrivée':STR_RANK,
            'NOM':STR_NAME,
            'Club':STR_CLUB,
            'Catégorie Age':STR_CAT}
    
    def parse_file(self, path: Path) -> pd.DataFrame:
        try:
            df = pd.read_csv(path)
        except:
            breakpoint()
            raise

        df[STR_NAME] = df.NOM + " " + df.Prénom
        df = df[~df[STR_NAME].isna()]
        df[STR_NAME] = df[STR_NAME].map(lambda x: re.sub(' +', ' ', x))
        df =df.rename(columns=self.COLS_REMAPPING)
        df[STR_RANK] = df[STR_RANK].astype(str)
        df[STR_RANK] = df[STR_RANK].str.replace("Ab", STR_DNF)
        df[STR_RANK] = df[STR_RANK].str.replace("Np", STR_DNS)

        if not STR_CAT in df:
            df[STR_CAT] = path.stem
    
        return df[self.COLS]

class CrasResultsFormatter(ResultsFormatter):
    COLS_REMAPPING = {'Place':STR_RANK,

            'Club':STR_CLUB}
    
    def parse_file(self, path: Path) -> pd.DataFrame:
        cat = path.with_suffix("").name.split("-")[-1].lstrip(" ")
        df = pd.read_csv(path, header=0)
        df[STR_NAME] = df.Nom + " " + df.Prénom
        df = df[~df[STR_NAME].isna()]
        df[STR_NAME] = df[STR_NAME].map(lambda x: re.sub(' +', ' ', x))
        df =df.rename(columns=self.COLS_REMAPPING)
        
        df[STR_RANK] = df[STR_RANK].astype(str)
        df[STR_RANK] = df[STR_RANK].str.replace("AB", STR_DNF)
        df[STR_RANK] = df[STR_RANK].str.replace("NP", STR_DNS)
        df[STR_CAT] = cat
        return df[self.COLS]

class TvsResultsFormatter(ResultsFormatter):
    COLS_REMAPPING = {'Class.':STR_RANK,

            'Club':STR_CLUB,
            'cat': STR_CAT}

    def parse_file(self, path: Path) -> pd.DataFrame:
        # cat = path.with_suffix("").name.split("-")[-1].lstrip(" ")
        df = pd.read_csv(path, header=0)
        df[STR_NAME] = df["Nom"] + " " + df["Prénom"]
        df =df.rename(columns=self.COLS_REMAPPING)
        return df


class VersoudResultsFormatter(ResultsFormatter):
    COLS_REMAPPING = {"Class.": STR_RANK, "Club": STR_CLUB, "cat": STR_CAT}

    def parse_file(self, path: Path) -> pd.DataFrame:
        df = pd.read_csv(path, header=0)
        df[STR_NAME] = df["NomFamille"] + " " + df["Prénom"]
        df[STR_CLUB] = df["Club"]
        df[STR_CAT] = path.stem
        df[STR_RANK] = df["Classement"]
        return df


class ResultsFormatterFactory:
    def __init__(self, riders_db: pd.DataFrame) -> None:
        self.riders_db = riders_db

    def create_formatter(self, name:str) -> ResultsFormatter:
        p = name.lower()
        if "oyeu" in p or "murianette" in p or "triptyque" in p or "montaud" in p:
            return CCGResultsFromatter(self.riders_db)
        elif "cyclespace" in p or "allevard" in p:
            return AlpespaceResultsFormatter(self.riders_db)
        elif "mouillat" in p:
            return MouillatResultsFormatter(self.riders_db)
        elif "cras" in p or "andrevière" in p:
            return CrasResultsFormatter(self.riders_db)
        elif "porte" in p or "roybon" in p:
            return TvsResultsFormatter(self.riders_db)
        elif "osier" in p or "la chapelle" in p:
            return NDResultsFromatter(self.riders_db)
        elif "morte" in p:
            return MorteResultsFormatter(self.riders_db)
        elif "peuil" in p:
            return PeuilResultsFormatter(self.riders_db)
        elif "versoud" in p:
            return VersoudResultsFormatter(self.riders_db)
        elif "arzelier" in p:
            return ArzelierResultsFormatter(self.riders_db)
        else:
            raise ValueError(f"No formatter found for {p}")


def format_all_results(
    race: str,
    race_type: str,
    date: datetime.date,
    root_path: Path,
    formatter_factory: ResultsFormatterFactory,
) -> List[pd.DataFrame]:

    res = []
    formatter = formatter_factory.create_formatter(race)
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
    riders[STR_DATE] = pd.to_datetime(riders[STR_DATE])
    races = pd.read_csv(root / PATH_RACES, index_col=STR_RACE_NAME)
    races.loc[races[STR_RACE_FOLDER].isna(), STR_RACE_FOLDER] = ""
    races[STR_DATE] = pd.to_datetime(races[STR_DATE])
    race_folder = (root / PATH_RACES).parent

    formatter_factory = ResultsFormatterFactory(riders)

    for race in races.index.values:
        if len(races.loc[race, STR_RACE_FOLDER]) == 0:
            continue
        date = races.loc[race, STR_DATE]
        race_type = races.loc[race, STR_RACE_TYPE]
        format_all_results(race, race_type, date, race_folder / races.loc[race, STR_RACE_FOLDER], formatter_factory)
