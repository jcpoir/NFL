## depth_chart.sh
# @author jcpoir
# orchestrates a paralell import of all current depth charts

year=$1
n_cores=$2
n_teams=32

teams_per_thread=$(($n_teams / $n_cores))

start_idx=0
while [ $start_idx -lt $n_teams ]
do  
    echo "Executing year = $year start_idx = $start_idx"
    end_idx=$(($start_idx + $teams_per_thread))
    python3 shell_get_depth_charts.py $start_idx $end_idx &
    start_idx=$end_idx
done
wait