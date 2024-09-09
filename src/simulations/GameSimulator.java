package simulations;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Random;
import java.util.TreeMap;
import java.util.concurrent.ThreadLocalRandom;
import java.time.Duration;
import java.time.Instant;

import teams.Team;
import tools.DataTable;
import tools.Tools;

public class GameSimulator {
	
	static String[] team_names;
	static Random r = new Random();
	int yds; int distance; int yardline; int down; int pos; int kickoff; int time; int quarter; int n_trials;
	Map<String,Integer> playInfo; Map<String,Integer> scores; Team[] teams;
	public Map<String, Map<String, Map<String, Double>>> dists; String leader;
	
	// NOTE: AVG_PLAYS adjusted down to deal w/ timeouts
	static int AVG_PLAYS = 145; static int N_SECONDS = 3600; // average number of plays in an NFL game, per research, and length of a game.
	static int XP_LINE = 15; static int TOUCHBACK_LINE = 25; static int KICKOFF_LINE = 35; static int SAFETY_PUNT_LINE = 20;
	String LOG_FILE = "data.txt";

	static String LF = "\n";
	
	DataTable pass_df; DataTable rush_df; DataTable rec_df; DataTable fantasy_df;
	DataTable pass_df2; DataTable rush_df2; DataTable rec_df2; DataTable fantasy_df2;
	
	// (0) Initialization
	public GameSimulator() throws IOException {
		
		this.dists = GameSimulator.loadData();
		initBoxScores(true); initTextFile();
	}
	
	public GameSimulator(Map<String, Map<String, Map<String, Double>>> dists) throws IOException {
		
		this.dists = dists;
		initBoxScores(true); initTextFile();
	}
	
	// (1) Helper functions
	static double round(double value, int places) {
	    if (places < 0) throw new IllegalArgumentException();

	    BigDecimal bd = BigDecimal.valueOf(value);
	    bd = bd.setScale(places, RoundingMode.HALF_UP);
	    return bd.doubleValue();
	}
	
	static int flip(int x) {
		if (x == 1) return 0;
		return 1;
	}
	
	static void displayTimeElapsed(Instant start) {
		
		Instant end = Instant.now();
		Duration timeElapsed = Duration.between(start, end);
		
		System.out.println("Time elapsed: " + timeElapsed.toMillis() + " ms" + LF);
	}

	static double calcPasserRTG(double cmp, double att, double yds, double td, double intr) {
		
		double m = 2.375;
		double a = (cmp / att - 0.3) * 5; double b = (yds / att - 3) * 0.25;
		double c = (td / att) * 20; double d = 2.375 - (intr / att * 25);
		
		a = Math.min(a, m); b = Math.min(b, m); c = Math.min(c, m); d = Math.min(d, m);
		a = Math.max(a, 0); b = Math.max(b, 0); c = Math.max(c, 0); d = Math.max(d, 0);
		
		double rtg = (a + b + c + d) / 6 * 100;
		
		if (att == 0) {rtg = 0;}
		
		return rtg;
	}
	
	String getWinner() {
		
		int max_score = -1; String winner = "TIE";
		for (Entry<String,Integer> entry : scores.entrySet()) {
			String team = entry.getKey(); int score = entry.getValue();
			
			// Case where a team is leading
			if (score > max_score) {
				max_score = score; winner = team; continue;
			}
			
			// Case where teams are tied
			if (score == max_score) return "TIE";	
		}
		
		return winner;
	}
	
	// (2) Gamescript formatting functions (convert data to pretty game descriptions)
	String getDownDist() {
		
		String down = "" + playInfo.get("down"); String distance = "" + playInfo.get("distance");
		
		if (down.equals("1")) down += "st";
		else if (down.equals("2")) down += "nd";
		else if (down.equals("3")) down += "rd";
		else down += "th";
		
		String field_pos = getFieldPos();
		
		return down + " & " + distance + " at the " + field_pos;
	}
	
	String getFieldPos() {
		
		String out = "";
		
		int possession = playInfo.get("pos"); int yardline = playInfo.get("yardline");
		String team_name = team_names[possession]; String op_name = team_names[flip(possession)];
		
		if (yardline < 50) out += team_name + " " + yardline;
		else if (yardline > 50) out += op_name + " " + (100 - yardline);
		else out += 50;
		
		return out;
	}
	
	String getScoreLine() {
		String t1 = teams[0].getName(); String t2 = teams[1].getName();
		return t1 + " " + scores.get(t1) + " – " + scores.get(t2) + " " + t2;
	}
	
	String getQuarterTime() {
		
		String out; boolean is_OT = quarter > 4;
		
		// Calculate the quarter
		double quarter_len = N_SECONDS / 4.0;
		
		// Calculate the time
		int seconds = time;
		if (is_OT == false) {
			seconds = (int) Math.floor(time % quarter_len);
			if (seconds == 0) seconds = (int) quarter_len;
		}
		int minutes = seconds / 60;
		seconds = seconds % 60;
		
		// Regular Time
		if (is_OT == false) out = String.format("[Q%s %s:%02d]", quarter, minutes, seconds);
		// OT
		else out = String.format("[OT %s:%02d]", minutes, seconds);
		
		return out;
	}
	
	static Map<String,Map<String,Double>> toSummaryStats(List<Map<String,Integer>> scores) {
		
		Map<String,Map<String,Double>> out = new HashMap<String,Map<String,Double>>();
		
		List<String> teams = new ArrayList<String>(scores.get(0).keySet());
		
		String team1 = teams.get(0); String team2 = teams.get(1);
		double w1 = 0.0; double pf1 = 0.0; double pa1 = 0.0; double df1 = 0.0;
		double w2 = 0.0; double pf2 = 0.0; double pa2 = 0.0; double df2 = 0.0; double d = 0.0;
		for (Map<String,Integer> score : scores) {
			int score1 = score.get(team1); int score2 = score.get(team2);
			
			// stats that are updated consistently across cases
			pf1 += score1; pa1 += score2; df1 += (score1 - score2);
			pf2 += score2; pa2 += score1; df2 += (score2 - score1);
			
			// track wins
			if (score1 > score2) w1 ++; else if (score1 < score2) w2 ++; else d += 1;
		}
		
		Map<String,Double> temp; double n = scores.size();
		temp = new HashMap<String,Double>(); temp.put("PF", pf1/n); temp.put("PA", pa1/n); temp.put("DIFF", df1/n);
		temp.put("W", w1); temp.put("L", w2); temp.put("D", d);
		out.put(team1, temp);
		temp = new HashMap<String,Double>(); temp.put("PF", pf2/n); temp.put("PA", pa2/n); temp.put("DIFF", df2/n);
		temp.put("W", w2); temp.put("L", w1); temp.put("D", d);
		out.put(team2, temp);
		
		return out;
	}
	
	void initTextFile() throws IOException {
		/*
		 * Touches/clears the data text file for use in this simulation . . .
		 */
		
		PrintWriter w = new PrintWriter(new FileWriter(LOG_FILE));
		w.write(""); w.close();
	}
	
	void writeToFile(String content) throws IOException {
		/*
		 * Appends the string to an output file "output.txt"
		 */
		
		BufferedWriter w = new BufferedWriter(new FileWriter(LOG_FILE, true));
		w.write(content); w.close();
	}

	void writeToFile(String content, String filepath, String filename) throws IOException {
		/*
		 * Writes a string to a selected file
		 */

		new File(filepath).mkdirs();
		BufferedWriter w = new BufferedWriter(new FileWriter(filepath + "/" + filename, false));
		w.write(content); w.close();
	}

	void appendToFile(String content, String filepath, String filename) throws IOException {
		/*
		 * Appends a string to a selected file
		 */

		 new File(filepath).mkdirs();
		 BufferedWriter w = new BufferedWriter(new FileWriter(filepath + "/" + filename, true));
		 w.write(content); w.close();
	}
	
	String formatStats(Map<String,Map<String,Double>> summary_stats) {
		/*
		 * Formats the win%, PF/PA, wins and losses for teams in a simulated matchup. Outputs, the result as a string.
		 */
		
		String out = "";
		
		List<String> teams = new ArrayList<String>(summary_stats.keySet());
		String team1 = teams.get(0); String team2 = teams.get(1); 
				
		double w1 = summary_stats.get(team1).get("W") / n_trials * 100.0; double w2 = summary_stats.get(team2).get("W") / n_trials * 100.0; 
		out += LF + team1 + " (" + round(w1,2) + "%) vs (" + round(w2,2) + "%) " + team2 + LF + LF;
		
		for (String team: summary_stats.keySet()) {
			out += team + ":" + LF;
			for (String stat: summary_stats.get(team).keySet()) {
				out += stat + ": " + round(summary_stats.get(team).get(stat),2) + LF;
			}
			out += LF;
		}
		
		return out;
	}

	String formatStatLine(Map<String,Map<String,Double>> summary_stats) {

		String out = "";

		List<String> teams = new ArrayList<String>(summary_stats.keySet());
		String team1 = teams.get(0); String team2 = teams.get(1); 

		double w1 = summary_stats.get(team1).get("W") / n_trials * 100.0; double w2 = summary_stats.get(team2).get("W") / n_trials * 100.0; 
		out += team1 + " (" + round(w1,2) + "%) vs (" + round(w2,2) + "%) " + team2;

		return out + LF;
	}
	
	String formatBoxScores() {
		/*
		 * Generates formatted pass/rush/rec stat tables via string manipulation.
		 */

		pass_df = pass_df2.copy(); rush_df = rush_df2.copy(); rec_df = rec_df2.copy();
		
		String out = "";
		
		int N_DECIMALS = 2; double mult = Math.pow(10.0, N_DECIMALS);
		int n = 14; int m = 30; String s = "%-"+n+"s"; Map<String,Map<String,Double>> map; Map<String,Double> row;
		
		// Passer data
		out += "== PASS ==" + LF + LF; 
		String headerFormat = "%-"+m+"s"+s+s+s+s+s+s; String header = String.format(headerFormat, "PASSER", "CMP", "YD", "TD", "INT", "FUM", "RTG"); 
		out += header + LF;
		
		List<Entry<String, Map<String, Double>>> entries = pass_df.sortByField("YD");
		
		String f = "%-"+n+".2f"; String rowFormat = "%-"+m+"s"+s+f+f+f+f+"%-"+n+".2f";
		for (Entry<String, Map<String, Double>> entry : entries) {
			
			row = entry.getValue(); String player = entry.getKey();
			
			// Passer rtg
			double c = row.get("CMP"); double a = row.get("ATT"); double td = row.get("TD"); double yd = row.get("YD"); double intr = row.get("INT");
			double rtg = calcPasserRTG(c, a, yd, td, intr);
			
			double cmp = Math.round(row.get("CMP") * mult) / mult; double att = Math.round(row.get("ATT") * mult) / mult;
			String entry_str = String.format(rowFormat, player, cmp+"/"+att, row.get("YD"), row.get("TD"), row.get("INT"), row.get("FUM"), rtg); 
			
			out += entry_str + LF;
		}
		
		// Rusher data
		out += LF + "== RUSH ==" + LF + LF;
		
		headerFormat = "%-"+m+"s"+s+s+s+s+s+s;
		header = String.format(headerFormat, "RUSHER", "ATT", "YD", "LNG", "TD", "FUM", "AVG"); rowFormat = "%-"+m+"s"+f+f+f+f+f+"%-"+n+".2f";
		out += header + LF;
		
		entries = rush_df.sortByField("YD");
		for (Entry<String, Map<String, Double>> entry : entries) {
			
			row = entry.getValue(); String player = entry.getKey();
			
			double yd = row.get("YD"); double att = row.get("ATT"); double avg = yd/att;
			String entry_str = String.format(rowFormat, player, att, yd, row.get("LNG"), row.get("TD"), row.get("FUM"), avg); 
			
			out += entry_str + LF;
		}
		
		out += LF + "== REC ==" + LF;
		
		headerFormat = "%-"+m+"s"+s+s+s+s+s;
		header = String.format(headerFormat, "RECEIVER", "CMP", "YD", "TD", "LNG", "FUM"); rowFormat = "%-"+m+"s"+s+f+f+f+f;
		out += header + LF;
		
		entries = rec_df.sortByField("YD");
		for (Entry<String, Map<String, Double>> entry : entries) {
			
			row = entry.getValue(); String player = entry.getKey();
			
			double cmp = Math.round(row.get("REC") * mult) / mult; double att = Math.round(row.get("TGT") * mult) / mult;
			String entry_str = String.format(rowFormat, player, cmp+"/"+att, row.get("YD"), row.get("TD"), row.get("LNG"), row.get("FUM")); 
			
			out += entry_str + LF;
		}
		
		out += LF;
		return out;
	}
	
	String formatFantasyPoints() {
		/*
		 * Formats fantasy datatable into a viewable string, which is logged and displayed to the console
		 */
		
		String out = "";
		
		out += "== FANTASY POINTS ==" + LF + LF;
		int n = 14; int m = 30; String s = "%-"+n+"s"; String f = "%-"+n+".2f";
		
		List<Entry<String, Map<String, Double>>> entries = fantasy_df.sortByField("PTS");
		String rowFormat = "%-"+m+"s"+f;
		
		for (Entry<String, Map<String, Double>> entry : entries) {
			String ID = entry.getKey(); double fpoints = entry.getValue().get("PTS");
			
			out += String.format(rowFormat, ID, fpoints) + LF;
		}
		
		return out;
	}
	
	// (3) Updating, tracking the game state
	void updatePlayInfo() {
		// updates play info map using yds, distance, etc. fields
		playInfo.put("down", down); playInfo.put("distance", distance); playInfo.put("yardline", yardline); 
		playInfo.put("pos", pos); playInfo.put("kickoff", kickoff);
	}
	
	void manageQuarters() {
		
		// check if end of Q1
		int q2_time = N_SECONDS / 4 * 3;
		if (time <= q2_time & quarter == 1) {time = q2_time; quarter = 2; return;}
		
		// check if end of Q3
		int q4_time = N_SECONDS / 4;
		if (time <= q4_time & quarter == 3) {time = q4_time; quarter = 4; return;}
	}
	
	void resetPlayInfo() {
		playInfo.put("down", 1); playInfo.put("distance", 10); playInfo.put("yardline", 100 - KICKOFF_LINE); 
		playInfo.put("pos", 0); playInfo.put("kickoff", 1);
	}
	
	void addScore(String team, int points) {
		scores.put(team, scores.get(team) + points);
	}
	
	double parseResult(String field, Map<String,String> result) {
		
		double db = 0.0; String str = result.get(field); if (str != null) {db = Double.parseDouble(str);}
		return db;
	}
	
	Map<String,Double> resultToBSInput(Map<String,String> result) {
		
		Map<String,Double> out = new HashMap<String,Double>();
		
		// Unpack, transform, add fields
		out.put("YD", parseResult("yards", result));
		out.put("TD", parseResult("isTD", result));
		out.put("INT", parseResult("interception", result));
		out.put("SACK", parseResult("sack", result));
		out.put("FUM", parseResult("fumble", result));
		out.put("ATT", parseResult("attempt", result));
		out.put("CMP", parseResult("complete", result));
		
		return out;
	}
	
	void initBoxScores(boolean reset_agg) {
		pass_df = new DataTable(); rush_df = new DataTable(); rec_df = new DataTable();
		
		pass_df.col("CMP"); pass_df.col("ATT"); pass_df.col("YD"); pass_df.col("TD"); pass_df.col("INT"); pass_df.col("SACK"); pass_df.col("FUM");
		rec_df.col("REC", "CMP"); rec_df.col("TGT", "ATT"); rec_df.col("YD"); rec_df.col("LNG", "YD", "max"); rec_df.col("TD"); rec_df.col("FUM");
		rush_df.col("ATT");  rush_df.col("YD"); rush_df.col("LNG", "YD", "max"); rush_df.col("TD"); rush_df.col("FUM");

		if (reset_agg) {pass_df2 = pass_df.copy(); rec_df2 = rec_df.copy(); rush_df2 = rush_df.copy();}
	}

	void initBoxScores() {
		initBoxScores(false);
	}
	
	void addToBox(Map<String,String> result, String team) {
		
		Map<String,Double> stats = resultToBSInput(result);
		
		String playType = result.get("playType"); if (playType == null) return;
		// String teamString = String.format("%-5s ", "[" + team + "]");
		String teamString = "[" + team + "]";
				
		if ("RUSH".equals(playType) | "SCRAMBLE".equals(playType)) {
			String ID = teamString + result.get("player1");
			rush_df.put(ID, stats); rush_df2.put(ID, stats);
		}
		
		else if ("PASS".equals(playType)) {
			String ID1 = teamString + result.get("player1"); String ID2 = teamString + result.get("player2");
			pass_df.put(ID1, stats); rec_df.put(ID2, stats); pass_df2.put(ID1, stats); rec_df2.put(ID2, stats);
		}
		
		// no longer counting sacks, as they lead to misleading QB rushing stats
		else if ("SACK".equals(playType)) {
//			String ID = teamString + result.get("player1");
//			rush_df.put(ID, stats);
			return; 
		}
		
	}
	
	void divBoxByN(double n, String[] exclude_cols) {
		pass_df2.divBy(n, exclude_cols); rush_df2.divBy(n, exclude_cols); rec_df2.divBy(n, exclude_cols);
	}
	
	void calcFantasyPoints() {
		// Calculate fantasy points based on box scores
		
		fantasy_df = new DataTable();
		fantasy_df.col("PTS");
		
		// Here we define the point value of each kind of event . . .
		double PASS_YD = 0.04; double PASS_TD = 4; double INT = -2; double FUM = -2;
		double RUSH_YD = 0.1; double RUSH_TD = 6; double PPR = 1;
		double REC_TD = 6; double REC_YD = 0.1;
		
		double fpoints; Map<String,Double> out;
		
		// Calculate passing points
		for (String player : pass_df.keySet()) {
			Map<String,Double> info = pass_df.get(player);
			
			double yds = info.get("YD"); double ints = info.get("INT"); double tds = info.get("TD"); double fums = info.get("FUM");
			fpoints = yds * PASS_YD + ints * INT + tds * PASS_TD + fums * FUM;
			
			out = new HashMap<>(); out.put("PTS", fpoints);
			
			fantasy_df.put(player, out);
		}
		
		// Calculate rushing points
		for (String player : rush_df.keySet()) {
			Map<String,Double> info = rush_df.get(player);
			
			double yds = info.get("YD"); double tds = info.get("TD"); double fums = info.get("FUM");
			fpoints = yds * RUSH_YD + tds * RUSH_TD + fums * FUM;

			out = new HashMap<>(); out.put("PTS", fpoints);
			
			fantasy_df.put(player, out);
		}
		
		// Calculate recieving points
		for (String player : rec_df.keySet()) {
			Map<String,Double> info = rec_df.get(player);
			
			double yds = info.get("YD"); double rec = info.get("REC"); double tds = info.get("TD"); double fums = info.get("FUM");
			fpoints = yds * REC_YD + rec * PPR + tds * REC_TD + fums * FUM;
			
			out = new HashMap<>(); out.put("PTS", fpoints);
			
			fantasy_df.put(player, out);
		}
	}

	class GameResult {
		Map<String,Integer> scores; String pbp;
		public GameResult(Map<String,Integer> scores, String pbp) {
			this.scores = scores; this.pbp = pbp;
		}
	}
	
	// (4) Simulation
	GameResult runGame(Team team1, Team team2, boolean OT, boolean verbose, boolean add_to_box, boolean to_txt) {

		// Aggregate play-by-play as a string
		String pbp = "START OF GAME";
		
		resetPlayInfo();
		
		teams = new Team[] {team1, team2}; boolean is_overtime = false; leader = "TIE";
		
		int avg_playTime = N_SECONDS / AVG_PLAYS; int playTime_low = avg_playTime - 15; int playTime_high = avg_playTime + 15;
		time = N_SECONDS;
		
		// Initialize the scoring dictionary
		scores = new TreeMap<String,Integer>();
		for (Team team : teams) {scores.put(team.getName(), 0);}
		
		int plays = 0; quarter = 1; // simulate two halves of football
		while (true) {
			
			// Switch teams by drive
			pos = playInfo.get("pos");
			Team team = teams[pos]; Team opp_team = teams[flip(pos)]; // opp_team is used exclusively for kickoffs
			
			String scoreline_txt = LF + LF + getScoreLine() + LF;
			if (to_txt) pbp = pbp + scoreline_txt + LF;
			
			// Simulate one drive!
			while (true) {
				
				plays++;
				
				// Check who's winning
				leader = getWinner();
				
				// Manage halves, quarters
				manageQuarters();
				if ((time <= N_SECONDS / 2) & quarter < 3) break; // HALFTIME
				else if ((time <= 0) & (is_overtime == false)) break; // GAME END
				else if ((is_overtime == true) & ("TIE".equals(leader) == false)) break; // GAME END (OT)
				
				// Update playclock
				String quarterTime = getQuarterTime();
				
				// if overtime, add time. Otherwise, subtract
				double time_delta = ThreadLocalRandom.current().nextInt(playTime_low, playTime_high); // determine play duration and subtract
				if (is_overtime == false) time -= time_delta;
				if (is_overtime == true) time += time_delta;
				
				kickoff = playInfo.get("kickoff");

				// Update game scripts with down & distance
				String dnd = getDownDist();
				if (verbose) System.out.println(dnd); // HERE
				if (to_txt) pbp += dnd + LF;
				
				// special case where a kickoff is required
				boolean isKickOff = (kickoff == 1);
				if (isKickOff) {
					
					Map<String,String> result = opp_team.kickOff();

					String kickoff_str = quarterTime + " " + result.get("summary");
					if (verbose) System.out.println(kickoff_str);
					if (to_txt) pbp += kickoff_str + LF;
				
					yds = Integer.parseInt(result.get("yards")); down = 1; distance = 10;
					yardline = playInfo.get("yardline") - yds; kickoff = 0;
					
					boolean isTouchback = result.get("isTouchback").equals("1"); 
					if (isTouchback) yardline = TOUCHBACK_LINE;
			
					updatePlayInfo();
					continue;
				}

				// (!!) call on the team object to run a play given the game state
				Map<String,String> result = team.runPlay(playInfo);

				// update game scripts with play description
				String play_txt = quarterTime + " " + result.get("summary");
				if (verbose) System.out.println(play_txt); // HERE
				if (to_txt) pbp += play_txt + LF;
								
				boolean isFG = (result.keySet().contains("FG")); 
				
				// special case where a field goal has been kicked
				if (isFG) {
					
					boolean isFG_good = (result.get("FG").equals("1"));
					
					if (isFG_good) {
						
						String drive_result = "FIELD GOAL: GOOD";
						if (verbose) System.out.print(drive_result); // HERE
						if (to_txt) pbp += drive_result;

						pos = flip(pos); down = 1; distance = 10; yardline = 100 - KICKOFF_LINE; kickoff = 1;
						updatePlayInfo(); addScore(team.getName(), 3); break;
					}
					
					else {
						String drive_result = "FIELD GOAL: NO GOOD";
						if (verbose) System.out.print(drive_result); // HERE
						if (to_txt) pbp += drive_result;

						pos = flip(pos); down = 1; distance = 10; yardline = 25;
						updatePlayInfo(); break;
					}
				}
				
				// Unpack results
				yds = Integer.parseInt(result.get("yards")); boolean isTurnover = "1".equals(result.get("isTurnover")); 
				
				// Update game state
				distance = playInfo.get("distance") - yds;
				yardline = playInfo.get("yardline") + yds;
				down = playInfo.get("down") + 1; pos = playInfo.get("pos");
				
				boolean isTD = yardline >= 100; if (isTD) {result.put("isTD", "1");} boolean isTOD = down > 4; boolean isFirstDown = distance <= 0;
				boolean isPunt = (result.keySet().contains("punt")); boolean isSafety = yardline < 0;
				
				// Aggregate box scores
				if(add_to_box) addToBox(result, team.team_name);
				
				if (isPunt) {
					String isTouchback = result.get("isTouchback");
					pos = flip(pos); down = 1; distance = 10; yardline = 100 - yardline;
					
					if (isTouchback.equals("1")) yardline = TOUCHBACK_LINE;
					updatePlayInfo(); 
					
					String drive_result = "PUNT";
					if (verbose) System.out.print(drive_result); // HERE
					if (to_txt) pbp += drive_result;

					break;
				}

				// case of turnover
				if (isTurnover) {

					pos = flip(pos); down = 1; distance = 10; yardline = 100 - yardline;
					updatePlayInfo();

					// case of touchback
					boolean isTouchback = yardline <= 0; boolean isDefTouchdown = yardline >= 100;

					String drive_result = "TURNOVER";
					if (isTouchback) {yardline = TOUCHBACK_LINE;}
					else if (isDefTouchdown) {
						
						pos = flip(pos); updatePlayInfo();
						Map<String,String> XP_result = team.kickXP();
						String XP_str = XP_result.get("summary");
						if (verbose) System.out.println(XP_str);
						if (to_txt) pbp += XP_str + LF;

						String isXP_good = XP_result.get("XP");
						if (isXP_good.equals("1")) addScore(team.getName(), 1);

						drive_result = "DEFENSIVE TOUCHDOWN";
						
					}
					
					if (verbose) System.out.print(drive_result); // HERE
					if (to_txt) pbp += drive_result;

					updatePlayInfo(); break;
				}
				
				else if (isTD) {
					pos = flip(pos); down = 1; distance = 10; yardline = 100 - KICKOFF_LINE; kickoff = 1;
					updatePlayInfo(); addScore(team.getName(), 6); 
					
					// Attempt and extra point (XP)
					Map<String,String> XP_result = team.kickXP();
					String XP_str = XP_result.get("summary");
					if (verbose) System.out.println(XP_str);
					if (to_txt) pbp += XP_str + LF;

					String isXP_good = XP_result.get("XP");
					if (isXP_good.equals("1")) addScore(team.getName(), 1);
					
					String drive_result = "TOUCHDOWN";
					if (verbose) System.out.print(drive_result); // HERE
					if (to_txt) pbp += drive_result;

					break;
				}
				
				// case of first down
				else if (isFirstDown) {
					down = 1; distance = 10;
				}
				
				else if (isTOD) {
					String drive_result = "TURNOVER ON DOWNS";
					if (verbose) System.out.print(drive_result); // HERE
					if (to_txt) pbp += drive_result;

					pos = flip(pos); down = 1; distance = 10; yardline = 100 - yardline;
					updatePlayInfo(); break;
				}	
				
				else if (isSafety) {
					String drive_result = "SAFETY";
					if (verbose) System.out.print(drive_result); // HERE
					if (to_txt) pbp += drive_result;

					pos = flip(pos); down = 1; distance = 10; yardline = 100 - SAFETY_PUNT_LINE;
					kickoff = 1; updatePlayInfo();
					addScore(teams[pos].getName(), 2); break;
				}
				
				updatePlayInfo(); // update the game state with the results of the play (if drive-ending conditions aren't met)
			}
			
			if (time <= 0) {
				if (OT == false) break; // GAME END
				
				if ((OT == true) & "TIE".equals(leader) == false) break;
				
				// CASE WHERE overtime is necessary. Reset the game state.
				is_overtime = true;
				pos = 1; down = 1; distance = 10; yardline = 100 - KICKOFF_LINE; kickoff = 1; updatePlayInfo();
				time = 0;
				quarter = 5;
			}
			
			if ((time <= N_SECONDS / 2) & quarter < 3) { // HALFTIME
				
				String halftime_str = LF + "HALFTIME";
				if (verbose) System.out.print(halftime_str);  // stop play at halftime and give possession to the other team to start 2H (HERE)
				if (to_txt) pbp += halftime_str;

				pos = 1; down = 1; distance = 10; yardline = 100 - KICKOFF_LINE; kickoff = 1; updatePlayInfo();
				time = N_SECONDS / 2;
				quarter = 3;
			}
			
			leader = getWinner();
			boolean is_OT_over = (is_overtime) & ("TIE".equals(leader) == false);
			if (is_OT_over) break; // GAME END (OT)
		}
		
		// Standardize output spacing and add end of game tag
		pbp = pbp.strip() + LF + LF;
		pbp += "END OF GAME";

		// Finish with final score, returning the result to simulateMatchup()
		String fin_score_string = LF + LF + "FINAL SCORE: " + getScoreLine();
		if (verbose) System.out.println(fin_score_string); // HERE
		if (to_txt) pbp += fin_score_string;
		
		GameResult out = new GameResult(scores, pbp);
		return out;
	}
	
	static Map<String, Map<String, Map<String, Double>>> loadData() throws IOException {

		// (1) Data Load
		String path = "data/";  // NOTE: change the source directory here!!
		
		String[] SpecialFilepaths = {path + "SPEC1.csv", path + "SPEC2.csv", path + "SPEC3.csv"};
		return Team.readDists(path + "DEF.csv", path + "OFF.csv", SpecialFilepaths);
	}
	
	void saveData(Map<String, Map<String, Map<String, Double>>> dists) {
		this.dists = dists;
	}
	
	// putting it all together; simulating a game!
	class MatchupResult {
		
		String boxScore = null; String summary = null; 
		Map<String,Map<String,Double>> matchup_stats; String winner;
		
		MatchupResult(Map<String,Map<String,Double>> matchup_stats, String winner) {
			this.matchup_stats = matchup_stats; this.winner = winner;
		}
	}
	
	MatchupResult simulateMatchup(String teamName1, String teamName2, int n_trials, boolean avg_stats, boolean OT, boolean verbose, boolean show_result, boolean add_to_box, boolean to_txt) throws IOException {
		// NOTE: added add_to_box paramaeter so that in the playoffs we don't aggregate fantasy stats anymore (causes bias)

		initBoxScores(true);
		
		// (0) Get execution time
		Instant start = Instant.now();
		this.n_trials = n_trials;
		
		// (2) Team Initialization
		Map<String,String> attributes = new HashMap<String,String>();
		team_names = new String[] {teamName1, teamName2};
		attributes.put("team", team_names[0]); attributes.put("opponent", team_names[1]); attributes.put("year", "2023"); Team team1 = new Team(attributes, dists);
		attributes.put("team", team_names[1]); attributes.put("opponent", team_names[0]); attributes.put("year", "2023"); Team team2 = new Team(attributes, dists);
		
		// (3) Play Running
		Map<String,Integer> PlayInfo = new HashMap<String,Integer>();
		PlayInfo.put("down", 1); PlayInfo.put("distance",10); PlayInfo.put("yardline",100 - KICKOFF_LINE); PlayInfo.put("pos",0);PlayInfo.put("kickoff", 1);

		// (4) Playing a Drive
		playInfo = PlayInfo;
		
		String matchup = teamName1 + "vs" + teamName2;
		String base_filepath = "java_outputs/matchups/" + matchup + "/";
		// track the game results in an arraylist
		List<Map<String,Integer>> scores_list = new ArrayList<Map<String,Integer>>();
		for (int i = 0; i < n_trials; i++) {
			GameResult game_result = runGame(team1, team2, OT, verbose, add_to_box, to_txt);
			Map<String,Integer> score = game_result.scores; String pbp = game_result.pbp;
			scores_list.add(score);
			
			// Record all game results
			if (to_txt) {
				String filepath = base_filepath + "/simulations/" + (i+1);

				calcFantasyPoints(); 

				// Record game data in the {matchup}/{game_ID} folder.
				writeToFile(pbp, filepath, "pbp.html");
				pass_df.to_csv(filepath + "/pass.html"); rush_df.to_csv(filepath + "/rush.html");
				rec_df.to_csv(filepath + "/rec.html"); fantasy_df.to_csv(filepath + "/fantasy.html");

				// Record fantasy data in fantasy/{player_id}.csv
				Tools.record_fantasy(fantasy_df, i, matchup, score);

				initBoxScores();
			}
		}

		Tools.to_csv(scores_list, base_filepath, "scores", true);
		
		// (5) Finalize tabular data, report results
		Map<String,Map<String,Double>> matchup_stats = toSummaryStats(scores_list);
		if (avg_stats) divBoxByN((double) n_trials, new String[] {"LNG"});
		
		// Get final fantasy totals (for the summary)
		pass_df = pass_df2; rush_df = rush_df2; rec_df = rec_df2; calcFantasyPoints(); 
		
		// Here is where logging, console printing of aggregated tabular data happens!
		String text = formatStats(matchup_stats); String statline = formatStatLine(matchup_stats);
		appendToFile(statline, "java_outputs/", "summary.txt");

		text += formatBoxScores() + formatFantasyPoints(); 
		
		if (show_result) {
			writeToFile(text); System.out.println(text);
			displayTimeElapsed(start);
		}	

		if (to_txt) {
			writeToFile(text, base_filepath, "summary.txt");
		}

		return new MatchupResult(matchup_stats, leader); // stats are sent to SeasonSimulator (if applicable)
	}
	
	MatchupResult simulateMatchup(String teamName1, String teamName2, int n_trials) throws IOException {
		
		return simulateMatchup(teamName1, teamName2, n_trials, true, false, false, false, false, true);
	}
	
	public static void main(String[] args) throws IOException, InterruptedException {
		
		Map<String, Map<String, Map<String, Double>>> dists = GameSimulator.loadData();
		GameSimulator sim = new GameSimulator(dists);

		Tools.clear_dir("java_outputs/fantasy");
		
		int n_trials = 1000; boolean avg_stats = true; boolean OT = false; boolean verbose = true; boolean show_result = true; boolean add_to_box = true; boolean to_txt = true;
		sim.simulateMatchup("ATL", "PIT", n_trials, avg_stats, OT, verbose, show_result, add_to_box, to_txt);
	}
}