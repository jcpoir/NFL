p = "<p>"; p_ = "</p>"; h1 = "<h1>"; h1_ = "</h1>"; h2 = "<h2>"; h2_ = "</h2>"; br = "</br>";
tr = "<tr>"; tr_ = "</tr>"; td = "<td>"; td_ = "</td>"; th = "<th>"; th_ = "</th>"; tab = "   ";
h6 = "<h6>"; h6_ = "</h6>"; thead = "<thead>"; thead_ = "</thead>"; tbody = "<tbody>"; tbody_ = "</tbody>";

function html_table(data, cols) {
    // Takes an javascript fetch() output as input as well as a Map of columns:display names to display
    // , returns a formatted html table

    // out = `<link rel="stylesheet" href="https://cdn.datatables.net/2.1.8/css/dataTables.dataTables.min.css"></link>`

    out = `<table id="table1" class="display">` + thead + tr;

    // Build the header row
    for ([k,v] of cols) {out += th + v + th_;}
    out += tr_ + thead_;

    // Add rows
    out += tbody;
    for (entry of data) {
        out += tr;
        for ([k,v] of cols) {out += td + entry[k] + td_;}
        out += tr_;
    }
    out += tbody_ + "</table style=\"text-align: center\">";

    out += "<script src=\"https://code.jquery.com/jquery-3.6.0.min.js\"></script>"
    out += `<script src="//cdn.datatables.net/2.1.8/js/dataTables.min.js"></script>`
    out += `<script>
                $(document).ready(function() {
                    $('#table1').DataTable();
                });
            </script>`

    return out;
}

module.exports = { html_table };