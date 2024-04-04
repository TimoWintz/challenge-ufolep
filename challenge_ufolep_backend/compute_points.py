from pathlib import Path
import pandas as pd
from challenge_ufolep_backend.format_results import STR_RACE_FOLDER, STR_RACE_NAME, STR_CAT, STR_DNF, STR_DNS, PATH_RACES, STR_ID, get_all_results, ResultsFormatterFactory, STR_NAME, STR_RANK, STR_WOMAN, STR_YOUNG, STR_CLUB
import json
from datetime import date
from typing import List

POINTS = [5, 4, 3, 2, 1]
POINTS_PER_START = 1

STR_POINTS = "POINTS"
STR_START = "PARTICIPATION"

def get_points(df: pd.DataFrame, rank_to_point: List[int]) -> List[pd.DataFrame]:
        if df[STR_YOUNG].any():
            df.loc[df[STR_WOMAN], STR_CAT] +=  "F"

        categories = df[STR_CAT].unique().tolist()
        ret = []
        for cat in categories:
            df_cat = df[df[STR_CAT] == cat]
            valid_ranking = df_cat[df_cat[STR_ID] >= 0]
            if len(valid_ranking) == 0:
                continue
            valid_ranking.insert(6, STR_POINTS, 0)
            valid_ranking.insert(7, STR_START, 0)

            valid_rank = -1
            prev_ranking = None
            for i, idx in enumerate(valid_ranking.index.values):
                current_ranking = valid_ranking.loc[idx, STR_RANK]
                if current_ranking == STR_DNS:
                    continue
                valid_ranking.loc[idx, STR_START] = 1
                if current_ranking == STR_DNF:
                    continue
                if prev_ranking != current_ranking:
                    valid_rank += 1
                if valid_rank < len(rank_to_point):
                    valid_ranking.loc[idx, "POINTS"] = rank_to_point[valid_rank]
                
                prev_ranking = current_ranking
            ret.append(valid_ranking)
        return ret


if __name__ == "__main__":
    root = Path(__file__).parent
    riders = pd.read_csv(root / "coureurs.csv")
    races = pd.read_csv(root / "courses/courses.csv", index_col=STR_RACE_NAME)
    races["PASSE"] = races["DOSSIER"].str.len() > 0
    races[STR_RACE_NAME] = races.index.str.upper()
    results = { "courses": races[[STR_RACE_NAME,"DATE","CLUB","PASSE"]].to_dict("records")}
    tous_points = []
    race_folder = (root / PATH_RACES).parent
    formatter_factory = ResultsFormatterFactory(riders)

    all_tables_points = []
    for race in races.index.values:
        if not races.loc[race, "PASSE"]:
            continue
        tables = get_all_results(race, race_folder / races.loc[race, STR_RACE_FOLDER], formatter_factory, override=False)
        tables_points = sum([get_points(x, POINTS) for x in tables], [])
        all_tables_points.extend(tables_points)

    df_all_points = pd.concat(all_tables_points)
    print(df_all_points)

    df_sum_points = df_all_points.groupby(STR_ID).agg({STR_NAME: "min", STR_CLUB:"min", STR_POINTS: "sum", STR_WOMAN: "max", STR_YOUNG: "max",  STR_START: "sum" })
    df_sum_points["TOTAL"] = df_sum_points[STR_POINTS] + POINTS_PER_START * df_sum_points[STR_START]
    df_sum_points = df_sum_points[df_sum_points.TOTAL > 0]
    ranking = df_sum_points.sort_values(["TOTAL", STR_POINTS, STR_NAME], ascending=False)


    classements = {
        "homme": ranking[(~ranking[STR_WOMAN])&(~ranking[STR_YOUNG])],
        "femme": ranking[(ranking[STR_WOMAN])&(~ranking[STR_YOUNG])],
        "jeune": ranking[ranking[STR_YOUNG]]
    }
    
    for k, df in classements.items():
        df.insert(0, STR_RANK, 0)
        df.loc[:, STR_RANK] = df["TOTAL"].rank(method='min', ascending=False)
        classements[k] = df
        results[k] = df.to_dict('records')

    results["date"] = date.today().isoformat()
    
    json_str = json.dumps(results, ensure_ascii=False, indent=4).encode("utf-8")
    with open(root.parent / "data" / "resultats_indiv.json", "wb") as f:
        f.write(json_str)