## shell_get_depth_charts.py
# @author jcpoir
# Helper script used in the parallelization of depth chart queries.

import sys
import os
from get_depth_charts import get_depth_charts

start_idx, end_idx = int(sys.argv[1]), int(sys.argv[2])
get_depth_charts(start_idx, end_idx)
print(f"Import finished for start_idx = {start_idx} end_idx = {end_idx}")