package tools;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

public class Tools {

    static String LF = "\n"; static String csv = ".csv";
    static Runtime r = Runtime.getRuntime();
    
    public static void to_csv(List<Map<String,Integer>> data, String filepath, String filename) throws IOException {
        // Outputs the given data to a .csv format. Used to store scores.

        new File(filepath).mkdirs(); // create directories if they don't exist alread!

        BufferedWriter w = new BufferedWriter(new FileWriter(filepath + "/" + filename + ".csv", true));
        int i = 0;
        for (Map<String,Integer> row : data) {

            boolean is_first = i == 0;
            if (is_first) {

                String line = "ID";
                for (String k : row.keySet()) {
                    line += "," + k;
                }
                w.write(line + LF);
            }

            String line = String.valueOf(i+1);
            for (Integer v : row.values()) {
                line += "," + String.valueOf(v);
            }
            w.write(line + LF);

            i++;
        }
        w.close();
    }

    public static void to_csv(List<Map<String,Integer>> data, String filepath, String filename, boolean to_clear) throws IOException {
        
        // Clear output file by opening the file outside of append mode!
        if (to_clear) {
            FileWriter f_dummy = new FileWriter(filepath + "/" + filename + ".csv", false); f_dummy.close();
        }

        to_csv(data, filepath, filename);
    }

    public static boolean fileExists(String filepath) {
        File f = new File(filepath);
        return f.exists();
    }

    public static void clear_dir(String filepath) throws IOException {
        if (Tools.fileExists(filepath)) r.exec("rm -r " + filepath);
    }

    public static void record_fantasy(DataTable fantasy_df, int game_ID, Map<String,Integer> scores) throws IOException {
        // Used to aggregate fantasy stats for players

        String filepath = "java_outputs/fantasy";

        // Ensure that fantasy directory exists. If not, create.
        new File(filepath).mkdirs();

        Map<String,Map<String,Double>> data = fantasy_df.getMap();

        // Team IDs
        String header_line = "game_ID,";
        String line = String.valueOf(game_ID) + ",";
        
        // Team Scores
        for (Entry<String,Integer> team_score : scores.entrySet()) {
            header_line += team_score.getKey() + ","; line += String.valueOf(team_score.getValue()) + ",";
        }
        
        // Player IDs, Fantasy Points
        for (String player_id : data.keySet()) {
            String curr_line = line;

            Map<String,Double> vals = data.get(player_id);
            curr_line += String.valueOf(player_id);

            for (double v : vals.values()) {
                curr_line += "," + String.valueOf(v);
            }

            // Check if file exists
            String filename = String.valueOf(player_id) + csv;
            File f = new File(filepath + "/" + filename);
            boolean isFile = f.isFile();

            // Write outputs to a file.
            BufferedWriter w = new BufferedWriter(new FileWriter(filepath + "/" + filename, true));

            if (!isFile) {
                String curr_header = header_line;
                curr_header += "player_ID";
                for (String k : vals.keySet()) {
                    curr_header += "," + k;
                }
                w.write(curr_header + LF); 
            }
            w.write(curr_line + LF);
            w.close();
        }
    }
}
