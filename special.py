## special.py
# @author jcpoir
# Perform skewed voigt smoothing on offensive play distributions. Also calculate frequency
# distributions for associated events (i.e. fumbles, interceptions).

from skewed_voigt import *
from smoothing_tools import *

def get_x(n_yds):
  return np.linspace(100 - n_yds, 100, n_yds + 1)

def get_sack_dists(pbp_df, show_plots = False):
  ''' returns the yardage distributions for sacks, striated by formation (under center, shotgun) '''

  x = get_x(120)

  df = pbp_df[pbp_df.IsSack == True]
  out = pd.DataFrame()

  for formation in [-1, "under_center", "shotgun"]:

    print(f"\nSack, formation = {formation}")

    # (1) Filter by formation
    if formation == "shotgun": df1 = df[(df.Formation == "SHOTGUN") | (df.Formation == "NO HUDDLE SHOTGUN")]
    elif formation == "under_center": df1 = df[(df.Formation == "UNDER CENTER") | (df.Formation == "NO HUDDLE")]
    else: df1 = df.copy()

    # (2) Get frequencies and standardize to a probability dist
    y = get_yds_dist(df1, x, allow_events = True)
    y = y / np.sum(y)

    # (3) Fit a probability dist
    y1 = smooth_normalize(x, y, isSack = True)

    # (4) Record the results
    row = pd.DataFrame()
    row["PlayType"], row["Condition"], row["Distribution"], row["ypa^"] = ["SACK"], [formation], [str(y1)], [get_dist_mean(x,y)]

    if len(out) == 0: out = row.copy()
    else: out = pd.concat((out, row))

  return out

def get_int_dists(pbp_df, show_plots = False):
  ''' returns the yardage distributions for INTs, striated by pass type (short vs long) '''

  x = get_x(120)

  # Get a modified dataframe with calculated yardages
  # df = yardline_shift(pbp_df, is_turnover = True) # replacing this with an API call . . .

  df = pbp_df.copy()

  df = df[(df.IsInterception == True) & (df.IsIncomplete == False) & (df.PlayType == "PASS")]
  df["PassType"] = df.PassType.fillna("")

  ## TODO: review this code: may not be relevant/necessary for API!
  def filter_plays_int(df):
    ''' interception detection in this dataset it bad, so we'll filter out penalty reversals,
    other common mistaken INT detections '''

    bad_terms = set(["reviewed", "replay", "official", "nearly", "upheld", "overturned", "touchback"])
    is_INTs = []

    for desc in df.Description:

      is_INT = True
      for term in bad_terms:
        if term in desc.lower(): is_INT = False

      is_INTs.append(is_INT)

    return df[is_INTs]

  df = filter_plays_int(df)

  out = pd.DataFrame()
  for passType in [-1, "short", "deep"]:

    print(f"\nInterception, passType = {passType}")

    isType = lambda x : passType in x.PassType.lower()

    # (1) Filter by formation
    if passType in ("short", "deep"): df1 = df[df.apply(isType, axis = 1)]
    else: df1 = df.copy()

    # (2) Get frequencies and standardize to a probability dist
    y = get_yds_dist(df1, x, yard_col = "CalcYards", allow_events = True)
    y = y / np.sum(y)

    # (3) Fit a probability dist
    y1 = smooth_normalize(x, y)

    # (4) Record the results
    row = pd.DataFrame()
    row["PlayType"], row["Condition"], row["Distribution"], row["ypa^"] = ["INT"], [passType], [str(y1)], [get_dist_mean(x,y)]

    if len(out) == 0: out = row.copy()
    else: out = pd.concat((out, row))

  return out

def get_fum_dists(pbp_df, show_plots = False):
  ''' returns the yardage distributions for fumbles, segmented by pass length '''

  x = get_x(120)

  df = pbp_df[pbp_df.IsFumble == True]
  df["PassType"] = df.PassType.fillna("")
  out = pd.DataFrame()

  isType = lambda x : passType in x.PassType.lower()

  for play_cat in [-1, "rush", "short_pass", "deep_pass"]:

    print(f"\nFumble, play_cat = {play_cat}")

    # (1) Filter by play type
    if play_cat == "rush": df1 = df[df.PlayType == "RUSH"]

    elif play_cat == "short_pass":
      df1, passType = df[df.PlayType != "RUSH"], "short"
      df1 = df1[df1.apply(isType, axis = 1)]

    elif play_cat == "deep_pass":
      df1, passType = df[df.PlayType != "RUSH"], "deep"
      df1 = df1[df1.apply(isType, axis = 1)]

    else: df1 = df[(df.PlayType == "RUSH") | (df.PlayType == "PASS")]

    # (2) Get frequencies and standardize to a probability dist
    y = get_yds_dist(df1, x, allow_events = True)
    y = y / np.sum(y)

    # (3) Fit a probability dist
    y1 = smooth_normalize(x, y, show_plots = show_plots)

    # (4) Record the results
    row = pd.DataFrame()
    row["PlayType"], row["Condition"], row["Distribution"], row["ypa^"] = ["FUM"], [play_cat], [str(y1)], [get_dist_mean(x,y)]

    if len(out) == 0: out = row.copy()
    else: out = pd.concat((out, row))

  return out

def get_kickoff_dists(pbp_df, show_plots = False):
  ''' returns the yardage distributions for kickoffs '''

  x = get_x(135)

  # Get a modified dataframe with calculated yardages
  # df = yardline_shift(pbp_df, is_turnover = True)

  # Downselect to relevant plays
  df = pbp_df[pbp_df.PlayType == "KICKOFF"]
  out = pd.DataFrame()

  teams = df.OffenseTeam.unique().tolist()
  teams = sorted(teams)

  for team in teams:

    print(f"\nKickoff, team = {team}")
    if len(team) == 0: continue

    # (1) Filter by team
    df1 = df[df.DefenseTeam == team]

    # (1a) ID Touchbacks and get a touchback rate! For simulation
    is_touchback  = lambda x : "touchback" in x.lower()
    touchbacks = df1.Description.apply(is_touchback)

    df1, touchback_df = df1[touchbacks == False], df1[touchbacks]
    touchback_rate = len(touchback_df) / (len(touchback_df) + len(df1))

    # (1b) Touchdown Rate
    TD_rate = df1.IsTouchdown.sum() / len(df1)

    # (2) Get frequencies and standardize to a probability dist
    y = get_yds_dist(df1, x=x, yard_col = "CalcYards", allow_events = True)
    y[15] = 0
    y = y / np.sum(y)

    # (3) Fit a probability dist
    y1 = smooth_normalize(x, y, show_plots = show_plots, isKickoff = True)

    # (4) Record the results
    row = pd.DataFrame()
    row["PlayType"], row["OffenseTeam"], row["Distribution"], row["Touchback%"], row["TD%"], row["ypa^"] = ["KICKOFF"], [team], [str(y1)], [touchback_rate], [TD_rate], [get_dist_mean(x,y)]
    row["Player1"] = [get_player_usage(df1, {"PlayType": "KICKOFF", "OffenseTeam": team}, 1)]

    if len(out) == 0: out = row.copy()
    else: out = pd.concat((out, row))

  return out

def get_punt_dists(pbp_df, show_plots = False):
  ''' returns the yardage distributions for punts '''

  x = get_x(135)

  # Get a modified dataframe with calculated yardages
  # df = yardline_shift(pbp_df, is_turnover = True) See note above!

  # Downselect to relevant plays
  df = pbp_df[pbp_df.PlayType == "PUNT"]
  out = pd.DataFrame()

  teams = df.OffenseTeam.unique().tolist()
  teams = sorted(teams)

  for team in teams:
    print(f"\nPunt, team = {team}")
    if len(team) == 0: continue

    # (1) Filter by team
    df1 = df[df.OffenseTeam == team]

    # (1a) ID Touchbacks and get a touchback rate! For simulation
    is_touchback  = lambda x : "touchback" in x.lower()
    touchbacks = df1.Description.apply(is_touchback)

    df1, touchback_df = df1[touchbacks == False], df1[touchbacks]
    touchback_rate = len(touchback_df) / (len(touchback_df) + len(df1))

    # (1b) Touchdown Rate
    TD_rate = df1.IsTouchdown.sum() / len(df1)

    # (2) Get frequencies and standardize to a probability dist
    y = get_yds_dist(df1, yard_col = "CalcYards", x = np.linspace(-35,100,136), allow_events = True)
    y[15] = 0
    y = y / np.sum(y)

    # (3) Fit a probability dist
    y1 = smooth_normalize(x, y, show_plots = show_plots, isKickoff = True)

    # (4) Record the results
    row = pd.DataFrame()
    row["PlayType"], row["OffenseTeam"], row["Distribution"], row["Touchback%"], row["TD%"], row["ypa^"] = ["PUNT"], [team], [str(y1)], [touchback_rate], [TD_rate], [get_dist_mean(x,y)]
    row["Player1"] = [get_player_usage(df1, {"PlayType": "PUNT", "OffenseTeam": team}, 1)]

    if len(out) == 0: out = row.copy()
    else: out = pd.concat((out, row))

  return out

def get_fg_percentages(pbp_df, min_val = 0.02, max_val = 0.98):
  ''' Get and record historical FG percentages, by team and yard range '''

  x = get_x(120)

  df = pbp_df[pbp_df.PlayType == "FIELD GOAL"]

  teams = df.OffenseTeam.unique().tolist()
  teams = sorted(teams)

  out = pd.DataFrame()

  for team in pbp_df.OffenseTeam.unique():
    if len(team) == 0: continue

    for yardRange in [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 100)]:
      
      is_team = df.OffenseTeam == team
      df1 = df[(is_team) & (df.YardLineFixed >= yardRange[0]) & (df.YardLineFixed < yardRange[1])]

      isGood = lambda x : ("NO GOOD" not in x) & ("GOOD" in x)
      condition = df1.Description.apply(isGood)
      FGs = df1[condition]

      FG_rate = relevancy_calc_rate(df1, condition)
      if len(df1) == 0: FG_rate = min_val
      elif FG_rate < min_val: FG_rate = min_val
      elif FG_rate > max_val: FG_rate = max_val

      row = pd.DataFrame()
      row["OffenseTeam"], row["YardRange"], row["FG%"], row["n"] = [team], [str(yardRange)], [FG_rate], [len(FGs)]
      row["Player1"] = [get_player_usage(df1, {"PlayType": "FIELD GOAL", "OffenseTeam": team}, 1)]

      if len(out) == 0: out = row
      else: out = pd.concat((out, row))

  out.sort_values("FG%", ascending = False, inplace = True)
  return out

def gen_spec_distributions(filepath = "pipeline/data3.1.csv"): ## TDOD: change to data3 after filter addition!

  print("\n== Generating Special Teams Distributions ==")

  pbp_df = pd.read_csv(filepath)

  # SPEC1: Sack + INT + FUM
  df = get_sack_dists(pbp_df, show_plots = False)
  df = pd.concat((df, get_int_dists(pbp_df)))
  df = pd.concat((df, get_fum_dists(pbp_df)))
  df.to_csv("pipeline/spec1_.csv", index = False) # NB: added underscores to avoid cofusion with final SPEC1, SPEC2.csv etc.

  # SPEC2: Kick off + Punt
  df = get_kickoff_dists(pbp_df)
  df = pd.concat((df, get_punt_dists(pbp_df)))
  df.to_csv("pipeline/spec2_.csv", index = False)

  # SPEC3: FG
  df = get_fg_percentages(pbp_df)
  df.to_csv("pipeline/spec3_.csv", index = False)