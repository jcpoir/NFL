## smoothing_tools.py
# @author jcpoir
# Perform skewed voigt smoothing on (1) offensive play distributions, (2)
# defensive play distributions, and (3) special teams plays. Also calculate frequency
# distributions for associated events (i.e. fumbles, interceptions).

from get_depth_charts import *

# (1) Support functions

def get_depth_charts():
  ''' calls both load_depth_charts functions once, then saves the result for multiple uses. 
  These are just three different representations of the same data. dc1 is team+player centric,
  dc2 uses just player, and dc3 is team+position+rank. They are all required as they're used
  within functions in smoothing_tools'''

  dc1, dc2 = load_depth_charts()
  dc3 = load_depth_charts_2()

  return dc1, dc2, dc3

dc1, dc2, dc3 = get_depth_charts()

def get_yds_dist(pbp_df, x, scoring = False, yard_col = "Yards", allow_events = False):
  ''' gets y, the frequency distribution of yards-per play, based on the yards column of
  the play-by-play dataset. allow_events is set to true in special.py, so that sacks, 
   interceptions etc. may be captured in the analysis. '''

  df = copy.deepcopy(pbp_df)
  is_score = (df.IsTouchdown) | (df.IsTwoPointConversion)

  # extract the subset of non-special event plays (not touchdown, 2pt, fumble, interception)
  # these all must be handled separately
  if not allow_events:
    df = df[(df.IsFumble == False) & (df.IsSack == False) & (is_score == scoring) & (df.IsInterception == False) & (df.IsIncomplete == False)]

  yds_dist = relevancy_get_value_counts(df, yard_col, str_convert = False)
  y = []
  for i in x:
    if i not in yds_dist: y.append(0)
    else: y.append(yds_dist[i])
  y = np.array(y)

  return y

def standardize(ref):
  ''' Standardizes a dictionary so that the sum of all values == 1.0 '''

  total = 0
  for k in ref: total += ref[k]
  out = {}
  for k in ref: out[k] = ref[k] / total

  return out

def relevancy_calc_rate(df, condition, rel_column = "Relevancy"):
  ''' Given a dataframe and a subset-defining condition, compute and the relevancy-weighted average
   value. Used in calc_analytics to find stats like incompletion percentage (INC%) and touchdown
   percentage (TD%) '''

  condition = condition.astype(bool)
  ans = np.sum(df[condition][rel_column]) / np.sum(df[rel_column])
  return ans

def relevancy_get_value_counts(df, agg_col, rel_column = "Relevancy", str_convert = True):
  ''' Given a dataframe or dataframe subset df, returns a string-converted dictionary of relevancy-
  weighted term frequencies. Essentially, instead of doing a value count, this function groups by value
  and sums across the relevancy column. '''

  ref = df.groupby(agg_col).sum()[rel_column].to_dict()
  gb = df.groupby(agg_col).sum()[rel_column]
  ref = gb[gb != 0].to_dict() ## bugfix: solved issue of 0 P mass players getting minimum threshold usage in java simulations

  if str_convert: ref = str(ref)
  return ref

def get_conditions(playType, player, is_OFF = True):
  ''' Get playtype-specific conditions. Used in enforce_min_usage(). Serves different conditions for offense,
  defense (defined by the optional boolean input is_OFF) '''

  if is_OFF:

    if playType == "PASS":
      if player == 1: return {"qb-1" : 1.0} # Here we're enforcing that the starting qb will take 95% of snaps at MINIMUM

      if player == 2:
        return {
          "wr-1" : 0.25,
          "wr-2" : 0.15,
          "wr-3" : 0.05
        }
      
    if playType == "RUSH":
      return {
        "rb-1" : 0.3,
        "rb-2" : 0.1
      }
    
    if playType == "SCRAMBLE":
      return {"qb-1" : 1.0}
    
    if playType in ("KICKOFF", "FIELD GOAL"):
      return {"pk-1" : 1.0}
    
    if playType == "PUNT":
      return {"p-1" : 1.0}
    
    if playType == "KICKOFF RETURN":
      return {"kr-1" : 0.75}
    
    if playType == "PUNT RETURN":
      return {"pr-1" : 0.75}
    
  else:

    primary, secondary = ["lde", "ldt", "rdt", "lde", "slb", "mlb", "wlb"], ["lcb", "ss", "fs", "rcb"]
    out = {}

    if playType == "PASS":

      for rank, mult in zip(range(1,4), [8, 2, 1]):

        for pos in primary:
          idx = f"{pos}-{rank}"
          out[idx] = 4 * mult

        for pos in secondary:
          idx = f"{pos}-{rank}"
          out[idx] = mult

      return out
    
    else:

      for rank, mult in zip(range(1,4), [8, 2, 1]):

        for pos in primary:
          idx = f"{pos}-{rank}"
          out[idx] = mult

        for pos in secondary:
          idx = f"{pos}-{rank}"
          out[idx] = 4 * mult

      return out
      
def player_id_to_player(player_id_ref):
  ''' convert a dictionary of player ids to a dictionary of 
  player names in the form 12-T.Brady '''

  global dc2

  out = {}
  for id in player_id_ref:
    
    if id not in dc2: continue
    name = dc2[id]["Name"]
    out[name] = player_id_ref[id]

  return out
  
def enforce_min_usage(player_id_ref, team, conditions):
  ''' Looks at a reference dictionary of player usage, looks up players in depth_charts.csv, then
   ensures that each player is used at least the minimum amount required for their rank on the depth chart '''
  
  global dc2, dc3
  dc_ref = dc3

  player_id_ref = standardize(player_id_ref)
  
  usage_ref = {}

  # Condition syntax: "wr-1"
  for dc_pos in conditions:

    # Look up player id for the given depth chart position
    c = dc_pos.split("-")
    pos, rank = c[0], int(c[1])

    if pos not in dc_ref[team]: continue

    pos_group = dc_ref[team][pos]
    
    if rank in pos_group: player_id = dc_ref[team][pos][rank]["id"]
    else: continue

    # Find the minimum rate of usage for the given player, as stipulated by conditions
    required_min_rate = conditions[dc_pos]

    # Case where the player has no recorded usage. Set usage = minimum and continue
    not_in_ref = player_id not in player_id_ref
    if not_in_ref: usage_ref[player_id] = required_min_rate

    else:
      empirical_rate = player_id_ref[player_id]
      rate_too_low = empirical_rate < required_min_rate

      # Case where player has recorded usage, but not enough to satisfy their depth chart condition
      if rate_too_low:
        usage_ref[player_id] = required_min_rate
        player_id_ref.pop(player_id)

      # Case where player has enough usage. Still hold them out, but keep current usage level (higher than minimum)
      else:
        usage_ref[player_id] = empirical_rate
        player_id_ref.pop(player_id)

  # Reconcile holdouts (usage_ref) with empirical dict (player_id_ref)
  usage_total = 0
  for k in usage_ref:
    usage_total += usage_ref[k]

  # Scale non-condition values and deposit them
  remainder = 1 - usage_total
  if remainder > 0:
    for k in player_id_ref:
      usage_ref[k] = player_id_ref[k] * remainder

  # Standardize values again (as a precaution)
  total = 0
  for k in usage_ref: total += usage_ref[k]
  for k in usage_ref: usage_ref[k] = usage_ref[k] / total
  
  # Replace player ids with names
  out = player_id_to_player(usage_ref)

  return out

def get_player_usage(df, metadata, player_idx):
  ''' player_idx = 1 or 2 i.e. column "Player1" '''

  is_OFF = "OffenseTeam" in metadata

  playType = metadata["PlayType"]
  if is_OFF: team = metadata["OffenseTeam"]
  else: team = metadata["DefenseTeam"]

  player_id_ref = relevancy_get_value_counts(df, f"Player{player_idx}_ID", str_convert = False)
  conditions = get_conditions(playType, player_idx, is_OFF = is_OFF)
  
  if conditions != None:
    player_ref = enforce_min_usage(player_id_ref, team, conditions)

  else:
    player_ref = player_id_to_player(player_id_ref)

  return str(player_ref)

def score_adjust(dist, score_dict, reference_dist, verbose = False):
  ''' takes a yardage distribution without scoring (TD, 2pt) and adds in scoring
  using a high-confidence reference distribution. If a two-yard pass touchdown is
  scored, for example, the distribution of pass plays given that yards >= 2 will
  be added to the distribution. '''

  x = np.linspace(-20,100,121)
  if verbose: init_dist = [yds for yds in dist]

  for yds, freq in zip(x, score_dict):

    idx = int(yds) + 20 # convert number of yards to an index for distributions on the range [-20,100]

    to_add = reference_dist[idx:]
    total = np.sum(to_add)

    if total != 0: to_add = to_add / np.sum(to_add) * freq # normalize the distriution to have a probability mass of one, then scale to the freqency mass at the given yardage

    dist[idx:] = dist[idx:] + to_add

  if verbose:
    plt.bar(x, dist, color = "orange")
    plt.bar(x, init_dist, color = "black")
    plt.title("Change in Yardage Distribution with Scoring Adjustments")

  return dist

def calc_analytics(df, y1, x, metadata):
  ''' Takes the dataframe and smoothed yardage distribution, returns a dictionary of statistics '''

  # Save relevant metadata
  ref = metadata.copy()

  # Get special event incidence rates
  r = relevancy_calc_rate

  ref["n"] = sum(df.Relevancy)
  ref["INC%"] = r(df, df.IsIncomplete)
  ref["FUM%"] = r(df, df.IsFumble)
  ref["SACK%"] = r(df, df.IsSack)
  ref["INT%"] = r(df, df.IsInterception)
  ref["TD%"] = r(df, df.IsTouchdown)

  # Find rates of occurance for different play types. Simplifying assumption here is that sacks and scrambles
  # happen only on pass plays
  passes, rushes, scrambles, sacks = r(df, df.PlayType == "PASS"), r(df, df.PlayType == "RUSH"), r(df, df.PlayType == "SCRAMBLE"), r(df, df.PlayType == "SACK")
  total = passes + rushes + scrambles + sacks

  ref["PASS%"] = (passes + scrambles + sacks) / total
  ref["RUSH%"] = rushes / total

  success_rate = 1 - (ref["INC%"] + ref["FUM%"] + ref["INT%"] + ref["SACK%"])

  # Get player, pass/run type value counts
  rvc = relevancy_get_value_counts
  for col in ("Formation", "PassType", "RushDirection"): ref[col] = rvc(df, col)

  if metadata["PlayType"] != -1: ref["Player1"] = get_player_usage(df, metadata, 1)
  if metadata["PlayType"] == "PASS": ref["Player2"] = get_player_usage(df, metadata, 2)

  ref["PlayDist"] = rvc(df, "PlayType")

  # save dist
  ref["Dist"] = str(y1)
  ref["ypa^"] = np.sum([a*b for a,b in zip(x, y1)]) * success_rate # calculate an estimate for yards per attempt

  return ref

def record_analytics(df, analytics_ref):
  ''' Takes a running dataframe of distributions and a dictionary of analytics for the
  current row. Deposits the current row into the dataframe '''

  if len(df) == 0:
    df = pd.DataFrame()
    for term in analytics_ref:
      res = analytics_ref[term]
      if type(res) == list:
        res = res[0]
      df[term] = [res]

  else:
    df1 = pd.DataFrame()
    for stat in analytics_ref:
      df1[stat] = [analytics_ref[stat]]

    df = pd.concat((df, df1))

  return df

def supplement(y, dist, n_examples, n_target = 50, discount = 0.9):
  ''' Compensates for low sample size by adding in another distribution
      "y" is an np array of yardage frequencies, "dist" is another yardage
      dist np array '''

  if n_examples >= n_target: return y

  r = n_examples / n_target
  y = y * r + dist * (1-r) * discount
  y = y / np.sum(y)

  return y

def combine_analytics(ref1, ref2, r, to_ignore = []):
  ''' Performs a weighted sum of analytics between distributions. For non-
  numeric columns, iterates through the dicts and combines them '''

  to_ignore = set(to_ignore)

  ## PROBLEM: r is sometimes > 1!
  if r > 1: r = 1

  for col in ref1:
    if col in to_ignore: continue
    else:
      try:

        players1, players2 = ast.literal_eval(ref1[col]), ast.literal_eval(ref2[col])

        for player in players2:

          if player in players1: players1[player] = players1[player] * r + players2[player] * (1 - r)
          else: players1[player] = players2[player] * (1 - r)

        ref1[col] = players1

      except: 
        ref1[col] = ref1[col] * r + ref2[col] * (1-r)

  return ref1

def combine_def_analytics(ref1, ref2, _min = 0.1, _max = 5, to_ignore = {}):
  ''' Performs a ratio of analytics between defensive distributions. For non-
  numeric columns, iterates through the dicts and combines them '''

  to_ignore = set(to_ignore)

  for col in ref1:

    cond = type(ref1[col]) not in (int, float, np.float64)

    if cond: continue
    if col in to_ignore: continue

    # case where ratio would be undefined (assign maximum allowed ratio)
    if ref2[col] == 0:
      ref1[col] = _max
      continue

    # calc ratio and bound
    ans = ref1[col] / ref2[col]
    if ans <= _min: ref1[col] = _min
    elif ans >= _max: ref1[col] = _max
    else: ref1[col] = ans

  return ref1

def save_figure(x,y,y1, metadata = {}, verbose = False):
  ''' takes a raw distribution "y" and a modified distribution 'y1' and
  plots a comparison chart. If verbose, output the chart to the console.
  Otherwise save the chart to drive! '''

  fig = plt.figure()
  plt.plot(x, y1, color = "orange")
  plt.bar(x,y, color = "black")

  title = " ".join([f"{key}: {metadata[key]}" for key in metadata])
  plt.title(title)
  if verbose: plt.show()
  else: fig.savefig(f"charts/team_dists/{title}.png")

def agg_distributions(group = "OFF"):
  ''' Creates a single csv file with all offensive data. Then eliminates all temporary files'''

  print("\n== Aggregating Temporary Files ==\n")

  pbp_df = pd.read_csv("pipeline/data3.csv", low_memory = False) ## TODO: finish filtering stage and change this to reading data3.csv!
  teams = pbp_df.OffenseTeam.unique()

  out_df = pd.DataFrame()
  for playType in ["RUSH", "SCRAMBLE", -1, "PASS"]:
    for team in tqdm(teams):
      
      isNaN = type(team) == float
      if isNaN: continue

      filepath = f"temp/{playType}+{team}+{group}.csv"

      try:
        if out_df.shape[0] == 0: out_df = pd.read_csv(filepath)
        else: out_df = pd.concat((out_df, pd.read_csv(filepath)))

      except: print(f"[ERR] {filepath}")

  subprocess.run(["rm", "-r", "temp"])
  subprocess.run(["mkdir", "temp"])

  out_df.to_csv(f"pipeline/{group.lower()}1.csv", index = False)

def get_tensors(x, y):
  ''' Returns array-like x and y as torch tensors, requiring gradients '''

  return torch.tensor(x, requires_grad = True), torch.tensor(y, requires_grad = True)

def yardline_shift(df,is_turnover = False):
  ''' some of the yardage calculations in the "Yards" columns — particularly those that
  are relevant to special plays — are incorrect. As a result, we need to calculate those
  values manually using abs(yardline i+1 - yardline i) '''

  ## Sort the input data by game id, minute, so that values are in sequence
  df.sort_values("Period", ascending = True, inplace = True)
  df.sort_values(["Date", "OffenseTeam", "Time"], inplace = True, ascending = False)

  ## Filter bad values
  df = df[df.PlayType != "TIMEOUT"]

  ## Find the yardage values as delta yardline
  yards = df.YardLine.tolist()
  after_yards, before_yards = np.array(yards + [0]), np.array([0] + yards)
  if is_turnover: after_yards = 100 - after_yards

  ## calc delta yardline
  out = after_yards - before_yards
  out = out[1:]

  df["CalcYards"] = out

  return df