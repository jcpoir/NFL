## shell_defense_offense.py

import sys
import os
from defense_offense import gen_distributions

side, start_idx, end_idx = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
gen_distributions(side=side, idx_low=start_idx, idx_high=end_idx, verbose=False)
print(f"Generation finished for side={side} start_idx={start_idx}")