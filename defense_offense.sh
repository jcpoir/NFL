## defense_offense.sh
# @author jcpoir

n_cores=$1
side=$2
n_target=$3
n_teams=32
n_playTypes=4
n_items=$(($n_teams * $n_playTypes))
items_per_thread=$(($n_items / $n_cores))

start_idx=0
while [ $start_idx -lt $n_items ]
do
    echo "Executing start_idx = $start_idx"
    end_idx=$(($start_idx + $items_per_thread))
    python3 shell_defense_offense.py $side $n_target $start_idx $end_idx &
    start_idx=$end_idx
done
wait