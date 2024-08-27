## defense_offense_parallel.py
# @author cjpoir
# splits up the computation of distributions across a predefined number of cores

from helper import *

N_CORES = 6

def gen_distributions(side = "OFF", show_plots = False, verbose = True):
    ''' Excecutes a parallel calculation of play distributions '''

    side_str = "Offense"
    if side == "DEF": side_str = "Defense"

    if verbose: print(f"\n== Parallelized Generation of {side_str[:-1]}ive Distributions ==\n")
    run(f"bash defense_offense.sh {N_CORES} {side}")
    if verbose: print(f"Generation complete [✓]")