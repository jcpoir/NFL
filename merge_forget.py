## merge_forget.py
# @author jcpoir
# Links this week's play-by-play data with that of the previous year. 
# Drops the earliest data from the dataset

import pandas as pd
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"

# (1) Helper functions
def drop_index(df):
    index_col = "Unnamed: 0"
    if index_col in df.columns:
        df.drop(index_col, axis = 1, inplace = True)
    return df

def get_curr_date(dates):
    ''' returns the most recent date from an array-like of dates'''

    # convert to a list of datetimes
    for i, date in enumerate(dates):
        dates[i] = datetime.strptime(date, DATE_FORMAT)

    # compare to find the most recent (maximum) date
    curr_date = dates[0]
    for date in dates:
        if max(date, curr_date) == date: curr_date = date

    return curr_date

# (2) Primary function
def merge_forget(season, week, new_data = None, source_directory = "pipeline/", retain_weeks = 6 * 52, decay_coeff = 0.4, min_relevancy = 0.05, merge = True):
    ''' Merges in new data (from the past week) to the existing dataset. Removes data older than
    retain_weeks old from the dataset. Assigns relevancy scores to each entry based on the time delta
    from present, using the formula y = 0.2^(x/365), where x is the time delta from present of the datapoint
    in days and y is a relevancy score on (0,1]. '''

    print("\n== Merging, Forgetting ==\n")

    old_data = pd.read_csv(f"{source_directory}before.csv")

    if merge:
        # If user doesn't provide the loaded API data, load it from the saved .csv
        new_data_missing = (new_data == None)
        if (new_data_missing): new_data = pd.read_csv(f"{source_directory}data1.csv")

        # Drop indices when I (accidentally) include them
        old_data, new_data = drop_index(old_data), drop_index(new_data)
        
        # Consolidate data
        data = pd.concat((new_data, old_data))

    else: data = old_data

    # "Forget" data that exceeds the retaining threshold
    retain_days = retain_weeks * 7
    curr_date = get_curr_date(data.Date.tolist())
    def calc_timeDelta(date):
        ''' calculates the difference in time (number of days) between the date of the most recent game
        and the date of every game in the dataset '''
        td = curr_date - datetime.strptime(date, "%Y-%m-%d")
        return td.days
    data["TimeDelta"] = data.Date.apply(calc_timeDelta)
    data = data[data["TimeDelta"] <= retain_days]

    # Assign relevancy scores
    def calc_relevancy(n_days):
        relevancy = max(decay_coeff ** (n_days / 365), min_relevancy)
        return relevancy
    data["Relevancy"] = data.TimeDelta.apply(calc_relevancy)
    data.drop("TimeDelta", axis = 1, inplace = True)

    data.sort_values("Date", ascending = False, inplace = True)

    print("Merge-forget complete [✔]")

    return data