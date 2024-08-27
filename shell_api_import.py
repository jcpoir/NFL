## shell_api_import.py

import sys
import os
from api_import import import_data

year, week, game_id = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
import_data(year, week ,game_id=game_id)
print(f"Import finished for year={year} week={week} game_id={game_id}")