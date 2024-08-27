## gen_off_distributions.py
# @author jcpoir
# Perform skewed voigt smoothing on offensive play distributions. Also calculate frequency
# distributions for associated events (i.e. fumbles, interceptions).

from smoothing_tools import *
from skewed_voigt import *

def gen_off_distributions(n_target = 20, show_plots = False):
  ''' for each play type/team/year/player/yardage/down etc., get a distribution and save '''

  print("\n== Generating Offensive Distributions ==\n")

  pbp_df = pd.read_csv("pipeline/data3.1.csv", low_memory = False)

  playTypes = ["SCRAMBLE", "RUSH", "PASS", -1] # -1 will mean "don't apply a filter here" in all cases
  x = np.linspace(-20,100,121)

  # Apply a cascading filter across the fields
  for playType in playTypes:

    if playType != -1:
      if playType != "PASS": df1 = pbp_df[pbp_df["PlayType"] == playType]
      else: df1 = pbp_df[(pbp_df["PlayType"] == playType) | (pbp_df["PlayType"] == "SACK")] # bugfix: removing sacks from this section of analysis | (pbp_df["PlayType"] == "SACK")]
    else: df1 = pbp_df[(pbp_df["PlayType"] == "RUSH") | (pbp_df["PlayType"] == "PASS") | (pbp_df["PlayType"] == "SCRAMBLE") | (pbp_df["PlayType"] == "SACK")]

    y = get_yds_dist(df1, x)
    gen_reference_dist = smooth_normalize(x,y)

    for none in [None]: # Used to filter by year, not relevant for the pipeline . . . will leave in case we want to add another filter step!

    #   if year != -1: df2 = df1[df1.SeasonYear == year]
      df2 = df1.copy()

      for team in [team for team in df2.OffenseTeam.unique()]:

        if team != -1: df3 = df2[df2.OffenseTeam == team]
        else: df3 = df2.copy()

        y = get_yds_dist(df3, x)
        team_reference_dist = smooth_normalize(x,y)

        out_df = pd.DataFrame()
        for yardRange in [-1, (0,2), (3,7), (8,13), (14,100)]:

          if yardRange != -1: df4 = df3[(df3.ToGo >= yardRange[0]) & (df3.ToGo <= yardRange[1])]
          else: df4 = df3.copy()

          for down in (-1, "early", "late"):

            #try:
              if down == -1: df5 = df4.copy()
              else:
                cond = (df4.Down <= 2)
                if down == "early": df5 = df4[cond]
                if down == "late": df5 = df4[cond == False]

              # combine analytics, allowing for compensation with another dist
              metadata = {"PlayType" : playType, "OffenseTeam" : team, "Yard Range" : yardRange, "Down" : down}
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

            # except: print("[ERR]")

        out_df.to_csv(f"temp/{playType}+{team}+OFF.csv", index = False)