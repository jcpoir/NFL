package simulations;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.TreeMap;

import tools.DataTable;

public class SeasonSimulator extends GameSimulator {
	
	List<String[]> matchups; DataTable season_df; DataTable curr_season_df;
	Map<String,String[]> divisions; Map<String,String[]> conferences;
	
	double SEASON_LEN = 17; double DIV_GAMES = 6; double CONF_GAMES = 13; double N_PLAYOFF_TEAMS = 7;

	public SeasonSimulator() throws IOException {
		super();
		loadMatchups(); initDivisions();
		initSeasonStats(); resetCurrSeasonStats();
	}
	
	// (0) Helper functions
	public void initDivisions() {
		
		divisions = new HashMap<>();
		
		divisions.put("AFC North", new String[] {"CIN", "PIT", "BAL", "CLE"});
		divisions.put("AFC East", new String[] {"NE", "MIA", "BUF", "NYJ"});
        divisions.put("AFC South", new String[] {"HOU", "IND", "JAX", "TEN"});
        divisions.put("AFC West", new String[] {"KC", "LV", "DEN", "LAC"});
        divisions.put("NFC North", new String[] {"GB", "CHI", "MIN", "DET"});
        divisions.put("NFC East", new String[] {"DAL", "PHI", "WSH", "NYG"});
        divisions.put("NFC South", new String[] {"NO", "TB", "CAR", "ATL"});
        divisions.put("NFC West", new String[] {"SF", "SEA", "LAR", "ARI"});
        
        conferences = new HashMap<>();
        
        conferences.put("CIN" , new String[] {"AFC", "North"});
        conferences.put("PIT" , new String[] {"AFC", "North"});
        conferences.put("BAL" , new String[] {"AFC", "North"});
        conferences.put("CLE" , new String[] {"AFC", "North"});
        conferences.put("NE"  , new String[] {"AFC", "East"});
        conferences.put("MIA" , new String[] {"AFC", "East"});
        conferences.put("BUF" , new String[] {"AFC", "East"});
        conferences.put("NYJ" , new String[] {"AFC", "East"});
        conferences.put("HOU" , new String[] {"AFC", "South"});
        conferences.put("IND" , new String[] {"AFC", "South"});
        conferences.put("JAX" , new String[] {"AFC", "South"});
        conferences.put("TEN" , new String[] {"AFC", "South"});
        conferences.put("KC"  , new String[] {"AFC", "West"});
        conferences.put("LV"  , new String[] {"AFC", "West"});
        conferences.put("DEN" , new String[] {"AFC", "West"});
        conferences.put("LAC" , new String[] {"AFC", "West"});
        conferences.put("GB"  , new String[] {"NFC", "North"});
        conferences.put("CHI" , new String[] {"NFC", "North"});
        conferences.put("MIN" , new String[] {"NFC", "North"});
        conferences.put("DET" , new String[] {"NFC", "North"});
        conferences.put("DAL" , new String[] {"NFC", "East"});
        conferences.put("PHI" , new String[] {"NFC", "East"});
        conferences.put("WSH" , new String[] {"NFC", "East"});
        conferences.put("NYG" , new String[] {"NFC", "East"});
        conferences.put("NO"  , new String[] {"NFC", "South"});
        conferences.put("TB"  , new String[] {"NFC", "South"});
        conferences.put("CAR" , new String[] {"NFC", "South"});
        conferences.put("ATL" , new String[] {"NFC", "South"});
        conferences.put("SF"  , new String[] {"NFC", "West"});
        conferences.put("SEA" , new String[] {"NFC", "West"});
        conferences.put("LAR" , new String[] {"NFC", "West"});
        conferences.put("ARI" , new String[] {"NFC", "West"});

	}
	
	public boolean[] determineRelation(String[] matchup) {
		// Are teams in the same division? Conference? Returns an array of two booleans.
		
		String[] team1_info = conferences.get(matchup[0]); String[] team2_info = conferences.get(matchup[1]);
				
		boolean is_conf = team1_info[0].equals(team2_info[0]);
		boolean is_div = false;
				
		if (is_conf == true) {
			is_div = team1_info[1].equals(team2_info[1]);
		}
		
		boolean[] out = new boolean[] {is_conf, is_div};
		return out;
	}
	
	public Map<String,Integer> flipMap (Map<Integer,String> ref) {
		
		Map<String,Integer> out = new HashMap<>();
		for (Integer key : ref.keySet()) {
			out.put(ref.get(key), key);
		}
		
		return out;
	}
	
	public Map<Integer,String> renumber(Map<Integer,String> ref) {
		// Used to renumber playoff seeds after each round
		
		Map<Integer,String> out = new HashMap<>(); int i = 1;
		for (String val : ref.values()) {
			out.put(i, val); i++;
		}
		
		return out;
	}
	
	// (1) Tracking simulation stats
	public void initSeasonStats() {season_df = getSeasonDF();}
	
	public void resetCurrSeasonStats() {curr_season_df = getSeasonDF();}
	
	public DataTable getSeasonDF() {
		// Makes and returns a generic datatable for storing season data
		
		DataTable season_df = new DataTable();
		season_df.col("W"); season_df.col("L"); season_df.col("D"); season_df.col("Playoff%"); season_df.col("SB%");
		season_df.col("Win%"); season_df.col("Win% (conf)"); season_df.col("Win% (div)");
		
		return season_df;
	}
	
	public Map<String,Double> calcTieBreakerStats(Map<String,Double> stats, boolean[] is_div) {
		// Calculate win% overall and by conference, division
		
		Map<String,Double> out = new HashMap<>();
		
		double w = stats.get("W"); double d = stats.get("D");
		double win_p = (w + 0.5 * d);
		
		out.put("Win%", (win_p / SEASON_LEN));
		if (is_div[0]) out.put("Win% (conf)", (win_p / CONF_GAMES));
		if (is_div[1]) out.put("Win% (div)", (win_p / DIV_GAMES));
		
		return out;
	}
	
	public void addToSeasonStats(GameResult result, boolean[] is_div) {
		
		Map<String,Map<String,Double>> matchup_stats = result.matchup_stats;
		
		for (String team : matchup_stats.keySet()) {
			Map<String,Double> stats = matchup_stats.get(team);
						
			season_df.put(team, stats); curr_season_df.put(team, stats);
			
			// Calculate tiebreaker stats
			Map<String,Double> tiebreaker_stats = calcTieBreakerStats(stats, is_div);
			curr_season_df.put(team, tiebreaker_stats); season_df.put(team, tiebreaker_stats);
		}
	}
	
	public void recordPlayoffsTeams(Map<String,Map<Integer,String>> seeds) {
		
		Map<String,Double> made_playoffs = new HashMap<>();
		made_playoffs.put("Playoff%", 1.0);
		
		for (Map<Integer,String> conference : seeds.values()) {
			for (String team : conference.values()) {
				season_df.put(team, made_playoffs);
			}
		}
	}
	
	public void divSeasonStatsByN(double n) {
		season_df.divBy(n);
	}
	
	// (2) Reading in data
	public void loadMatchups(String filepath, int startWeek) throws IOException {
		
		// Read in lines of the input file
		BufferedReader br = new BufferedReader(new FileReader(new File(filepath)));
		
		matchups = new ArrayList<String[]>();
		
		String line;
		while ((line = br.readLine()) != null) {
			
			String[] components = line.split(",");
			
			boolean isFirst = "Week".equals(components[0]);
			if (isFirst) continue;
			
			int week = Integer.parseInt(components[0]);
			if (week < startWeek) continue;
			
			String[] matchup = new String[] {components[1], components[2]};
			matchups.add(matchup);
		}
	}
	
	public void loadMatchups() throws IOException {
		loadMatchups("data/NFL_2024_Matchups.csv", 1);
	}
	
	// (3) Displaying outputs
	public String formatSeasonStats() {
		/*
		 * Formats aggregated season win totals, playoff results, across teams into a readable tabular format. 
		 */
		
		String out = "";
		
		out += "\n== SEASON STATS ==\n\n";
		
		List<Entry<String, Map<String,Double>>> entries = season_df.sortByFields(new String[] {"SB%", "W", "Playoff%"});
		
		int n = 10; String s = "%-"+n+"s"; String f = "%-"+n+".2f";
		String headerFormat = s+s+s+s+s+s; String rowFormat = s+f+f+f+f+f;
		
		String header = String.format(headerFormat, "TEAM", "W", "L", "D", "Playoff%", "SB%");
		String[] columns = new String[] {"W", "L", "D", "Playoff%", "SB%"};
		
		out += header + "\n";
		
		for (Entry<String, Map<String, Double>> entry : entries) {
			Map<String,Double> row = entry.getValue(); String team = entry.getKey();
			
			out += String.format(s,team);
			for (String column : columns) {
				
				double stat = row.get(column);

				out += String.format(f,stat);
			}
			out += "\n";
		}
		
		out += "\n";
		return out;
	}
	
	// (4) Simulation
	public Map<String,Map<Integer,String>> toPlayoffStanding() {
		
		Map<String,Map<Integer,String>> seeds = new HashMap<>(); List<Entry<String, Map<String,Double>>> ranks;
		String[] tiebreaker_fields = new String[] {"Win%", "Win% (div)", "Win% (conf)"};
		
		// (1) Get division winners and seed them (!!)
		DataTable afc_division_winners = getSeasonDF(); DataTable nfc_division_winners = getSeasonDF();
		
		for (String division : divisions.keySet()) {
			DataTable division_df = getSeasonDF();
						
			// Set up a mini datatable containing only the division's stats
			String[] teams = divisions.get(division);
			for (String team : teams) {
				division_df.put(team, curr_season_df.get(team));
			}
			
			// Sort by relevant metrics
			ranks = division_df.sortByFields(tiebreaker_fields);
			
			// Get division winner as the top of the division ranks table (by win% div win%, conf win%) TODO: add head-to-head
			Entry<String,Map<String,Double>> division_winner = ranks.get(0);
			
			boolean is_AFC = division.contains("AFC");
			
			if (is_AFC) {afc_division_winners.put(division_winner.getKey(), division_winner.getValue());}
			else {nfc_division_winners.put(division_winner.getKey(), division_winner.getValue());
			}
		}
		
		// Determine seeds of division winners (1-4)
		Map<Integer,String> bracket; bracket = new TreeMap<>();
		ranks = nfc_division_winners.sortByFields(tiebreaker_fields);
		int i = 1; Set<String> in_playoffs = new HashSet<>();
		
		// add NFC teams to the bracket
		for (Entry<String, Map<String,Double>> rank : ranks) {
			String team = rank.getKey();
			bracket.put(i, team); in_playoffs.add(team); i++;
		}
		seeds.put("NFC", bracket);
		
		// add AFC teams to the bracket
		bracket = new TreeMap<>(); ranks = afc_division_winners.sortByFields(tiebreaker_fields); i = 1;
		for (Entry<String, Map<String,Double>> rank : ranks) {
			String team = rank.getKey();
			bracket.put(i, team); in_playoffs.add(team); i++;
		}
		seeds.put("AFC", bracket);
		
		// (2) Get wildcards and seed them (!!)
		
		// add the remaining "in the hunt" teams to new datatables for selection
		DataTable afc_in_hunt = getSeasonDF(); DataTable nfc_in_hunt = getSeasonDF();
		for (String team : curr_season_df.table.keySet()) {
			
			if (in_playoffs.contains(team)) continue;
			
			// get division, conference. Separate data by conference for this
			String[] affiliations = conferences.get(team); 
			String conference = affiliations[0];
			
			if (conference.equals("AFC")) afc_in_hunt.put(team, curr_season_df.get(team));
			if (conference.equals("NFC")) nfc_in_hunt.put(team, curr_season_df.get(team));
		}
		
		// add top three of each to seeds
		bracket = seeds.get("AFC"); ranks = afc_in_hunt.sortByFields(tiebreaker_fields); i = 5;
		for (Entry<String, Map<String,Double>> rank : ranks) {
			String team = rank.getKey();
			bracket.put(i,team); i++;
			
			if (i > N_PLAYOFF_TEAMS) {break;}
		}
		seeds.put("AFC", bracket);
		
		bracket = seeds.get("NFC"); ranks = nfc_in_hunt.sortByFields(tiebreaker_fields); i = 5;
		for (Entry<String, Map<String,Double>> rank : ranks) {
			String team = rank.getKey();
			bracket.put(i,team); i++;
			
			if (i > N_PLAYOFF_TEAMS) {break;}
		}
		seeds.put("NFC", bracket);
		
		return seeds;
	}
	
	public Map<String,Map<Integer,String>> simPlayoffRound(Map<String,Map<Integer,String>> seeds, int n_byes) throws IOException {
		
		Map<String,Map<Integer,String>> out = new HashMap<>(); boolean OT = true;
		
		for (String conference : new String[] {"AFC", "NFC"}) {
			
			// Unpack conference resources, create output map ...
			Map<Integer,String> conf_out = new TreeMap<>();
			Map<Integer,String> conf_seeds = seeds.get(conference);
			Map<String,Integer> seed_ref = flipMap(conf_seeds); // transpose the seeding map to be a lookup for teams
			
			int i = 0; int j = conf_seeds.size();
			
			// Give byes to the top n_byes teams
			for (i = 1; i <= n_byes; i++) {
				conf_out.put(i, conf_seeds.get(i));
			}
			
			GameResult result;
			
			while (i < j) {
				result = simulateMatchup(conf_seeds.get(i), conf_seeds.get(j), 1, false, OT, false, false);
				conf_out.put(seed_ref.get(result.winner), result.winner);
				i++; j--;
			}
			
			// Reset seeds to be consecutive
			conf_out = renumber(conf_out);
			
			out.put(conference, conf_out);
		}
		
				
		return out;
	}
	
	public String simSB(Map<String,Map<Integer,String>> seeds) throws IOException {
		String afc_team = seeds.get("AFC").get(1);
		String nfc_team = seeds.get("NFC").get(1);
		
		boolean OT = true;
		GameResult result = simulateMatchup(afc_team, nfc_team, 1, false, OT, false, false);
		
		return result.winner;
	}
	
	Map<String,Map<Integer,String>> simPlayoffRound(Map<String,Map<Integer,String>> seeds) throws IOException {
		return simPlayoffRound(seeds, 0);
	}
	
	public void simulateSeason(int n_trials, boolean verbose) throws IOException {
		
		Instant start = Instant.now();
		
		int j = matchups.size();
		for (int trial = 1; trial <= n_trials; trial++) {
			if (verbose) System.out.println("Simulating season " + trial + "/" + n_trials + " . . .");
			
			// (1) Regular Season
			int i = 1; 
			for (String[] matchup : matchups) {
	
				if (verbose) System.out.println("(" + i + "/" + j + ") " + matchup[0] + " vs " + matchup[1]);
				GameResult result = simulateMatchup(matchup[0], matchup[1], 1);
				
				// calculate additional stats
				boolean[] is_div = determineRelation(matchup);
				
				// add stats to the season stats bucket
				addToSeasonStats(result, is_div);
				i++;
			}
			
			// (2) Determine who made the playoffs
			Map<String,Map<Integer,String>> seeds = toPlayoffStanding();
			recordPlayoffsTeams(seeds);
			
			// (3) Playoffs
			
			// Wildcard
			int n_byes = 1; seeds = simPlayoffRound(seeds, n_byes);
			
			// Divisional
			seeds = simPlayoffRound(seeds);
			
			// Championships
			seeds = simPlayoffRound(seeds);
			
			// Super bowl
			String champ = simSB(seeds);
			season_df.increment(champ, "SB%");

			// (-1) Reset and prepare for the next trial
			resetCurrSeasonStats();
		}
		
		divBoxByN((double) n_trials, new String[] {"LNG"}); divSeasonStatsByN((double) n_trials); 
		calcFantasyPoints();
		
		String text = formatSeasonStats() + formatBoxScores() + formatFantasyPoints();
		writeToFile(text); System.out.println(text);
		displayTimeElapsed(start);
		
	}
	
	public static void main(String[] args) throws IOException {
		
		SeasonSimulator sim = new SeasonSimulator();
		
		boolean verbose = true; int n_trials = 10;
		sim.simulateSeason(n_trials, verbose);

	}
}
