## get_depth_charts.py
# @author jcpoir
# Stores depth chart information in a tabular format, then outputs to the "temp" directory
# results are aggregated by another script

from helper import *
import csv

def get_injuries(team_id):

    out = {}

    injury_data = get(f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/teams/{team_id}/injuries")["items"]
    for item in injury_data:

        ref_url = item[ref]
        player_id = ref_url.split("/")[-3]
        injury = get(ref_url)

        status = injury["type"]["abbreviation"]
        if status == "A": status = "H"

        returnDate = "N/A"
        if status != "H":
            returnDate = injury["details"]["returnDate"]

        out[player_id] = (status, returnDate)

    return out

def get_depth_charts(start_idx, end_idx, verbose = False):

    ref = "$ref"
    out = pd.DataFrame()

    # Query the list of team ids from ESPN
    depth_charts = {}
    teams = get("https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams")
    nfl = teams["sports"][0]["leagues"][0]["teams"]

    # For paralellization
    idx = 0

    for team in nfl:
        
        is_job = (idx >= start_idx) and (idx < end_idx)
        if not is_job: 
            idx += 1
            continue
        idx += 1
            
        # Unpack team metadata
        team_info = team["team"]
        team_id, team_name = team_info["id"], team_info["abbreviation"]

        # Load in data from the ESPN API
        injury_ref = get_injuries(team_id)

        # Query the team's depth chart
        URL = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2023/teams/{team_id}/depthcharts"
        depth_charts = get(URL)["items"]

        # Iterate through the depth charts (defense (0), offense (1), special teams (2))
        for depth_chart in depth_charts:
            
            # Iterate through position groups (WR, RB, DT, etc.)
            positions = depth_chart["positions"]

            for position_idx in positions:
                
                position = positions[position_idx]
                athletes = position["athletes"]

                if verbose:
                    pbar = tqdm(athletes)
                    pbar.set_description(f"Team: {team_name} Position: {position_idx}")
                else:
                    pbar = athletes

                # Iterate through athletes on a given team at a given position
                n_injuries = 0
                for athlete in pbar:

                    rank = athlete["rank"] - n_injuries # IMPORTANT: depth chart position
                    athlete_info = get(athlete["athlete"][ref])

                    # Gather athlete metadata
                    player_name, player_id = athlete_info["shortName"], athlete_info["id"] # Also include
                    jersey = 0
                    if "jersey" in athlete_info: jersey = athlete_info["jersey"]
                    
                    formatted_name = remove_whitespace(f"{jersey}-{player_name}")

                    # Save health data
                    injury_status, return_date  = "H", "N/A"
                    if player_id in injury_ref: 
                        player_data = injury_ref[player_id]
                        injury_status, return_date = player_data[0], player_data[1]

                    if injury_status not in ["H", "Q"]:
                        rank = -1
                        n_injuries += 1

                    # Save draft stats
                    experience, round, pick = athlete_info["experience"]["years"], -1, -1
                    if "draft" in athlete_info:
                        draft_info = athlete_info["draft"]
                        round, pick = draft_info["round"], draft_info["selection"]

                    # Save data for this player
                    df = pd.DataFrame()
                    df["Team"], df["Position"], df["Rank"] = [team_name], [position_idx], [rank]
                    df["Player"], df["Injury_Status"], df["Return_Date"] = [formatted_name], [injury_status], [return_date]
                    df["YOE"], df["Round"], df["Pick"] = [experience], [round], [pick]
                    df["Team_id"], df["Player_id"] = [team_id], [player_id]

                    out = pd.concat((out,df))

    out.to_csv(f"temp/depth_charts{start_idx}-{end_idx}.csv", index = False)

def load_depth_charts():
    ''' Reads in depth charts to a pandas dataframe, then deposits the data into a nested dictionary 
    for which dict[team][name] returns a dictionary of {rank:1, pos:"wr" . . . }. Also will return
     a player-centric reference dict. '''

    df = pd.read_csv("pipeline/depth_charts.csv")

    key_positions = set(["qb", "rb", "wr", "te"])

    # Initialize the output dictionary
    dc_ref, player_ref = {}, {}
    for team in df.Team.unique():
        dc_ref[team] = {}
        df1 = df[df.Team == team]

        for i in range(len(df1)):

            row = df1.iloc[i]

            player_id = row.Player_id
            ref = {}

            ## Ensure that key positions aren't overwritten. RB > KR
            plays_multiple_positions = player_id in player_ref
            if plays_multiple_positions:

                is_key_position = player_ref[player_id]["Position"] in key_positions
                rank = row["Rank"]
                is_top_option = rank == 1
                
                if is_key_position and not is_top_option:
                    continue

            for col in ["Position", "Rank", "Injury_Status", "Return_Date"]:
                ref[col] = row[col]

            dc_ref[team][player_id] = ref
            ref["Team"] = row["Team"]
            ref["Name"] = row["Player"]

            player_ref[player_id] = ref

    return dc_ref, player_ref

def load_depth_charts_2():
    ''' Loads depth charts in the format dc_ref[team][pos][rank]. This is used in enforce_min_usage() in smoothing
    tools. '''

    df = pd.read_csv("pipeline/depth_charts.csv")
    dc_ref = {}

    for team in sorted(df.Team.unique()):
        dc_ref[team] = {}
        df1 = df[df.Team == team]

        for pos in sorted(df1.Position.unique()):
            dc_ref[team][pos] = {}
            df2 = df1[df1.Position == pos]

            for rank in sorted(df2.Rank.unique()):
                df3 = df2[df2.Rank == rank]
                rank = int(rank)

                ## Changing to account for multiple players at the same depth chart rank
                players = []
                for i in range(len(df3)):

                    entry = df3.iloc[i]

                    id, name = entry.Player_id, entry.Player
                    players.append({"id": id, "name": name})

                dc_ref[team][pos][rank] = players

    return dc_ref

def add_java_formats(depth_chart_filepath, verbose = True):
    ''' Uses transformations to get a team + player format i.e. [NE]12-T.Brady, which can act as an index for
    players, and a URL format <a href = localhost:/ . . . '''

    print(LF + f"== Adding Java Formats to {depth_chart_filepath} ==" + LF)

    df = pd.read_csv(depth_chart_filepath)
    
    df["Player_java"] = df.apply(to_java_format, axis = 1)
    df["Player_link"] = df.apply(to_player_link, axis = 1)
    print(df["Player_link"])

    df.to_csv(depth_chart_filepath, index = False, quoting=csv.QUOTE_NONE)

    print("Formats added. [✓]" + LF)