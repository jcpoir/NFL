## api_parallel_import.py
# @author jcpoir
# Speeds up the querying of play-by-play data from the ESPN API by splitting the work
# across eight threads. This is done by calling a bash script that calles a helper
# python script, which in turn interfaces directly with api_import.py

from helper import *

N_GAMES = 16

def import_data(season, week, verbose = True, delay = 10):
  ''' Executes a parallel import of all ~16 games, then aggregates and removes temporary tables '''

  if verbose: print("\n== Parallelized API Import ==\n")
  run(f"bash load_data.sh {season} {week}")
  print("Waiting . . .")
  time.sleep(delay)
  print("Consolidating . . .")
  out = consolidate_week(season, week)

  return out
  
def consolidate_week(season, week):
  ''' Concatenates parallel compute results into one file. Then removes the intermediate files '''
  out = pd.DataFrame()
  for game_id in range(N_GAMES):

    filepath = f"temp/year={season}week={week}game_id={game_id}.csv"

    file = Path(filepath)
    if file.is_file() == False: continue

    temp = pd.read_csv(filepath)
    out = pd.concat((out,temp))

    run(f"rm {filepath}")
  return out