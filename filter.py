## filter.py
# @author jcpoir
# Filters input data in a collection of ways. Examples include replacing NaN values
# with whitespace for certain columns and zero in others, and detecting/removing certain
# play types.

from api_parallel_import import run
from get_depth_charts import load_depth_charts
from helper import *

import warnings
warnings.filterwarnings("ignore")

def check_rank(pos, rank):
    ''' determine if the player is high enough on the depth chart to factor significantly
    into team performance '''

    if rank < 0: return False
    if pos == "wr": return rank <= 8
    if pos == "rb": return rank <= 4
    if pos == "te": return rank <= 2
    if pos == "qb": return rank == 1
    else: return rank <= 2

def filter():

    print("\n== Filtering Dataset ==\n")

    df = pd.read_csv("pipeline/data2.csv")

    ## (1) Fill Specified NaN values
    for col in ["PassType", "Formation", "PlayType", "RushDirection"]:
        df[col].fillna("", inplace = True)

    # Remove non-useful playtypes
    for bad_playType in ["Penalty", "Safety"]:
        df = df[df.PlayType != bad_playType]

    # Remove plays where descriptions contain red flag terms
    for bad_term in ["penalty", "ruling", "upheld", "kneel"]:
        contains_bad_term = lambda x : (bad_term not in x.lower())
        cond = df.Description.apply(contains_bad_term)
        df = df[cond]
    
    # Handle issue where interceptions, fumbles have flipped offense, defense teams
    INTs = df.IsInterception == True
    df["OffenseTeam"][INTs], df["DefenseTeam"][INTs] = df["DefenseTeam"][INTs], df["OffenseTeam"][INTs]
    df["Player2"][INTs] = ""

    def resolve_fumbles(df):
        cond1 = df.IsFumble == True

        is_fum_turnover = lambda x : (("FUMBLES" in x) and ("RECOVER" in x))
        cond2 = df.Description.apply(is_fum_turnover)

        cond3 = cond1 & cond2

        df["OffenseTeam"][cond3], df["DefenseTeam"][cond3] = df.DefenseTeam[cond3], df.OffenseTeam[cond3]
        df["IsFumble"][cond2 == False] = 0 # For cases where a fumble is recovered, mark as non-fumbles

        return df
    
    df = resolve_fumbles(df)
   
    # Add explicit under center markers in "formation" column
    df["Formation"] = df["Formation"].replace("", "UNDER CENTER")

    # Handle issue with kickoff, punt team assignments
    def resolve_KO_punt(df):

        for playType in ("KICKOFF", "PUNT"):

            cond = df.PlayType == playType
            df_sub = df[cond]

            # (1) Define a new kick return, punt return playtypes
            df_R = copy.deepcopy(df_sub)
            df_R["Player1"], df_R["Player1_ID"], df_R["Player2"], df_R["Player2_ID"] = df_R.Player2, df_R.Player2_ID, "", ""
            df_R = df_R[df_R.Player1.isna() == False]
            df_R["PlayType"] = playType + " RETURN"

            # (2) Revise kickoff play information
            df["OffenseTeam"][cond], df["DefenseTeam"][cond] = df_sub.DefenseTeam, df_sub.OffenseTeam
            df["Player2"][cond], df["Player2_ID"][cond] = "", ""

            df = pd.concat((df, df_R))

        return df
    
    df = resolve_KO_punt(df)

    ## Add a second relevancy column
    df["Rel_Time"] = df["Relevancy"]

    print("Filtering complete [✓]")

    return df

def reassign_plays():
    ''' Checks depth charts and injury reports.
    (1) for players with injuries, removes their portion of relevancy from the play and removes
    their name from the involved players. 
    (2) for players who have moved to new teams, duplicates the play, removes their portion of relevancy
    from their original team's copy of the play, and adds their portion of relevancy to their new team's
    copy.
    (3) for players who are too low on the depth chart: (QB below rank 1, WR below rank 8, RB below rank 4, etc)
    remove their portion of relevancy. '''

    print("\n== Reassigning Injuries, Player Releases/Trades ==\n")

    dc_ref , player_ref = load_depth_charts()
    
    # Assign relevancy coefficients. Other will handle special players like kicker/punter
    R_PASS, R_RUSH, R_REC, R_SCRAMBLE, R_OTHER = 0.7, 0.7, 0.25, 0.75, 0.9
    
    # Assigns the importance of player1, player2, to the outcome of a given offensive play type.
    rel_ref = {"PASS" : [R_PASS, R_REC], "RUSH" : [R_RUSH, 0], "SCRAMBLE" : [R_SCRAMBLE, 0],
               "SACK" : [R_SCRAMBLE, 0], "OTHER" : [R_OTHER, 0]}
    
    # Load in post-filter() data
    df = pd.read_csv("pipeline/data3.csv")
    extra_rows = pd.DataFrame(columns = df.columns)
    block_idx = 1

    def reassign(row):
        nonlocal extra_rows, dc_ref, player_ref, block_idx

        player1_id, player2_id = row.Player1_ID, row.Player2_ID
        offenseTeam, playType = row.OffenseTeam, row.PlayType

        # (1) Initialize reference data structures
        rel_coeff, relevancy = 1.0, rel_ref["OTHER"]
        if playType in rel_ref: relevancy = rel_ref[playType]
        
        # (2) Apply relevancy modification, row reassignment
        curr_teams = []
        for i, id in enumerate([player1_id, player2_id]):

            if np.isnan(id): continue

            id = int(id)
            str_idx = i + 1 # Use for player1/player2 indexing
            alt_str_idx = int(i != 1) + 1

            # Check if the current player is in the ESPN database
            is_player_known = id in player_ref
            if is_player_known:

                pos, rank = player_ref[id]["Position"], player_ref[id]["Rank"]
                is_starter = check_rank(pos, rank)

                if is_starter:
                    curr_teams.append(player_ref[id]["Team"])
                else:

                    curr_teams.append("None")
                    rel_coeff -= relevancy[i]
                    row[f"Player{str_idx}"], row[f"Player{str_idx}_ID"] = "", ""
                    continue

            else: 
                
                curr_teams.append("None")
                rel_coeff -= relevancy[i]
                row[f"Player{str_idx}"], row[f"Player{str_idx}_ID"] = "", ""
                continue
        
            # Handle player1
            player_released, player_injured = curr_teams[i] != offenseTeam, player_ref[id]["Injury_Status"] not in ["H", "Q"]

            if player_released or player_injured:
                rel_coeff -= relevancy[i]

                # Initialize row copy for new team
                is_new_team = (curr_teams[i] != "None") and (curr_teams[i] != offenseTeam)
                if is_new_team and not player_injured:

                    new_row = copy.deepcopy(row)
                    new_row["Relevancy"] = new_row.Relevancy * relevancy[0] # Relevancy of the new row = just relevancy from the trader/released player
                    new_row[f"Player{alt_str_idx}"], new_row[f"Player{alt_str_idx}_ID"] = "", ""
                    new_row["OffenseTeam"] = curr_teams[i]

                    new_row = pd.DataFrame([new_row])
                    extra_rows = pd.concat([extra_rows, new_row])
                
                # Remove player from the original row
                row[f"Player{str_idx}"], row[f"Player{str_idx}_ID"] = "", ""

        def store_snapshot(df, block_size = 1000):
            ''' deals with the dampening of runtime efficiency by the dataframe extra_rows by outputting to .csv
            files periodically and aggregating at the end '''

            nonlocal block_idx

            if len(df) > block_size: 
                df.to_csv(f"temp/block{block_idx}.csv", index = False)
                block_idx += 1
                return pd.DataFrame()
            
            return df
        
        extra_rows = store_snapshot(extra_rows)

        row["Relevancy"] = row.Relevancy * rel_coeff
        return row
    
    tqdm.pandas()
    df["Rel_Time"] = df["Relevancy"] ## Save time-only relevnacy before player injuries/trades are accounted for. "Rel_Time" is used to determine target share later
    df = df.progress_apply(reassign, axis = 1)
    
    # Aggregate extra rows
    for i in range(block_idx-1, 0, -1):
        filepath = f"temp/block{i}.csv"
        block_df = pd.read_csv(filepath)
        extra_rows = pd.concat((extra_rows, block_df))
        run(f"rm {filepath}")
    df = pd.concat((df, extra_rows))

    print("\nReassignment complete [✓]")

    return df