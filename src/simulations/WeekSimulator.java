package simulations;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import tools.Tools;

public class WeekSimulator extends GameSimulator{

    List<String[]> matchups;

    public WeekSimulator() throws IOException {super();}

    public List<String[]> loadMatchups(int week, String filepath) throws NumberFormatException, IOException {
        // Loads matchups for a given week of the season

        BufferedReader br = new BufferedReader(new FileReader(filepath));
        matchups = new ArrayList<>();

        String line;
        while ((line = br.readLine()) != null) {

            String[] components = line.split(",");
            boolean isFirst = "Week".equals(components[0]);
            if (isFirst) continue;
            
            // Load in only the current week
            int curr_week = Integer.parseInt(components[0]);
            if (curr_week < week) continue;
            if (curr_week > week) break;

            String[] matchup = new String[] {components[1], components[2]};
            matchups.add(matchup);
        }
        return matchups;
    }

    public void simWeek(int week) throws IOException {

        matchups = loadMatchups(week, "data/NFL_2024_Matchups.csv");

        int n_trials = 10000; boolean avg_stats = true; boolean OT = false; boolean verbose = false; boolean show_result = true; boolean add_to_box = true; boolean to_txt = true;

        for (String[] matchup : matchups) {
            System.out.println(matchup[0] + " vs " + matchup[1]);
            simulateMatchup(matchup[0], matchup[1], n_trials, avg_stats, OT, verbose, show_result, add_to_box, to_txt);
        }
    }

    public static void main(String[] args) throws IOException, InterruptedException {

        Tools.clear_dir("java_outputs");
        WeekSimulator s = new WeekSimulator();
        s.simWeek(2);
    }
}