package tools;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

public class DataTable {
	
	Map<String,String[]> cols = new HashMap<String,String[]>();
	public Map<String,Map<String,Double>> table = new HashMap<String,Map<String,Double>>();
	
	public DataTable () {}
	
	public void col(String name, String source, String agg_type) {this.cols.put(name, new String[] {source, agg_type});}
	public void col(String name, String source) {this.cols.put(name, new String[] {source, "add"});}
	public void col(String name) {this.cols.put(name, new String[] {name, "add"});}
	
	public Map<String, Map<String, Double>> getMap() {return table;}

	public Map<String,Double> new_row () {
		Map<String,Double> out = new HashMap<String,Double>();
		for (String col : cols.keySet()) out.put(col, 0.0);
		return out;
	}
	
	void reverse(String[] array) {
        int left = 0;
        int right = array.length - 1;
        while (left < right) {
            String temp = array[left];
            array[left] = array[right];
            array[right] = temp;
            left++;
            right--;
        }
	}
	
	public List<Entry<String, Map<String, Double>>> sortByField(String field) {
		
		List<Entry<String,Map<String,Double>>> out = new ArrayList<Entry<String,Map<String,Double>>>();
		
		Entry<String,Map<String,Double>> temp;
		for (Entry<String,Map<String,Double>> row : table.entrySet()) {out.add(row);}
		
		// Sort by entries
		int _len = out.size();
		for (int i = 0; i < _len-1; i++) {
			for (int j = i+1; j < _len; j++) {
				if (out.get(i).getValue().get(field) < out.get(j).getValue().get(field)) {
					temp = out.get(i); out.set(i, out.get(j)); out.set(j, temp);
				}
			}
		}
		
		return out;
	}
	
	public List<Entry<String, Map<String, Double>>> sortByFields(String[] fields) {
		
		reverse(fields);
		
		List<Entry<String,Map<String,Double>>> out = new ArrayList<Entry<String,Map<String,Double>>>();
		
		Entry<String,Map<String,Double>> temp;
		for (Entry<String,Map<String,Double>> row : table.entrySet()) {out.add(row);}
		
		// Sort by fields, from least important (last) to most (first)
		for (String field : fields) {
			
			// Sort by entries
			int _len = out.size();
			for (int i = 0; i < _len-1; i++) {
				for (int j = i+1; j < _len; j++) {
					if (out.get(i).getValue().get(field) < out.get(j).getValue().get(field)) {
						temp = out.get(i); out.set(i, out.get(j)); out.set(j, temp);
					}
				}
			}
		}
		
		return out;
	}
	
	public Set<String> keySet() {
		
		Set<String> out = new HashSet<>();
		
		for (String key: table.keySet()) {
			out.add(key);
		}
		
		return out;
	}
	
	// Takes a playerID and a map of play information
	// uses predefined column information to aggregate accordingly
	public void put(String ID, Map<String,Double> info) {
		
		// (1) attempt to fetch data from the given key. If not present, define a new map
		Map<String,Double> row = table.get(ID);
		if (row == null) row = new_row();
		
		// (2) iterate through the columns, looking to see if the input contains the required info
		for (String col : cols.keySet()) {
			
			String[] c = cols.get(col); String source = c[0]; String agg_type = c[1];
			
			// if the source is missing, skip operation
			boolean isMissing = info.keySet().contains(source) == false; if (isMissing) continue;
			
			// otherwise, apply the relevant aggregation operation
			double val = info.get(source);
			if (agg_type.equals("add")) row.put(col, row.get(col) + info.get(source));
			if (agg_type.equals("max")) row.put(col, Math.max(row.get(col), info.get(source)));
		}
		
		table.put(ID, row);
	}
	
	public void increment(String ID, String col) {
		// Adds a value of one to the named column
		
		Map<String,Double> info = new HashMap<>();
		info.put(col, 1.0);
		
		put(ID, info);
	}
	
	public Map<String,Double> get(String ID) {
		return table.get(ID);
	}
	
	public void divBy(double n, String[] exclude_cols) {
		
		Set<String> exclude_col_set = new HashSet<String> (Arrays.asList(exclude_cols));
		
		for (String k1 : table.keySet()) {
			Map<String,Double> row = table.get(k1);
			Map<String,Double> new_row = new HashMap<String,Double>();
			
			for (String k2 : row.keySet()) {
				
				double val = row.get(k2);
				if (!exclude_col_set.contains(k2)) val = val / n;

				new_row.put(k2, val);
			}
			
			table.put(k1, new_row);
		}
		
	}
	
	public void divBy(double n) {
		divBy(n, new String[] {});
	}
	
	public void print() {
		for (String ID: this.table.keySet()) {
			System.out.print(ID + ": ");
			System.out.println(this.table.get(ID));
		}
	}
	
	public static void main(String args[]) {
		
		System.out.println("== DataTable Test ==\n");
		
		DataTable df = new DataTable();
		df.col("Player"); df.col("Yds"); df.col("TD"); df.col("INT", "add"); df.col("SACK");
		df.col("FUM"); df.col("LNG", "Yds", "max");
		
		String ID = "17-P.Rivers";
		
		Map<String,Double> info = new HashMap<String,Double>();
		info.put("Yds", 11.0);
		
		df.put(ID, info);
		df.put(ID, info);
		
		ID = "12-T.Brady";
		
		df.put(ID, info);
		df.put(ID, info);
		df.put(ID, info);
		
		df.print();
		
		System.out.println(df.sortByField("Yds"));
	}
	
}
