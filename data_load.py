## data_load.py
# @author jcpoir
# Not a part of the main pipeline. Uses API calls, merging code to 
# build up a full-season dataset

from api_parallel_import import import_data, run
from merge_forget import merge_forget
from tqdm import tqdm

def load_data(season):

    max_week  = 19
    if year < 2021: max_week = 18

    # For each week in the season . . .
    pbar = tqdm(range(1,max_week))
    pbar.set_description("Loading API data")
    for week in pbar:

        # Grab data from the ESPN API
        data = import_data(season, week)
        data.to_csv("temp/data1.csv", index = False)

        # Merge data into the growing dataset
        if week != 1: data = merge_forget(season, week, source_directory = "temp/")
        data.to_csv("temp/before.csv", index = False)

    run(f"mv temp/before.csv data/NFL_{season}.csv")

for year in range(2019, 2009, -1):  
    load_data(year)