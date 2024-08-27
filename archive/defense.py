## defense.py
# @author jcpoir
# Perform skewed voigt smoothing on defensive play distributions. Also calculate frequency
# distributions for associated events (i.e. fumbles, interceptions).

from smoothing_tools import *
from skewed_voigt import *

def gen_def_distributions(n_target = 50, show_plots = False):
  ''' for each play type/team/year/player/yardage/down etc., get a distribution and save '''

  print("\n== Generating Defensive Distributions ==\n")

  pbp_df = pd.read_csv("pipeline/data3.csv", low_memory = False) # TODO: change to data3 when available

  playTypes = [-1, "RUSH", "SCRAMBLE", "PASS"] # -1 will mean "don't apply a filter here" in all cases
  x = np.linspace(-20,100,121)

  # Apply a cascading filter across the fields
  # for playType in playTypes:
  for playType in playTypes:

    if playType != -1:
      if playType != "PASS": df1 = pbp_df[pbp_df["PlayType"] == playType]
      else: df1 = pbp_df[(pbp_df["PlayType"] == playType)] # bugfix on removing sacks for pass analysis | (pbp_df["PlayType"] == "SACK")]
    else: df1 = pbp_df[(pbp_df["PlayType"] == "RUSH") | (pbp_df["PlayType"] == "PASS") | (pbp_df["PlayType"] == "SCRAMBLE") | (pbp_df["PlayType"] == "SACK")]

    #for year in range(2023, 2013, -1):
    for none in [None]:

      # if year != -1: df2 = df1[df1.SeasonYear == year]
      df2 = df1.copy()

      def get_avg_dist(df2, x):
        ''' get the season average distribution for a play type.
        used as a reference point for evaluating the relative
        efficacy of defenses '''

        y, scores = get_yds_dist(df2, x), get_yds_dist(df2, x, scoring = True)
        y = score_adjust(y, scores, y)
        y = y / np.sum(y)

        y = smooth_normalize(x, y, show_plots = show_plots)

        metadata = {"PlayType" : playType, "DefenseTeam" : -1, "Yard Range" : -1, "Down" : -1}
        ref = calc_analytics(df2, y, x, metadata = metadata)

        return y, ref

      y_avg, ref_avg = get_avg_dist(df2, x)

      # Sort the teams list!
      teams = [team for team in df2.DefenseTeam.unique()]
      sorted(teams)

      for team in teams:

        if team != -1: df3 = df2[df2.DefenseTeam == team]
        else: df3 = df2.copy()

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
              metadata = {"PlayType" : playType, "DefenseTeam" : team, "Yard Range" : yardRange, "Down" : down}
              print(metadata)
              def string_to_ref_dist(out_df, metadata):
                ''' loads the reference dist from the dataframe '''

                reference_dist_str = out_df[(out_df.PlayType == playType) & (out_df.DefenseTeam == team) & (out_df["Yard Range"] == -1) & (out_df.Down == -1)].iloc[0]["Dist"]

                reference_dist = []
                for x in reference_dist_str[1:-1].split(" "):
                  try: reference_dist.append(float(x.strip()))
                  except: continue
                reference_dist = np.array(reference_dist)

                return reference_dist

              # load the appropriate reference distribution
              def get_reference_dist(metadata, out_df):
                ''' generates a large sample-size distribution, for supplementing sparse distributions '''
                nonlocal df3, x

                playType, team, yardRange, down = metadata["PlayType"], metadata["DefenseTeam"], metadata["Yard Range"], metadata["Down"]

                y = get_yds_dist(df3, x)
                y = y / np.sum(y)

                y = smooth_normalize(x, y, show_plots = show_plots)

                return y

              reference_dist = get_reference_dist(metadata, out_df)

              if len(df5) == 0: df5 = df4.copy()
              if len(df5) == 0: df5 = df3.copy()

              # construct the y colummn
              y, scores = get_yds_dist(df5, x), get_yds_dist(df5, x, scoring = True)

              # adjust distributions for scoring
              y = score_adjust(y, scores, reference_dist)

              # perform a constrained skewed voigt optimization
              _sum = np.sum(y)
              if _sum != 0: y = y / _sum # constrain to probability mass == 1

              # for small datasets, compensates by adding in less relevant examples (at a discount)
              n_examples = len(df5)
              y = supplement(y, reference_dist, n_examples, n_target = n_target)

              # smooth the distribution via the normal dist abstraction
              y1 = smooth_normalize(x, y, show_plots = show_plots)

              # transform result dist into a ratio
              def to_def_dist(y, y_avg, min_ = 0.05, max_ = 20):
                ''' takes an normal input distribution, y, and transforms it into a
                relative distribution, where y[i] is the relative performance of the defense for
                plays of that distance. min_ and max_ parameters define the limits on allowable
                defense ratios (in the output array) '''

                out = []
                for yds, a_yds in zip(y, y_avg):

                  # case where average val is zero, undefined result resolves to max value
                  if a_yds == 0: out.append(max_)

                  else:
                    ans = yds/a_yds
                    if ans >= max_: out.append(max_)
                    elif ans <= min_: out.append(min_)
                    else: out.append(ans)

                return np.array(out)

              # y1 = to_def_dist(y1, y_avg) # Bugfix: changing the defense mechanism from ratio to weighted averaging between off, def dists!

              # save insights from each
              # save_figure(x, y, y1, metadata = metadata, verbose = True)

              # calculate FUM%, TD% etc. for the down&distance and overall dataframes
              ref1 = calc_analytics(df5, y1, x, metadata = metadata)
              ref2 = calc_analytics(df3, y1, x, metadata = metadata)

              # take a weighted average of the metrics
              to_ignore = [col for col in metadata.keys()] + ["Dist"] + ["n"]
              ref = combine_analytics(ref1, ref2, n_examples/n_target, to_ignore)

              # get defensive ratio stats
              # ref = combine_def_analytics(ref, ref_avg, to_ignore = to_ignore)

              # aggregate results in a dataframe
              out_df = record_analytics(out_df, ref)

            #except: print("[ERR]")

        out_df.to_csv(f"temp/{playType}+{team}+DEF.csv", index = False)