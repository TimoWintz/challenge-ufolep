import csv
import re
from collections import defaultdict

with open("collet.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

scratch_lines = []
in_scratch = False
for line in lines:
    if "CLASSEMENT : SCRATCH GÉNÉRAL" in line:
        in_scratch = True
        continue
    if "CLASSEMENT : SCRATCH UFOLEP" in line:
        break
    if in_scratch:
        scratch_lines.append(line)

parsed_entries = []
i = 0
while i < len(scratch_lines):
    line = scratch_lines[i].strip()
    if not line:
        i += 1
        continue

    # Check if it starts with a number (Clst)
    match = re.match(
        r"^(\d+)\s+(\d+)\s+(.*?)\s+([MF])\s+(.*?)(?:(\d+ème Catégorie|1ère Catégorie|Féminine))?\s+([A-Z0-9]+)\s*\([^)]+\)\s+(\d+)h\s+(\d+)\'(\d+)\'\'",
        line,
    )

    if match:
        clst = int(match.group(1))
        doss = int(match.group(2))
        nom_prenom = match.group(3).strip()
        sexe = match.group(4)
        club = match.group(5).strip()
        cat = match.group(7)
        h = int(match.group(8))
        m = int(match.group(9))
        s = int(match.group(10))
        parsed_entries.append(
            {
                "clst": clst,
                "doss": doss,
                "nom_prenom": nom_prenom,
                "club": club,
                "cat": cat,
                "h": h,
                "m": m,
                "s": s,
            }
        )
        i += 1
    else:
        # Try to match split lines
        # Case 1: gender is on the same line
        match_start = re.match(r"^(\d+)\s+(\d+)\s+(.*?)\s+([MF])\s+(.*)", line)
        # Case 2: gender is on the next line
        match_start2 = re.match(r"^(\d+)\s+(\d+)\s+(.*)", line)

        if (
            match_start
            and not "Clst DOS" in line
            and not "Les résultats" in line
            and not "La solution" in line
            and not "PME," in line
            and not "contact@gsi38.fr" in line
        ):
            clst = int(match_start.group(1))
            doss = int(match_start.group(2))
            nom_prenom = match_start.group(3).strip()
            sexe = match_start.group(4)
            club_part1 = match_start.group(5).strip()

            # Look ahead for the rest
            j = i + 1
            club_part2 = ""
            cat = ""
            h, m, s = 0, 0, 0
            while j < len(scratch_lines):
                next_line = scratch_lines[j].strip()
                if next_line:
                    match_end = re.search(
                        r"([A-Z0-9]+)\s*\([^)]+\)\s+(\d+)h\s+(\d+)\'(\d+)\'\'",
                        next_line,
                    )
                    if match_end:
                        cat = match_end.group(1)
                        h = int(match_end.group(2))
                        m = int(match_end.group(3))
                        s = int(match_end.group(4))
                        before_cat = next_line[: match_end.start()].strip()
                        if before_cat:
                            club_part2 = before_cat
                        i = j
                        break
                    else:
                        club_part2 += " " + next_line
                j += 1

            club = (club_part1 + " " + club_part2).strip()
            club = re.sub(r"\d+ème Catégorie", "", club).strip()
            club = re.sub(r"1ère Catégorie", "", club).strip()
            club = re.sub(r"Féminine", "", club).strip()

            parsed_entries.append(
                {
                    "clst": clst,
                    "doss": doss,
                    "nom_prenom": nom_prenom,
                    "club": club,
                    "cat": cat,
                    "h": h,
                    "m": m,
                    "s": s,
                }
            )
            i += 1
        elif (
            match_start2
            and not "Clst DOS" in line
            and not "Les résultats" in line
            and not "La solution" in line
            and not "PME," in line
            and not "contact@gsi38.fr" in line
        ):
            clst = int(match_start2.group(1))
            doss = int(match_start2.group(2))
            nom_prenom = match_start2.group(3).strip()

            # Look ahead for the rest
            j = i + 1
            club_part2 = ""
            cat = ""
            h, m, s = 0, 0, 0
            sexe = ""
            while j < len(scratch_lines):
                next_line = scratch_lines[j].strip()
                if next_line:
                    if not sexe:
                        match_sexe = re.match(r"^([MF])\s+(.*)", next_line)
                        if match_sexe:
                            sexe = match_sexe.group(1)
                            next_line = match_sexe.group(2)

                    match_end = re.search(
                        r"([A-Z0-9]+)\s*\([^)]+\)\s+(\d+)h\s+(\d+)\'(\d+)\'\'",
                        next_line,
                    )
                    if match_end:
                        cat = match_end.group(1)
                        h = int(match_end.group(2))
                        m = int(match_end.group(3))
                        s = int(match_end.group(4))
                        before_cat = next_line[: match_end.start()].strip()
                        if before_cat:
                            club_part2 += " " + before_cat
                        i = j
                        break
                    else:
                        club_part2 += " " + next_line
                j += 1

            club = club_part2.strip()
            club = re.sub(r"\d+ème Catégorie", "", club).strip()
            club = re.sub(r"1ère Catégorie", "", club).strip()
            club = re.sub(r"Féminine", "", club).strip()

            parsed_entries.append(
                {
                    "clst": clst,
                    "doss": doss,
                    "nom_prenom": nom_prenom,
                    "club": club,
                    "cat": cat,
                    "h": h,
                    "m": m,
                    "s": s,
                }
            )
            i += 1
        else:
            i += 1

# Calculate distance based on winner
winner = parsed_entries[0]
winner_time_h = winner["h"] + winner["m"] / 60 + winner["s"] / 3600
distance = 19.0 * winner_time_h

cat_counts = defaultdict(int)

with open("resultats.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(
        ["Class.", "Doss.", "Nom", "Prénom", "Club", "cat", "place", "Temps", "Moyenne"]
    )

    for entry in parsed_entries:
        cat_counts[entry["cat"]] += 1
        place = cat_counts[entry["cat"]]

        parts = entry["nom_prenom"].split()
        if len(parts) > 1:
            if parts[-1].lower() == "luc" and parts[-2].lower() == "jean":
                prenom = "Jean Luc"
                nom = " ".join(parts[:-2])
            elif parts[-1].lower() == "eliott" and parts[-2].lower() == "paul-":
                prenom = "Paul-Eliott"
                nom = " ".join(parts[:-2])
            else:
                prenom = parts[-1].capitalize()
                nom = " ".join(parts[:-1])
        else:
            prenom = ""
            nom = entry["nom_prenom"]

        temps_str = f"{entry['h']:02d}:{entry['m']:02d}:{entry['s']:02d},0"

        time_h = entry["h"] + entry["m"] / 60 + entry["s"] / 3600
        moyenne = distance / time_h if time_h > 0 else 0
        moyenne_str = f"{moyenne:.2f}".replace(".", ",")

        writer.writerow(
            [
                entry["clst"],
                entry["doss"],
                nom,
                prenom,
                entry["club"],
                entry["cat"],
                place,
                temps_str,
                moyenne_str,
            ]
        )

print(f"Processed {len(parsed_entries)} entries.")
