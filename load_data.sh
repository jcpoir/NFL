## load_data.sh
# @author jcpoir
# orchestrates a parallel import of a full week of ESPN NFL API data

year=$1
week=$2

game_id=0
while [ $game_id -le 7 ]
do
    python3 shell_api_import.py $year $week $game_id &
    echo "Executing year = $year week = $week game_id = $game_id"
    game_id=$((game_id + 1))
done
wait
echo "DONE (1/2)"

while [ $game_id -le 15 ]
do
    python3 shell_api_import.py $year $week $game_id &
    echo "Executing year = $year week = $week game_id = $game_id"
    game_id=$((game_id + 1))
done
wait
echo "DONE (2/2)"