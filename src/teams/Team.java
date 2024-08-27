package teams;

import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.TreeMap;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;

public class Team {
	
	public static String SEP1 = "\\$"; public static final String SEP2 = "&"; static double TINY = 1e-5;
	public static Random r = new Random(); public int max_yards;
	
	public Map<String,Map<String,Map<Double,String>>> team_dists;
	public Map<String, Map<String,Map<String,Double>>> temp_dists;
	
	public String team_name; public String opp_name;
	
	public Map<String,double[]> ranges;
	
	static double TACKLE_rate = 0.86; static double TWO_TACKLE_rate = 0.14; static double DEF_ratio = 0.5; // this is the percentage of prediction that is alotted to defense
	
	public String getName() {return team_name;}
	
	public Team(Map<String,String> attributes, Map<String, Map<String,Map<String,Double>>> dists) {
		
		// Initialize bounds on allowable event rates (
		this.ranges = Team.init_ranges();
		
		// Generate the set of relevant indices to pull, based on the specified attributes
		Set<String> indices = getIndices(attributes);
		
		// Pull the specified distributions
		temp_dists = Team.filterData(indices, dists);
		
		// Standardize the indices (remove year, team)
		temp_dists = Team.standardizeIndices(attributes, temp_dists);
				
		// Add effects of defense by multiplying dist, outcome columns by defensive multipliers
		temp_dists = addDefenseEffects(temp_dists);
		
		// Convert all dists to probability dists, then output to an instance map "team_dists"
		this.team_dists = Team.toProbDists(temp_dists);
	}
	
	// (1) Direct calls from the init() function
	
	private static Map<String, double[]> init_ranges() {
		
		Map<String,double[]> ranges = new HashMap<String,double[]>();
		
		double[] sack_range = new double[] {0.005, 0.20};  		
		double[] int_range = new double[] {0.005, 0.20};
		double[] inc_range = new double[] {0.005, 0.80};
		double[] fum_range = new double[] {0.005, 0.80};
		double[] cmp_range = new double[] {0.20, 0.995};
		
		try {ranges.put("SACK", sack_range); ranges.put("INT", int_range); ranges.put("INC", inc_range);
		ranges.put("FUM", fum_range); ranges.put("CMP", cmp_range);
		} catch (Exception e) {e.printStackTrace();}
		
		return ranges;
	}

	private Set<String> getIndices(Map<String, String> attributes) {
		
		SEP1 = "$"; // deal w/ java escape character issue.
		
		// (0) init output set
		Set<String> out = new HashSet<String>();
		team_name = attributes.get("team"); opp_name = attributes.get("opponent");
		
		// (1a) get offense indices
		for (String play : new String[] {"-1", "PASS", "SCRAMBLE", "RUSH"}) {
			for (String yardage : new String[] {"-1", "14&100", "8&13", "3&7", "0&2"}) {
				for (String down : new String[] {"-1", "early", "late"}) {
					
					String[] components = new String[] {team_name, play, yardage, down};
					String idx = String.join(SEP1, components);
										
					out.add(idx);
				}
			}
		}
		
		// (1b) get defense indices
		for (String play : new String[] {"-1", "PASS", "SCRAMBLE", "RUSH"}) {
			for (String yardage : new String[] {"-1", "14&100", "8&13", "3&7", "0&2"}) {
				for (String down : new String[] {"-1", "early", "late"}) {
					
					String[] components = new String[] {opp_name, play, yardage, down};
					String idx = String.join(SEP1, components);
					
					out.add(idx + "$DEF");
				}
			}
		}
		
		// (2) get special teams indices
		String[] spec_idx = new String[] {"SACK" + SEP1 + "-1", "SACK" + SEP1 + "under_center", "SACK" + SEP1 + "shotgun", 
				"INT" + SEP1 + "-1", "INT" + SEP1 + "short", "INT" + SEP1 + "deep", "FUM" + SEP1 + "-1", "FUM" + SEP1 + "-1", 
				"FUM" + SEP1 + "short_pass", "FUM" + SEP1 + "deep_pass", "FUM" + SEP1 + "rush"};
		for (String idx : spec_idx) {out.add(idx);}
		
		// (3) get FG indices
		for (String fg_rng : new String[] {"0" + SEP2 + "10", "10" + SEP2 + "20", "20" + SEP2 + "30", "30" + SEP2 + "40", "40" + SEP2 + "50"}) {
			out.add(team_name + SEP1 + fg_rng);
		}
		
		// (4) get PUNT, KICKOFF indices
		out.add("PUNT" + SEP1 + team_name);
		out.add("KICKOFF" + SEP1 + team_name);
		
		return out;
	}
	
	private static Map<String, Map<String, Map<String,Double>>> filterData(Set<String> indices,
			Map<String, Map<String, Map<String,Double>>> dists) {
		
		Map<String, Map<String, Map<String,Double>>> out = new TreeMap<String, Map<String, Map<String,Double>>>();
		for (String idx : indices) {out.put(idx, dists.get(idx));}
		
		return out;
	}

	private static Map<String, Map<String,Map<String,Double>>> standardizeIndices(Map<String, String> attributes, Map<String, Map<String,Map<String,Double>>> temp_dists) {
		
		String SEP1 = "\\$";
		
		Set<String> bad_attr = new HashSet<String>();
		bad_attr.add(attributes.get("year")); bad_attr.add(attributes.get("team")); bad_attr.add(attributes.get("opponent"));
		
		Map<String, Map<String,Map<String,Double>>> out = new HashMap<String, Map<String,Map<String,Double>>>();
		
		for (String k : temp_dists.keySet()) {
			String[] components = k.split(SEP1);
			
			String new_idx = "";
			for (String component: components) {
				if (!bad_attr.contains(component)) {
					new_idx += component + "$";
				}
			}
			new_idx = new_idx.substring(0, new_idx.length() - 1);
			out.put(new_idx, temp_dists.get(k));

		}
		
		return out;
	}

 	private Map<String, Map<String, Map<String, Double>>> addDefenseEffects(Map<String,Map<String,Map<String,Double>>> temp_dists) {
		
		Set<String> keys = temp_dists.keySet(); Set<String> colsToDefend = new HashSet<String> (Arrays.asList("dist", "outcome"));
		
		Map<String,Map<String,Map<String,Double>>> out = new HashMap<>();
		
		for (String k : temp_dists.keySet()) {
			String def_key = k + "$DEF";
			boolean isOffense = keys.contains(def_key);
						
			if (isOffense) {
				
				boolean isCarry = (k.contains("RUSH") | k.contains("SCRAMBLE"));
												
				Map<String,Map<String,Double>> off = temp_dists.get(k);
				Map<String,Map<String,Double>> def = temp_dists.get(def_key);
				
				Map<String,Map<String,Double>> out1 = new HashMap<>();
				
				// HERE: save defensive players
				out1.put("DefPlayer", def.get("Player1"));
								
				for (String col : off.keySet()) {
					
					Map<String,Double> out2;
					
					if (colsToDefend.contains(col)) {
					
						Map<String,Double> off_col = off.get(col);
						Map<String,Double> def_col = def.get(col);
						
						out2 = new HashMap<>();
						
						// Track total for the purpose of standardization, adding a success % to the final outcome dist
						double total = 0.0;
						for (String yd : off_col.keySet()) {
							
							double off_val = off_col.get(yd); double def_val = def_col.get(yd);
							if ("".equals(off_val)) {off_val = 0.0;}
							if ("".equals(def_val)) {def_val = 1.0;}
							
							// NOTE: Important line of code (bugfixing)
							double new_val = off_val * (1 - DEF_ratio) + def_val * DEF_ratio;
							total += new_val;
							
							out2.put(yd, new_val);
						}
					
						// Add success% to the outcome dists
						if (col.equals("outcome")) {
							
							out2.put("CMP", 1-total);
							out2 = constrainOutcomes(out2, isCarry);
						}
						
						else {
							// Standardize the data so that total probability mass = 1
							out2 = standardizeData(out2, total);

						}
						
					} else {
						out2 = off.get(col);
					}
					
					out1.put(col, out2);
				}
				out.put(k, out1);
			} else if (!k.contains("DEF")){
				out.put(k, temp_dists.get(k)); // If it's not an offensive dist, just keep the original content
			}
		}
		return out;
	}
	
	private static Map<String,Map<String,Map<Double,String>>> toProbDists(Map<String,Map<String,Map<String,Double>>> temp_dists) {
		
		Map<String,Map<String,Map<Double,String>>> out = new HashMap<String,Map<String,Map<Double,String>>>();
		for (String k : temp_dists.keySet()) {
			
			Map<String,Map<Double,String>> out1 = new HashMap<String,Map<Double,String>>();
			Map<String,Map<String,Double>> td1 = temp_dists.get(k);
						
			for (String k1 : td1.keySet() ) {
				
				Map<Double,String> out2;
				Map<String,Double> td2 = td1.get(k1);
				
				out2 = Team.formProbDist(td2);
				out1.put(k1, out2);
				
				if (k1.equals("dist")) {
					
					// Define a display-friendly output map to print TODO: remove
					double ev = 0.0; TreeMap<Integer, Double> disp = new TreeMap<>();
					for (String key : td2.keySet()) {
						double v = td2.get(key); ev += v * Double.parseDouble(key);
						disp.put(Integer.parseInt(key), v);
					}
				}
				
			}
			out.put(k, out1);
		}
		
		return out;
	}
	
	// (2) Support functions 
	
 	private Map<String,Double> constrainOutcomes(Map<String,Double> in, boolean isCarry) {
 		
 		Map<String,Double> out = new HashMap<String,Double>();
 		
 		// (1) Case where it's not a carry. Constrain all outcomes
 		if (!isCarry) {
	 		for (String k : in.keySet()) {
	 			
	 			double v = in.get(k); double[] rng = ranges.get(k);
	 			if (v < rng[0]) {v = rng[0];} 
	 			else if (v > rng[1]) {v = rng[1];}
	 			
	 			out.put(k, v);
	 		}
 		}
 		
 		// (2) Case where it's a carry. Constrain only fumble, completion (other events are impossible)
 		if (isCarry) {
	 		for (String k : new String[] {"CMP", "FUM"}) {
	 			
	 			double v = in.get(k); double[] rng = ranges.get(k);
	 			if (v < rng[0]) {v = rng[0];} 
	 			else if (v > rng[1]) {v = rng[1];}
	 			
	 			out.put(k, v);
	 		}			
 		}
 		
		return out;
	}

	public static String formIndex(String[] components) {
		
		String idx = components[0];
		
		String[] bad_cs = {" ", "(", ")"};
		for (String bad_c : bad_cs) {
			idx = idx.replace(bad_c, "");// eliminate whitespace
		}
		
		if (idx.startsWith("\"")) {idx = idx.substring(1, idx.length());}
		if (idx.endsWith("\"")) {idx = idx.substring(0, idx.length() - 1);}
		return idx;
	}

	public static Map<String,Double> formDist(String content) {
		
		// Define output map
		Map<String,Double> out = new TreeMap<String,Double>();
		
		// Handle empty cases
		if (content.contains("NULL")) {
			out.put("NULL", (double) 1.0); return out;
		}
		
		String SEP1 = "\\$";
		String[] components = content.split(SEP1);
		
		for (String component: components) {
						
			String[] x = component.split(SEP2);
			if (x.length != 2) {continue;}
			if (x[1].equals("nan")) {x[1] = "1.0";}
					
			// Deposit entry into the output treemap
			try {
				String k = x[0]; Double v = Double.parseDouble(x[1]);
				out.put(k, v);
			}
			catch (Exception e) {
				System.out.println(x[0] + ": " + x[1] + " content : " + content);
			}

		}
		return out;
	}
	
	public static Map<String,Double> formFGDist(String content) {
		
		double fg_percentage = 0.0;
		if (!"".equals(content)) {fg_percentage = Double.parseDouble(content);}
		
		Map<String,Double> out = new HashMap<String,Double>();
		out.put("1", fg_percentage); out.put("0", 1-fg_percentage);
		
		return out;	
	}
	
	public static Map<Double,String> formProbDist(Map<String,Double> td) {
		
		// Define output map
		Map<Double, String> out = new TreeMap<Double, String>();
		
		// Loop 1: Get total
		Double total = (double) 0.0;
		for (String k: td.keySet()) {total += td.get(k);}
		
		// Loop 2: Fill the output map
		Double running_total = (double) 0.0;
		for (String k: td.keySet()) {
			Double v = td.get(k) / total; if (v == 0) v = TINY; // save from the zero-val indexing problem!!
			out.put(v + running_total, k);
			running_total += v;
			
			if (1 - running_total <= 0.001) break;
		}
		
		return out;
	}
	
	public static Map<String, Map<String,Map<String,Double>>> readDists(String DefenseFilepath, String OffenseFilepath, String[] SpecialFilepaths) throws IOException {
		
		Map<String, Map<String,Map<String,Double>>> PLAYS = new HashMap<String, Map<String,Map<String,Double>>>();
		
		String[] filepaths = {DefenseFilepath, OffenseFilepath, SpecialFilepaths[2]};
		
		// Populate the OFF, DEF dists
		for (String filepath : filepaths) {
			
			int low = 1; int high = 9;
			if (SpecialFilepaths[2].equals(filepath)) {high = 2;}
			
			// Start by just reading in the lines of the input files
			BufferedReader br = new BufferedReader(new FileReader(new File(filepath)));
					
			String line; String[] cols = {};
			int i = 0;
			while ((line = br.readLine()) != null) {
				i += 1;
	
				if (i == 1) {cols = line.split(","); continue;}				
	
				String[] components = line.split(",");
				
				// Save all distributions for the current index
				Map<String,Map<String,Double>> temp = new HashMap<String,Map<String,Double>>();
							
				// Build a hashmap String index
				String idx = Team.formIndex(components);
				
				// Handle case where last row component is left black (2023 SD Chargers bug)
				int high_ = Math.min(components.length - 1, high);
							
				for (int j = low; j <= high_; j++) {
					
					Map<String,Double> prob_dist = Team.formDist(components[j]);
					String col = cols[j];
					
					// deal with sepcial FG format
					if (col.equals("FG%")) {prob_dist = Team.formFGDist(components[j]);}
					
					// save each result to the temporary map
					temp.put(col, prob_dist);
				
				}	
				
				// Add defense idx tags where necessary
				if (filepath.equals(DefenseFilepath)) {idx = idx + "$DEF";}
				PLAYS.put(idx, temp);
			}
		}
		
		filepaths = Arrays.copyOfRange(SpecialFilepaths, 0, 2);
		
		// Populate the SPEC dist
		for (String filepath: filepaths) {
			
			// Start by just reading in the lines of the input files
			BufferedReader br = new BufferedReader(new FileReader(new File(filepath)));
					
			String line;
			int i = 0;
			while ((line = br.readLine()) != null) {
				i += 1;
	
				if (i == 1) {continue;}
				String[] components = line.split(",");
							
				// Build a hashmap String index
				String idx = Team.formIndex(components);
							
				Map<String,Double> prob_dist = Team.formDist(components[1]);
				
				// save each result to the temporary map
				Map<String,Map<String,Double>> temp = new HashMap<String,Map<String,Double>>();
				temp.put("dist", prob_dist); 
				
				// get the player column in SPEC2.csv
				if (components.length > 2) {
					Map<String,Double> player_dist = Team.formDist(components[2]);
					temp.put("player", player_dist);
				}
				
				PLAYS.put(idx, temp);
			}
		}
		
		String filepath = SpecialFilepaths[2];
		BufferedReader br = new BufferedReader(new FileReader(new File(filepath)));
		
		String line;
		int i = 0;
		while ((line = br.readLine()) != null) {
			i += 1;
			
			if (i == 1) {continue;}
			String[] components = line.split(",");	
		}
		
		return PLAYS;
	}
	
	public static String addYards(String yds) {
		if (yds == "1") {return yds + " yard";}
		return yds + " yards";
	}
	
	public void printExpectedValue(Map<String,Double> yardage_dist) {
		
		double mean_val = 0.0;
		for (String k : yardage_dist.keySet()) {
			double yds = Double.parseDouble(k); double prob = yardage_dist.get(k);
			mean_val += (yds * prob);
		}
		
		System.out.println(mean_val);
	}
	
	// The following two functions are used to convert game data (down and distance) to an index
	// to be used in play simulations
	
	public Map<String,Double> standardizeData(Map<String,Double> dist, double p_mass) {
		
		Map<String,Double> out = new HashMap<String,Double>();
		
		for (String k: dist.keySet()) {
			double v = dist.get(k); v = v / p_mass;
			out.put(k, v);
		}
		
		return out;
	}
	
	public static String downToDownRange(int down) {
		int EARLY = 2; int LATE = 4;
		
		if (down <= EARLY) return "early";
		return "late";
	}
	
	public static String distanceToDistanceRange(int distance) {
		int SHORT = 2; int MEDIUM1 = 7; int MEDIUM2 = 13; int LONG = 100;
		
		if (distance <= SHORT) return "0&"+SHORT;
		if (distance <= MEDIUM1) return "" + (SHORT+1) + "&" + MEDIUM1;
		if (distance <= MEDIUM2) return "" + (MEDIUM1+1) + "&" + MEDIUM2;
		return "" + (MEDIUM2+1) + "&" + LONG;
	}
	
	public static String yardlineToYardlineRange(int yardline) {
		
		yardline = 100 - yardline; // flip the field to find FG range!
		
		int[] markers = new int[] {10,20,30,40,50,100};
		
		int last = 0;
		for (int marker: markers) {
			if (yardline <= marker) return last + "&" + marker;
			last = marker;
		}
		
		return null;
	}
	
	// Gerates a random double on [0,1], then uses it to select a result from dist
	public static String randomSelect(Map<Double,String> dist) {
				
		double x = r.nextDouble();
		
		double k_ = 0.0;
		for (double k : dist.keySet()) {
			if (x <= k) {return dist.get(k);}
			k_ = k;
		}
		return dist.get(k_);
	}
	
	public static Map<String,String> randomSelectAll(Map<String,Map<Double,String>> dists) {
		
		Map<String,String> out = new HashMap<String,String>();
		
		for (String k: dists.keySet()) {
			out.put(k, Team.randomSelect(dists.get(k)));
		}
		
		return out;
	}
	
	public static String formPlayIndex(String play, String distance_rng, String down_rng) {
		return play + SEP1 + distance_rng + SEP1 + down_rng;
	}
	
	public static String formSackIndex(String formation) {
		
		if (formation.contains("under") & formation.contains("center")) return "SACK$under_center";
		else if (formation.contains("shotgun")) return "SACK$shotgun";
		else return "SACK$-1";
	}
	
	/**
	 * Takes a map of string : string play information from the game simulator, runs a randomized
	 * play based on its distributions, and outputs a map containing information about the play
	 * result (i.e. player1: 18-P.Manning, playType: "PASS", ... yards: "31")
	 * @param PlayInfo
	 * @return
	 */
	public Map<String,String> runPlay(Map<String,Integer> PlayInfo) {
		
		// Unpack game state dictionary, convert to ranges for the index
		int down = PlayInfo.get("down"); int distance = PlayInfo.get("distance");
		String down_rng = Team.downToDownRange(down); String distance_rng = Team.distanceToDistanceRange(distance);
		
		// Build an index for looking up plays
		String idx = Team.formPlayIndex("-1", distance_rng, down_rng);
		Map<String,Map<Double,String>> team_dist = team_dists.get(idx);
		
		// Select a play type at random
		String playType = Team.randomSelect(team_dist.get("PlayDist"));
		
		// Get maximum allowable yardage for TD
		int yardline = PlayInfo.get("yardline"); int max_yds = 100 - yardline;
				
		// Prepare the output map
		boolean attempt_FG = (down == 4) & (yardline >= 60); boolean punt = (down == 4) & (yardline < 50);
		
		if (attempt_FG) {return kickFG(yardline);}
		
		if (punt) return punt();
		
		else {return this.runPlay(down_rng, distance_rng, playType, max_yds);}
	}
	
	public Map<String,String> runPlay(String down_rng, String distance_rng, String playType, int max_yds) {
		
		max_yards = max_yds;
		
		// Initialize the final result map
		Map<String,String> out = new HashMap<String,String>();
		
		// Build an index for looking up plays
		String idx = Team.formPlayIndex(playType, distance_rng, down_rng);
		Map<String,Map<Double,String>> team_dist = team_dists.get(idx);
		
		String summary = "";
		
		if (playType.equals("SACK")) {
			
			out.put("attempt", "1");
			
			// Use a randomized pass play to get player1, formation
			String pass_idx = Team.formPlayIndex("PASS", distance_rng, down_rng);
			Map<String,String> play_selection = Team.randomSelectAll(team_dists.get(pass_idx));
			
			// Look up sack distribution by formation (only variable considered at this time)
			String formation = play_selection.get("Formation"); String p1 = play_selection.get("Player1");
			String outcome = play_selection.get("outcome");
			
			String sack_idx = Team.formSackIndex(formation);
			
			Map<String,Map<Double,String>> sack_dist = team_dists.get(sack_idx);
			
			String n_yds = capYards(Team.randomSelect(sack_dist.get("dist"))); String yds = Team.addYards(n_yds);
			
			// Generate a random yardage

			out.put("yards", n_yds); out.put("playType", playType); out.put("player1", p1);
			out.put("player2", null); out.put("isTurnover", "0");
			
			// Formulate output message
			summary = "(" + formation + ") "  + p1 + " SACKED for " + yds + ".";
			
			// Strip sack (special case)
			if (outcome.equals("FUM")) {
				String fum_message = " FUMBLES, recovered by " + opp_name + ".";
				summary += fum_message; out.put("isTurnover", "1");
			}
			
		}
		
		// If the play is not a sack . . .
		else {

			// Get the ingredients of the play
			Map<String,String> results = Team.randomSelectAll(team_dist);
			
			// Add defense content
			String def_player = results.get("DefPlayer"); String def_player_2 = Team.randomSelect(team_dist.get("DefPlayer"));
			double x = r.nextDouble();
			boolean is_tackle = x <= TACKLE_rate; boolean is_two_tackle = (x <= TWO_TACKLE_rate) & (!def_player.equals(def_player_2)); String tackle_str = "";
			if (is_two_tackle) tackle_str = " (" + def_player + ", " + def_player_2 + ")";
			else if (is_tackle) tackle_str = " (" + def_player + ")";
			
			// Unpacking offense/other information from Team randomSelectAll . . .
			String p1 = results.get("Player1"); String p2 = results.get("Player2"); String n_yds = capYards(results.get("dist")); // addYards changes plural "yards" to singular "yard" for one-yard plays
			String formation = results.get("Formation"); String passtype = results.get("PassType"); String rushdir = results.get("RushDirection");
			String outcome = results.get("outcome"); String yds = Team.addYards(n_yds);
			
			// Update the output
			out.put("yards", n_yds); out.put("playType", playType); out.put("player1", p1);
			out.put("player2", p2); out.put("isTurnover", "0");
			
			if (outcome.equals("SACK")) {
				out.put("attempt", "1");
				out = this.runPlay(down_rng, distance_rng, "SACK", max_yds); out.put("sack", "1"); return out;
			}
			
			summary = "(" + formation + ") " ;
			
			if (playType.equals("PASS")) {
				
				out.put("attempt", "1");
								
				if (outcome.equals("CMP")) {
					
					passtype = validatePassType(passtype, n_yds); out.put("complete", "1");
					summary +=  p1 + " pass " + passtype + " complete to " + p2 + " for " + yds + tackle_str + ".";
				}
				
				else if (outcome.equals("INC")) {
					summary += p1 + " incomplete pass " + passtype + ", intended for " + p2 + ".";
					out.put("yards", "0");
				}
				
				else if (outcome.equals("INT") ) {
					summary += p1 + " pass " + passtype + " intended for " + p2 + " INTERCEPTED by " + opp_name + " and returned for " + yds + tackle_str + ".";
					out.put("isTurnover", "1"); out.put("interception", "1");
				}
				
				else if (outcome.equals("FUM")) {
					summary += p1 + " pass " + passtype + " complete to " + p2 + " for " + yds + tackle_str;
					out = this.runFumble(passtype, summary, out); summary = out.get("summary"); 
				}
			}
			
			if (playType.equals("RUSH")) {
				
				out.put("attempt", "1");
				summary += p1 + " rushes " + rushdir + " for " + yds;
			
				if (outcome.equals("CMP")) {
					 summary += tackle_str + ".";
				}
				
				else if (outcome.equals("FUM")) {
					 out = this.runFumble(playType, summary, out); summary = out.get("summary");
				}
			}
			
			if (playType.equals("SCRAMBLE")) {
				
				out.put("attempt", "1");
				summary += p1 + " scrambles for " + yds;
				
				if (outcome.equals("CMP")) {
					 summary += tackle_str + ".";
				}
				
				else if (outcome.equals("FUM")) {
					 out = this.runFumble(playType, summary, out); summary = out.get("summary");
				}
			}
		}
				
		out.put("summary", summary);
		return out;
	}
	
	private String validatePassType(String passtype, String yds) {
		
		int yards = Integer.parseInt(yds);
		if (yards < 20) return passtype.replace("DEEP", "SHORT");
		else if ((yards > 30) & (r.nextDouble() <= 0.1)) return passtype.replace("SHORT", "DEEP");
		
		return passtype;
	}

	public String capYards(String yds) {
		int out_yds = Integer.parseInt(yds);
		if (out_yds > max_yards) out_yds = max_yards;
		return "" + out_yds;
	}
	
	public Map<String,String> runFumble(String play, String summary, Map<String,String> out) {
		
		String fum_message = " FUMBLES, recovered by " + opp_name + ", ";
		summary += fum_message;
		
		if (play.contains("DEEP")) play = "deep_pass";
		else if (play.contains("SHORT")) play = "short_pass";
		else play = "rush";
		
		String fum_idx = "FUM$" + play;
		Map<String,Map<Double,String>> fum_dist = team_dists.get(fum_idx);
		
		String n_yds = capYards(Team.randomSelect(fum_dist.get("dist"))); String yds = addYards(n_yds);
		
		summary += "returned for " + yds + ".";
		out.put("summary", summary); out.put("yards", n_yds); out.put("isTurnover", "1"); out.put("fumble", "1");
		
		return out;
	}
	
	public Map<String,String> kickFG(int yardline) {
		
		String FG_idx = yardlineToYardlineRange(yardline);
		Map<String,Map<Double,String>> FG_dist = team_dists.get(FG_idx);
		
		String isGood = Team.randomSelect(FG_dist.get("FG%"));
		String kicker = Team.randomSelect(FG_dist.get("player"));
		
		Map<String,String> out = new HashMap<String,String>();
		out.put("FG", isGood); out.put("player", kicker);
		
		// build a summary
		String summary = kicker + " FG attempt from " + opp_name + " " + (100 - yardline);
		if (isGood.equals("1")) summary += " is GOOD.";
		else summary += " is NO GOOD.";
		
		out.put("summary", summary);
		
		return out;
	}
	
	public Map<String,String> kickXP() {
		
		int yardline = 85;
		
		String FG_idx = yardlineToYardlineRange(yardline);
		Map<String,Map<Double,String>> FG_dist = team_dists.get(FG_idx);
		
		String isGood = Team.randomSelect(FG_dist.get("FG%"));
		String kicker = Team.randomSelect(FG_dist.get("player"));
		
		Map<String,String> out = new HashMap<String,String>();
		out.put("XP", isGood); out.put("player", kicker);
		
		// build a summary
		String summary = kicker + " EXTRA POINT attempt from " + opp_name + " " + (100 - yardline);
		if (isGood.equals("1")) summary += " is GOOD.";
		else summary += " is NO GOOD.";
		
		out.put("summary", summary);
		
		return out;
	}
	
	public Map<String,String> kickOff() {
		
		Map<String,String> out = new HashMap<String,String>();
		Map<String,Map<Double,String>> kickoff_dist = team_dists.get("KICKOFF");
		
		max_yards = 100 - max_yards; // kickoffs are done by the opposing team, so the field is flipped.
		
		String n_yds = Team.randomSelect(kickoff_dist.get("dist"));
		boolean isTouchback = Integer.parseInt(n_yds) > max_yards;
		
		String yds = addYards(n_yds);
		String kicker = Team.randomSelect(kickoff_dist.get("player"));
		out.put("yards", n_yds); out.put("player", kicker); out.put("isTurnover", "1"); out.put("isTouchback", "0");
		String summary = kicker + " kicks off for " + yds + ".";
		
		if (isTouchback) {
			summary += " TOUCHBACK."; out.put("isTouchback", "1");
		}
		out.put("summary", summary);
		
		return out;
	}
	
	public Map<String,String> punt() {
		 
		Map<String,String> out = new HashMap<String,String>();
		Map<String,Map<Double,String>> punt_dist = team_dists.get("PUNT");
		
		String n_yds = Team.randomSelect(punt_dist.get("dist"));
		boolean isTouchback = Integer.parseInt(n_yds) > max_yards;
		
		String yds = addYards(n_yds);
		String punter = Team.randomSelect(punt_dist.get("player"));
		out.put("yards", n_yds); out.put("player", punter); out.put("isTurnover", "1"); out.put("punt", "1"); out.put("isTouchback", "0");
		String summary = punter + " punts for " + yds + ".";
		
		if (isTouchback) {
			summary += " TOUCHBACK."; out.put("isTouchback", "1");
		}
		out.put("summary", summary);
		
		return out;
	}
}