## depth_chart_parallel_import.py
# @author jcpoir
# Speeds up the querying of depth data from the ESPN API by splitting the work
# across eight threads. This is done by calling a bash script that calles a helper
# python script, which in turn interfaces directly with get_depth_charts.py

from helper import *

BASE_DIR, TARGET_DIR = "temp/", "pipeline/"
N_CORES = 6

def import_data(season, verbose = True, delay = 10):
    ''' Executes a parallel import of depth chart data, then aggregates. '''

    if verbose: print("\n== Parallelized Depth Chart Import (API) ==\n")
    run(f"bash depth_chart.sh {season} {N_CORES}")
    print("Waiting . . .\n")
    time.sleep(delay)
    print("Consolidating . . .\n")
    out = consolidate()

def consolidate():
    ''' Concatenates parallel compute results into one file. Then removes the intermediate files. '''

    out = pd.DataFrame()
    
    os.chdir(BASE_DIR)
    files = os.listdir()
    for file in files:
        if "depth_chart" not in file: continue
        df = pd.read_csv(file)
        out = pd.concat((df, out))
        run(f"rm {file}")
    os.chdir("..")

    out.to_csv(TARGET_DIR + "depth_charts.csv", index = False)