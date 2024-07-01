from pathlib import Path
import pandas as pd
from challenge_ufolep_backend.format_results import (
    STR_RACE_FOLDER,
    STR_RACE_NAME,
    STR_CAT,
    STR_DNF,
    STR_DNS,
    PATH_RACES,
    STR_ID,
    get_all_results,
    ResultsFormatterFactory,
    STR_NAME,
    STR_RANK,
    STR_WOMAN,
    STR_YOUNG,
    STR_CLUB,
)
import json
from datetime import date
from typing import List

POINTS = [5, 4, 3, 2, 1]
POINTS_PER_START = 1

STR_POINTS = "POINTS"
STR_START = "PARTICIPATION"
STR_RACE = "COURSE"
STR_RACE_RANK = "PLACE"


def get_points(df: pd.DataFrame, rank_to_point: List[int]) -> List[pd.DataFrame]:
    if df[STR_YOUNG].any():
        df.loc[df[STR_WOMAN], STR_CAT] += "F"

    categories = df[STR_CAT].unique().tolist()
    ret = []
    for cat in categories:
        df_cat = df[df[STR_CAT] == cat]
        valid_ranking = df_cat[df_cat[STR_ID] >= 0]
        if len(valid_ranking) == 0:
            continue
        valid_ranking.insert(6, STR_POINTS, 0)
        valid_ranking.insert(7, STR_START, 0)
        valid_ranking.insert(8, STR_RACE_RANK, 0)

        valid_rank = -1
        prev_ranking = None
        for i, idx in enumerate(valid_ranking.index.values):
            current_ranking = valid_ranking.loc[idx, STR_RANK]
            if current_ranking == STR_DNS:
                valid_ranking.loc[idx, STR_RACE_RANK] = STR_DNS
                continue
            valid_ranking.loc[idx, STR_START] = 1
            if current_ranking == STR_DNF:
                valid_ranking.loc[idx, STR_RACE_RANK] = STR_DNF
                continue
            if prev_ranking != current_ranking:
                valid_rank += 1
            if valid_rank < len(rank_to_point):
                valid_ranking.loc[idx, STR_POINTS] = rank_to_point[valid_rank]
            valid_ranking.loc[idx, STR_RACE_RANK] = valid_rank + 1

            prev_ranking = current_ranking
        ret.append(valid_ranking)
    return ret


if __name__ == "__main__":
    root = Path(__file__).parent
    riders = pd.read_csv(root / "coureurs.csv")
    races = pd.read_csv(root / "courses/courses.csv", index_col=STR_RACE_NAME)
    races["PASSE"] = races["DOSSIER"].str.len() > 0
    races[STR_RACE_NAME] = races.index.str.upper()
    results = {
        "courses": races[[STR_RACE_NAME, "DATE", "CLUB", "PASSE"]].to_dict("records")
    }
    tous_points = []
    race_folder = (root / PATH_RACES).parent
    formatter_factory = ResultsFormatterFactory(riders)

    all_tables_points = []
    for race in races.index.values:
        if not races.loc[race, "PASSE"]:
            continue
        tables = get_all_results(
            race,
            race_folder / races.loc[race, STR_RACE_FOLDER],
            formatter_factory,
            override=False,
        )
        tables_points = sum([get_points(x, POINTS) for x in tables], [])
        for t in tables_points:
            t.insert(0, STR_RACE, race)

        all_tables_points.extend(tables_points)

    df_all_points = pd.concat(all_tables_points)
    df_all_points[["NOM","JEUNE","FEMME","COURSE","RANG","POINTS","PARTICIPATION","CLUB"]].to_csv("points.csv")
    print(df_all_points)

    df_all_points[STR_POINTS + "_L"] = df_all_points[STR_POINTS]
    df_all_points[STR_START + "_L"] = df_all_points[STR_START]
    df_sum_points = df_all_points.groupby(STR_ID).agg(
        {
            STR_NAME: "min",
            STR_CLUB: "min",
            STR_POINTS: "sum",
            STR_WOMAN: "max",
            STR_YOUNG: "max",
            STR_START: "sum",
            STR_RACE_RANK: list,
            STR_RACE: list,
            STR_POINTS + "_L": list,
            STR_START + "_L": list,
        }
    )

    df_sum_points["TOTAL"] = (
        df_sum_points[STR_POINTS] + POINTS_PER_START * df_sum_points[STR_START]
    )
    df_sum_points = df_sum_points[df_sum_points.TOTAL > 0]
    ranking = df_sum_points.sort_values(
        ["TOTAL", STR_POINTS, STR_NAME], ascending=False
    )

    points_per_club = df_sum_points.groupby("CLUB").sum()
    points_per_club["ORGA"] = 0
    points_per_club["INDIV"] = points_per_club["TOTAL"]

    points_races = races[races.PASSE]
    points_races = points_races[races.CLUB != "COMITE"]

    for race in points_races.index.values:
        club_rankings = points_races.loc[race, "CLUB"]
        type = points_races.loc[race, "TYPE"]
        if type == "Championnat":
            points = 25
        elif type == "Combiné":
            points = 30
        else:
            points = 20
        print(f"{race=},{points=},{club_rankings=}")
        if not club_rankings in points_per_club.index: # When club has no riders
            points_per_club.loc[club_rankings] = {"INDIV": 0, "ORGA": points}
        else:
            points_per_club.loc[club_rankings, "ORGA"] += points

    points_per_club["TOTAL"] = points_per_club["INDIV"] + points_per_club["ORGA"]
    points_per_club = points_per_club.sort_values("TOTAL", ascending=False)
    points_per_club = points_per_club[["TOTAL", "INDIV", "ORGA"]]

    rankings = {
        "homme": ranking[(~ranking[STR_WOMAN]) & (~ranking[STR_YOUNG])],
        "femme": ranking[(ranking[STR_WOMAN]) & (~ranking[STR_YOUNG])],
        "jeune": ranking[ranking[STR_YOUNG]],
    }

    for k, df in rankings.items():
        df.insert(0, STR_RANK, 0)
        df.loc[:, STR_RANK] = df["TOTAL"].rank(method="min", ascending=False)
        rankings[k] = df
        results[k] = df.to_dict("records")

    results["date"] = date.today().isoformat()

    json_str = json.dumps(results, ensure_ascii=False, indent=4).encode("utf-8")
    with open(root.parent / "data" / "resultats_indiv.json", "wb") as f:
        f.write(json_str)

    points_per_club["CLUB"] = points_per_club.index
    points_per_club.to_csv("clubs.csv")
    points_per_club.loc[:, STR_RANK] = (
        points_per_club["TOTAL"].rank(method="min", ascending=False).astype(int)
    )
    club_rankings = points_per_club.to_dict("records", index=True)
    json_str = json.dumps(club_rankings, ensure_ascii=False, indent=4).encode("utf-8")
    with open(root.parent / "data" / "resultats_club.json", "wb") as f:
        f.write(json_str)
