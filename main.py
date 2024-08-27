## main.py
# @author jcpoir
# The file that calls all steps of preprocessing in sequence.

import pandas as pd

def run_pipeline(season, week):

    # Support for bypassing of steps
    dir = "pipeline/"
    p = lambda x : f"{dir}{x}.csv"
    def bypass(f1, f2):
        df = pd.read_csv(p(f1))
        df.to_csv(p(f2), index = False)

    # (1) Read in data from the ESPN API
    if False:
        from api_parallel_import import import_data
        data = import_data(season, week, verbose = True)
        data.to_csv(p("data1"), index = False)
    else:
        pass
        bypass("before", "data1")

    # (2) Merge new data into the dataset, abandon old data
    if True:
        from merge_forget import merge_forget
        data = merge_forget(season, week, merge = False)
        data.to_csv(p("data2"), index = False)
    else:
        pass
        bypass("data1", "data2")

    # (3) Filter data to account for injuries, roster changes
    if True:

        if True:
            from depth_chart_parallel_import import import_data
            import_data(season)

        from filter import filter, reassign_plays
        if True:
            data = filter()
            data.to_csv("pipeline/data3.csv", index = False)
        if True:
            data = reassign_plays()
            data.to_csv("pipeline/data3.1.csv", index = False)
    else:
        pass
        bypass("data2", "data3")

    # (4) Aggregate data into team distributions
    from smoothing_tools import agg_distributions
    from defense_offense import gen_distributions
    if True:
        gen_distributions(side = "OFF", show_plots = False)
        agg_distributions("OFF")
    
    if True:
        gen_distributions(side = "DEF", show_plots = False)
        agg_distributions("DEF")

    if True:
        from special import gen_spec_distributions
        gen_spec_distributions()

    # (5) Converting data into a java-readable format (END)
    if True:
        from to_java_df import to_java_dfs
        to_java_dfs()

run_pipeline(season = 2023, week = 1)