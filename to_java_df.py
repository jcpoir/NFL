## to_java_df.py
# @author jcpoir
# This script is responsible for convering distribution data, in csv format,
# into a more java-interpretable format that uses custom seperators and spacing

from smoothing_tools import *
import re

# (0) Defining term seperators
SEP1, SEP2 = "$", "&"

_, player_ref = load_depth_charts()

# (1) Support functions

def convert_dict(ref):
  ''' converts the dict "ref" into a compact java-readable string form '''

  out = ""
  for key in ref:
    val = ref[key]
    key, val = str(key), str(val)
    out = out + key + SEP2 + val + SEP1

  return out

def form_yardage_dist(row):

  # Convert string distribution to array
  dist = []
  for x in re.split("\s+", row.Dist[1:-1]):
    if len(x) == 0: continue
    try: dist.append(float(x.strip()))
    except: dist.append(0)

  yds = [x for x in range(100 - len(dist) + 1, 101)]

  # Assemble a dictionary from the arrays
  ref = {}
  for k,v in zip(yds, dist):
    ref[k] = v

  return convert_dict(ref)

col = "Player1"
def form_dist(row):
  global col

  # Case where no players detected
  if row[col] == "-1": return convert_dict({"NULL":1})

  # Convert string to dictionary
  ref = ast.literal_eval(row[col])

  return convert_dict(ref)

def form_player_dist(row):
  ''' like form_dist, but incorporates player id via lookup to player columns. 
  This is so that we can view player names in java but also have a value that may
  be used as an index '''

  global col, plyaer_ref

  # Case where no players detected
  if row[col] == "-1": return convert_dict({"NULL":1})

  # Convert string to dictionary
  ref = ast.literal_eval(row[col])

  out = {}
  for id in ref:
    id = int(id)
    # Player id is the input col value, get player name from the depth chart reference map
    name = player_ref[id]["Name"]
    player_tag = name + "+" + str(id)
    out[player_tag] = ref[id]

  return convert_dict(out)

# (2) Primary Conversion Functions

def to_java_df(df, team_col = "OffenseTeam"):
  ''' Converts an offense/defense df into a java-readable format '''

  global col

  df.fillna("-1", inplace = True)
  out = pd.DataFrame()

  ## (1) Define an index column that combines all metadata
  def form_index(row):
    if row["Yard Range"] != "-1": row["Yard Range"] = SEP2.join(re.split("[,\s+]+", row["Yard Range"][1:-1])) # deal w/ problematic yard range format (contains ",")
    idx = SEP1.join([str(x) for x in [row[team_col], row.PlayType, row["Yard Range"], row.Down]])
    return idx
  out["idx"] = df.apply(form_index, axis = 1)

  ## (2) Define a player, play selection distributions
  for i in [1, 2]:
    col = f"Player{i}_ID"
    out[f"Player{i}"] = df.apply(form_player_dist, axis = 1)
  for col in ("Formation", "RushDirection", "PassType", "PlayDist"):
    out[col] = df.apply(form_dist, axis = 1)

  ## (2a) Collect PlayType column as well, with PASS/RUSH breakdown
  def form_playtype(row):
    ref = {}
    ref["PASS"], ref["RUSH"] = row["PASS%"], row["RUSH%"]
    return convert_dict(ref)

  out["PlayType"] = df.apply(form_playtype, axis = 1)

  ## (3) Define play outcome distribution
  def form_outcome_dist(row):

    ref = {}
    for play in ["FUM", "INT", "SACK", "INC"]:
      ref[play] = row[play + "%"]

    return convert_dict(ref)

  out["outcome"] = df.apply(form_outcome_dist, axis = 1)

  ## (4) Define yardage/turnover distribution
  out["dist"] = df.apply(form_yardage_dist, axis = 1)

  return out

def spec_to_java_df(SPEC1_df, SPEC2_df, SPEC3_df):
  ''' Converts the special play dataframes into a java-readable format '''
  global col

  ## (1) Special Distributions (SPEC1)

  SPEC1 = pd.DataFrame()

  def form_index(row):
    idx = SEP1.join([str(row.PlayType), str(row.Condition)])
    return idx

  SPEC1["idx"] = SPEC1_df.apply(form_index, axis = 1)
  SPEC1_df.rename({"Distribution": "Dist"}, axis = 1, inplace = True)
  SPEC1["dist"] = SPEC1_df.apply(form_yardage_dist, axis = 1)

  ## (2) Kicking, Punting (SPEC2)

  SPEC2 = pd.DataFrame()

  def form_index(row):
    idx = SEP1.join(str(x) for x in [row.PlayType, row.OffenseTeam])
    return idx

  SPEC2["idx"] = SPEC2_df.apply(form_index, axis = 1)
  SPEC2_df.rename({"Distribution": "Dist"}, axis = 1, inplace = True)
  SPEC2["dist"] = SPEC2_df.apply(form_yardage_dist, axis = 1)

  col = "Player1_ID"
  SPEC2["player"] = SPEC2_df.apply(form_player_dist, axis = 1)

  ## (3) FGs

  SPEC3 = pd.DataFrame()

  def form_index(row):
    if row["YardRange"] != "-1": row["YardRange"] = SEP2.join(re.split("[,\s+]+", row["YardRange"][1:-1])) # deal w/ problematic yard range format (contains ",")
    idx = SEP1.join(str(x) for x in [row.OffenseTeam, row.YardRange])
    return idx

  SPEC3["idx"] = SPEC3_df.apply(form_index, axis = 1)
  SPEC3["FG%"] = SPEC3_df["FG%"]

  col = "Player1_ID"
  SPEC3["player"] = SPEC3_df.apply(form_player_dist, axis = 1)

  return SPEC1, SPEC2, SPEC3

# (2) Main function
def to_java_dfs():

  print("\n== Converting to Java Format ==\n")

  def r(filename):
    return pd.read_csv(f"pipeline/{filename}.csv")

  OFF_df, DEF_df, SPEC1_df, SPEC2_df, SPEC3_df = r("off1"), r("def1"), r("spec1_"), r("spec2_"), r("spec3_")

  OFF, DEF = to_java_df(OFF_df), to_java_df(DEF_df, team_col = "DefenseTeam")
  SPEC1, SPEC2, SPEC3 = spec_to_java_df(SPEC1_df, SPEC2_df, SPEC3_df)

  ## Write files to pipeline and java startpoint (data folder)
  def w(df, file):
    df.to_csv(f"pipeline/{file}.csv", index = False)
    df.to_csv(f"data/{file}.csv", index = False)

  w(OFF, "OFF")
  w(DEF, "DEF")
  w(SPEC1, "SPEC1")
  w(SPEC2, "SPEC2")
  w(SPEC3, "SPEC3")

  print("DONE\n")