## defense_offense.py
# @author jcpoir
# The methods for generating offensive, defenive distributions have converged over time.
# This means that it no longer makes sense to use two seperate functions, so I'll be unifying them
# into one function here. Based on the current offense.py implementation

from smoothing_tools import *
from skewed_voigt import *

x = np.linspace(-20,100,121)

def gen_distributions(n_target = 20, show_plots = False, side = "OFF"):
  ''' for each play type/team/year/player/yardage/down etc., get a distribution and save '''

  global x
  
  side_str = "Offense"
  if side == "DEF": side_str = "Defense"

  print(f"\n== Generating {side_str[:-1]}ive Distributions ==\n")

  pbp_df = pd.read_csv("pipeline/data3.1.csv", low_memory = False)

  playTypes = ["SCRAMBLE", "RUSH", "PASS", -1] # -1 will mean "don't apply a filter here" in all cases

  # Apply a cascading filter across the fields
  for playType in playTypes:

    if playType != -1:
      if playType != "PASS": df1 = pbp_df[pbp_df["PlayType"] == playType]
      else: df1 = pbp_df[(pbp_df["PlayType"] == playType) | (pbp_df["PlayType"] == "SACK")] # bugfix: removing sacks from this section of analysis | (pbp_df["PlayType"] == "SACK")]
    else: df1 = pbp_df[(pbp_df["PlayType"] == "RUSH") | (pbp_df["PlayType"] == "PASS") | (pbp_df["PlayType"] == "SCRAMBLE") | (pbp_df["PlayType"] == "SACK")]

    y = get_yds_dist(df1, x)
    gen_reference_dist = smooth_normalize(x,y)
    
    team_col = f"{side_str}Team"
    for team in [team for team in df1[team_col].unique()]:

        if team != -1: df3 = df1[df1[team_col] == team]
        else: df3 = df1.copy()

        y = get_yds_dist(df3, x)
        team_reference_dist = smooth_normalize(x,y)

        out_df = pd.DataFrame()
        for yardRange in [-1, (0,2), (3,7), (8,13), (14,100)]:

            if yardRange != -1: df4 = df3[(df3.ToGo >= yardRange[0]) & (df3.ToGo <= yardRange[1])]
            else: df4 = df3.copy()

            for down in (-1, "early", "late"):

                if down == -1: df5 = df4.copy()
                else: cond = (df4.Down <= 2)
                if down == "early": df5 = df4[cond]
                if down == "late": df5 = df4[cond == False]

                # combine analytics, allowing for compensation with another dist
                metadata = {"PlayType" : playType, f"{side_str}Team" : team, "Yard Range" : yardRange, "Down" : down}
                print(metadata)

                if len(df5) == 0: df5 = df4.copy()
                if len(df5) == 0: df5 = df3.copy()

                # construct the y colummn
                y, scores = get_yds_dist(df5, x), get_yds_dist(df5, x, scoring = True)

                # adjust distributions for scoring
                y = score_adjust(y, scores, gen_reference_dist)

                # perform a constrained skewed voigt optimization
                _sum = np.sum(y)
                if _sum != 0: y = y / _sum # constrain to probability mass == 1

                # for small datasets, compensates by adding in less relevant examples (at a discount)
                n_examples = len(df5)
                y = supplement(y, team_reference_dist, n_examples, n_target = n_target)
                n_examples = len(df3)
                y = supplement(y, gen_reference_dist, n_examples, n_target = n_target)

                y1 = smooth_normalize(x, y, show_plots = show_plots)

                # calculate FUM%, TD% etc. for the down&distance and overall dataframes
                ref1 = calc_analytics(df5, y1, x, metadata = metadata)
                ref2 = calc_analytics(df3, y1, x, metadata = metadata)

                # take a weighted average of the metrics
                to_ignore = [col for col in metadata.keys()] + ["Dist", "n"]
                ref = combine_analytics(ref1, ref2, n_examples/n_target, to_ignore)

                # aggregate results in a dataframe
                out_df = record_analytics(out_df, ref)

        out_df.to_csv(f"temp/{playType}+{team}+{side}.csv", index = False)