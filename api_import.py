## api_import.py
# @author jcpoir
# Grabs, formats NFL play-by-play data from the ESPN API for a given year/week

# (0) Imports & Setup
import requests
import json
import datetime
from datetime import date
import pandas as pd
import numpy as np
import copy
import re
from tqdm import tqdm
import pdb
import sys

from helper import *

ref = "$ref"

# (1) Helper Functions
def get(URL):
  
  response = requests.get(URL)
  response = json.loads(response.text)
  return response

def remove_list_format(term):
   ''' Some items in the dataset are inexplicably ending up in brackets, quotations.
    This function removes them (if they're present) '''
   
   if len(term) < 2: return term
   if (term[:2] == "'[") or (term[:2] == '"]'):
      return term[2:-2]
   return term

def add_players(play, out):
  ''' Determines the primary players involved in a play, as well as their fundammental
  roles, using the "participants" section of the API output '''

  off_athletes, off_athlete_ids, def_athletes, def_athlete_ids = [], [], [], []
  skill_positions = set(["QB", "WR", "WO", "TE", "RB", "HB", "FB", "K", "PK", "P"])
  non_skill_positions = set(["OL", "OT", "OG", "C", "RT", "RG", "LG", "LT"])

  for athlete in play["participants"]:
    ath_info = get(athlete["athlete"][ref])

    # Get metadata about players, form name + number into a pseudo-index
    name, number, id = ath_info["shortName"], ath_info["jersey"], ath_info["id"]
    athlete_str = remove_whitespace(f"{number}-{name}".upper())

    id, athlete_str = remove_list_format(id), remove_list_format(athlete_str)

    # Classify players by type
    team = get(ath_info["team"][ref])["abbreviation"]

    # Assumption: Offensive skill players or special teams = same team. Defensive Positions = other team
    position = ath_info["position"]["abbreviation"]

    if position in skill_positions: 
       off_athletes.append(athlete_str) # Only take involved players who touch the ball 
       off_athlete_ids.append(id)
    elif position not in non_skill_positions: 
       def_athletes.append(athlete_str)
       def_athlete_ids.append(id)

  # Distribute players into a dictionary, using columns from the input datatable format
  _len = len(off_athletes)
  if _len >= 2: out["Player2"], out["Player2_ID"] = off_athletes[1], off_athlete_ids[1]
  if _len >= 1: out["Player1"], out["Player1_ID"] = off_athletes[0], off_athlete_ids[0]
  out["OtherPlayers"], out["OtherPlayer_IDs"] = def_athletes, def_athlete_ids

  return out

def get_playTypes(play, row):
  ''' Interprets a string playType from the ESPN API into a collection of one-hot
  playType variables in the pbp dataset '''

  p = play["type"]["text"]
  row["PlayType"] = p # NOTE: the ESPN playtypes are slightly different from those in the original pbp

  playTypes = {
      "PASS" : ["Pass", "Intercept"],
      "RUSH" : ["Rush"],
      "SACK" : ["Sack"],
      "KICKOFF" : ["Kickoff"],
      "FIELD GOAL" : ["Field Goal"],
      "PUNT" : ["Punt"],
      "SCRAMBLE" : ["Scramble"]
  }

  for col in playTypes:
    for label in playTypes[col]:
      if label in p:
        row["PlayType"] = col

  ## (2) Encode playtype as a set of one-hot variables
  playTypes = {
      "IsRush" : ["Rush"],
      "IsPass" : ["Pass", "Interception"],
      "IsIncomplete" : ["Incompletion"],
      "IsInterception" : ["Intercept"],
      "IsFumble" : ["Fumble"],
      "IsSack" : ["Sack"],
      "IsTouchdown" : ["Touchdown"]
  }

  ## NEW: adding two-point conversion detection back in
  row["IsTwoPointConversion"] = int("TWO-POINT CONVERSION" in play["text"])

  # Check for substrings to determine values for one-hot playtype variables
  for col in playTypes:
    row[col] = 0
    for label in playTypes[col]:
      if label in p: 
        row[col] = 1
        break

  return row

def get_specialPlayTypes(play, row):
  ''' Specifically eliminates fumbles as a playtype and adds in scrambles.
  We label a fumble as a pass play if the play description contains the word
  "pass" and a rush play otherwise. If a rush play's description contains the word
  "scramble", it will be labeled as a scramble. '''

  p = play["type"]["text"]
  desc = play["text"]

  # (1) Reallocate fumbles
  if "Fumble" in p:
    if "pass" in desc: row["PlayType"] = "PASS"
    else: row["PlayType"] = "RUSH"

  # (2) Redefine scrambles
  if ("scramble" in desc) and ("Rush" in p):
    row["PlayType"] = "SCRAMBLE"

  return row

# (2) Primary function
def import_data(season, week, game_id = -1, verbose = False):
  global out

  is_parallel_compute = (game_id != -1)

  if verbose: print("\n== Importing Data from the ESPN API ==\n")

  out = pd.DataFrame()

  # Get all events for a team/season
  info = get(f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype=2&week={week}")

  events = info["events"]

  for i, event in enumerate(events):

    # Parallel compute: each function call will only take one game_id
    if is_parallel_compute:
       if i != game_id: 
          # print(f"Skipping event with id = {i}. Assigned only id = {game_id}")
          continue

    def import_event(event):

        out = pd.DataFrame()
        ## Get teams (both) from the event schema
        teams = []
        for j in range(2):
            team = event["competitions"][0]["competitors"][j]["team"]["abbreviation"]
            teams.append(team)

        if verbose: print(f"({i+1}) {event['name']} {event['id']}")
        event_id = event['id']
        event_date = event["date"].split("T")[0]

        pbp = get(f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{event_id}/competitions/{event_id}/plays?limit=500")
        plays = pbp["items"]

        if verbose: 
           pbar = tqdm(plays)
           pbar.set_description("Reading in play-by-play data")

        else: pbar = plays

        for play in pbar:
            
            try:

              row = {}

              def is_invalid(play):
                  ''' If the necessary information isn't present for the play, or if the play
                  isn't a relevant play type, avoid adding its data to the dataset '''

                  for col in ["team", "participants"]:
                      if col not in play: return True
                      return False

              if is_invalid(play): continue

              # (1) Collect relevant data about the play
              row["SeasonYear"] = season
              row["Week"] = week
              row["Date"] = event_date
              row["Description"] = play["text"]
              row["Yards"] = play["statYardage"]
              row["YardLine"] = play["start"]["yardLine"]
              row["YardLineFixed"] = play["start"]["yardsToEndzone"]
              row["CalcYards"] = play["start"]["yardsToEndzone"] - (100 - play["end"]["yardsToEndzone"]) # For special teams distributions i.e. kickoff, punt, normal yardage stats are incomplete for distribution approximation
              row["Down"] = play["start"]["down"]
              row["ToGo"] = play["start"]["distance"]
              row["Period"] = play["period"]["number"] ## For yardline shift . . .
              row["Time"] = play["clock"]["value"]

              off_team = get(play["team"][ref])["abbreviation"]

              # (2) Determine team data based on event, play metadata
              def get_def_team(off_team, teams):
                  ''' Since the defense team isn't explicitly listed in the json data of the play,
                  we'll use an indexing trick to get the defense team '''

                  idx = teams.index(off_team) 
                  return teams[idx == 0] # if idx == 0, returns 1. Otherwise, returns zero

              def_team = get_def_team(off_team, teams)
              row["OffenseTeam"], row["DefenseTeam"] = off_team, def_team

              # (3) Identify relevant players
              row = add_players(play, row)
              
              # (4) Identify play variety
              row = get_playTypes(play, row)
              row = get_specialPlayTypes(play, row)

              # (5) Identify formation/rush direction/passtype
              def get_formations(play, row):
                  ''' intuits formation, rush direction, pass type from the description of a play
                  by searching for key terms '''

                  formations = {
                      "Formation": ["(Shotgun)", "(Under Center)", "(No Huddle)", "(No Huddle Shotgun)"],
                      "RushDirection": ["left end", "left tackle", "left guard", "center", "right guard", "right tackle", "right end"],
                      "PassType": ["short left", "short middle", "short right", "deep left", "deep middle", "deep right"]
                  }

                  description = play["text"]

                  for col in formations:
                      row[col] = ""
                      for key_term in formations[col]:
                          if key_term in description:

                              if col == "Formation": key_term = key_term[1:-1] # Remove leading/trailing parentheses from the capture group
                              row[col] = key_term.upper()
                              break

                  return row

              row = get_formations(play,row)

              # (-1) Concatenate/save results
              def dict_to_df_format(ref):

                  out = {}
                  for key in ref:
                      out[key] = [ref[key]]
                  return out

              row = dict_to_df_format(row)
              row_df = pd.DataFrame.from_dict(row)

              def concat_dfs(out, row_df):

                  if len(out) == 0: return row_df
                  return pd.concat((out, row_df))

              out = concat_dfs(out, row_df)

            except: continue # print(f"[ERR] for play: {play['text']}")

        return out
    
    df = import_event(event)
    out = pd.concat((df,out))

  if is_parallel_compute: 
     if len(out) != 0: 
        out.to_csv(f"temp/year={season}week={week}game_id={game_id}.csv", index = False)

  return out