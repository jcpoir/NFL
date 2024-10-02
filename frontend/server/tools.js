const { parse } = require('csv-parse')

async function parse_dc(dc_str, player_id) {
    return new Promise((resolve, reject) => {
        parse(dc_str, {
                columns: true, skip_empty_lines: true, relax_quotes: true,
            }, (err, records) => {
                if (err) {console.error("CSV Parsing Error: ", err) 
                    resolve();}
                
                filtered_rows = records.filter(row => row["Player_id"] === player_id);
                resolve({ filtered_rows: filtered_rows });
            })
    });
};

function exists(filepath) {
    var http = new XMLHttpRequest();
    http.open('HEAD', url, false);
    http.send();
    return http.status!=404;   
}

module.exports = { parse_dc, exists };