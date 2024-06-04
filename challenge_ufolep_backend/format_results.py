from abc import ABC, abstractmethod
import pdfplumber
from typing import List, Optional
import pandas as pd
import difflib
import unicodedata
from pathlib import Path
import re

STR_NAME = "NOM"
STR_ALL_NAMES = "LISTE_NOMS"
STR_RANK = "RANG"
STR_CLUB = "CLUB"
STR_CAT = "CAT"

STR_RACE_NAME = "NOM"
STR_RACE_FOLDER = "DOSSIER"

STR_WOMAN = "FEMME"
STR_YOUNG = "JEUNE"
STR_ID = "COUREUR"

STR_DNS = "DNS"
STR_DNF = "DNF"

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
        for idx in df.index.values:
            idx_coureur = df.loc[idx, STR_ID]
            if idx_coureur < 0:
                continue
            df.loc[idx, STR_NAME] = self.riders_db.loc[idx_coureur, STR_NAME]
            df.loc[idx, STR_CLUB] = self.riders_db.loc[idx_coureur, STR_CLUB]
            age = self.riders_db.loc[idx_coureur, "AGE"]
            if "Féminin" in age:
                df.loc[idx, STR_WOMAN] = True
            if "15/16" in age or "13/14" in age:
                df.loc[idx, STR_YOUNG] = True
        df[STR_WOMAN] = df[STR_WOMAN].astype(bool)
        df[STR_YOUNG] = df[STR_YOUNG].astype(bool)
        return df

    def format_results(self, path: Path, out: Optional[Path] = None) -> pd.DataFrame:
        df = self.parse_file(path=path)
        df = df[self.COLS]
        df = self.match_riders(df)
        if out is not None:
            df.to_csv(out)
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
            breakpoint()
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
        breakpoint()

        return df[self.COLS]
    
class CCGResultsFromatter(ResultsFormatter):
    COLS_REMAPPING = {'Rang':STR_RANK,
            'NOM':STR_NAME,
            'Club':STR_CLUB}
    
    def parse_file(self, path: Path) -> pd.DataFrame:
        with path.open("r", encoding="utf8") as f:
            cat = f.readline().split(",")[0].replace("Classement ", "").replace(" UFOLEP", "").capitalize()
        df = pd.read_csv(path, skiprows=1)
        df[STR_NAME] = df.Nom + " " + df.Prénom
        df = df[~df[STR_NAME].isna()]
        df[STR_NAME] = df[STR_NAME].map(lambda x: re.sub(' +', ' ', x))
        df =df.rename(columns=self.COLS_REMAPPING)
        df[STR_RANK] = df[STR_RANK].astype(str)
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
        df = pd.read_csv(path)

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
        #cat = path.with_suffix("").name.split("-")[-1].lstrip(" ")
        df = pd.read_csv(path, header=0)
        df[STR_NAME] = df["Nom"] + " " + df["Prénom"]
        df =df.rename(columns=self.COLS_REMAPPING)
        return df
    
class ResultsFormatterFactory:
    def __init__(self, riders_db: pd.DataFrame) -> None:
        self.riders_db = riders_db

    def create_formatter(self, name:str) -> ResultsFormatter:
        p = name.lower()
        if "oyeu" in p:
            return CCGResultsFromatter(self.riders_db)
        elif "cyclespace" in p or "allevard" in p:
            return AlpespaceResultsFormatter(self.riders_db)
        elif "mouillat" in p:
            return MouillatResultsFormatter(self.riders_db)
        elif "cras" in p:
            return CrasResultsFormatter(self.riders_db)
        elif "porte" in p:
            return TvsResultsFormatter(self.riders_db)
        elif "osier" in p:
            return NDResultsFromatter(self.riders_db)
        elif "morte" in p:
            return MorteResultsFormatter(self.riders_db)
        else:
            raise ValueError(f"No formatter found for {p}")

def get_all_results(race: str, root_path: Path, formatter_factory: ResultsFormatterFactory, override: bool) -> List[pd.DataFrame]:
    res = []
    formatter = formatter_factory.create_formatter(race)
    for path in root_path.glob("*"):
        out_path = get_output_file(race, path)
        if out_path.exists() and not override:
            points = pd.read_csv(out_path)
        else:
            points = formatter.format_results(path, out_path)
        print(points)
        res.append(points)
    return res


if __name__ == "__main__":
    root = Path(__file__).parent
    riders = pd.read_csv(root / PATH_RIDERS)
    riders[STR_ALL_NAMES] = riders[STR_NAME].map(normalize_string).str.upper().str.split(",")
    riders[STR_NAME] = riders[STR_ALL_NAMES].map(lambda x: x[0])
    races = pd.read_csv(root / PATH_RACES, index_col=STR_RACE_NAME)
    races.loc[races[STR_RACE_FOLDER].isna(), STR_RACE_FOLDER] = ""
    race_folder = (root / PATH_RACES).parent

    formatter_factory = ResultsFormatterFactory(riders)

    for race in races.index.values:
        if len(races.loc[race, STR_RACE_FOLDER]) == 0:
            continue
        get_all_results(race, race_folder / races.loc[race, STR_RACE_FOLDER], formatter_factory, override=True)