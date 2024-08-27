import pandas as pd
import numpy as np
import requests
import json
from tqdm import tqdm
import re
import subprocess
import pandas as pd
import time
from pathlib import Path
import os
import copy
import pdb
import matplotlib.pyplot as plt
import math
from math import exp
import ast
import subprocess
import copy
import torch
from datetime import datetime

N_CORES = 8

# Helper functions
def get(URL):
  response = requests.get(URL)
  response = json.loads(response.text)
  return response

def remove_whitespace(input):
    return re.sub("\.\s+", ".", input)

def examine(dict):
    for col in dict:
        print(str(col) + ": " + str(dict[col]))

def run(command):
  ''' run the specified command via subprocess.run '''
  command = command.split(" ")
  process = subprocess.Popen(command)
  process.wait()

def segment_apply(df, fun, pbar_description = "", block_size = 10000):
  ''' Speeds up the .apply() function in pandas dataframe by spliting computation into unifornmly sized blocks and 
  concatenating full blocks rather than individual rows '''
   
  out = pd.DataFrame()

  start_idx, end_idx = 0, block_size
  _len = len(df)

  # Compute values for each block and store results in temporary .csv files
  n = 0
  while end_idx < _len:

    tqdm.pandas(desc = f"{end_idx}/{_len}")

    df1 = df[start_idx:end_idx].progress_apply(fun, axis = 1)
    start_idx += block_size
    end_idx += block_size

    df1.to_csv(f"temp/block{n}.csv")
    n += 1

  out = df[start_idx:].progress_apply(fun, axis = 1)

  # Read in blocks and consolidate results.
  pbar = range(n)
  pbar.set_description("Consolidating blocks.")
  for i in pbar:
     df = pd.read_csv(f"temp/block{i}.csv")
     out = pd.concat((df, out))
    
  return out