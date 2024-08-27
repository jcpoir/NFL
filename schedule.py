## Schedule conversion script
# Takes a schedule in the online format of team + opponents by week
# outputs a schema of week + homeTeam + awayTeam

import pandas as pd
import pdb

df = pd.read_excel("data/NFL_2024.xlsx")

out = pd.DataFrame(columns = ("Week", "homeTeam", "awayTeam"))

n_weeks = 18
def changeWeekFormat(row):
    global out

    homeTeam = row["TEAM"]
    print(homeTeam)
    
    for i in range(1, 19):
        
        awayTeam = row[i]
        if "@" in awayTeam: continue
        elif awayTeam == "BYE": continue

        ## Fix a naming inconsistency between datasets!
        if awayTeam == "LAR": awayTeam = "LA"
        if homeTeam == "LAR": homeTeam = "LA"
        if awayTeam == "WSH": awayTeam = "WAS"
        if homeTeam == "WSH": homeTeam = "WAS"

        new_row = pd.DataFrame.from_dict({"Week" : [i], "homeTeam" : [homeTeam], "awayTeam" : [awayTeam]})
        out = pd.concat((out, new_row))

    return

# for i in range(n_weeks):
#     df.rename({i : f"Week {i}"}, axis = 1, inplace = True)

df.apply(changeWeekFormat, axis = 1)

out.sort_values(["Week", "homeTeam", "awayTeam"], inplace = True)
out.to_csv("data/NFL_2024_Matchups.csv", index = False)