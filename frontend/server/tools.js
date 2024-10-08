const { parse } = require('csv-parse');
const fetch = require('node-fetch');

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

async function txt_parse(str, col, value) {
    return new Promise((resolve, reject) => {
        parse(str, {
                columns: true, skip_empty_lines: true, relax_quotes: true,
            }, (err, records) => {
                if (err) {console.error("CSV Parsing Error: ", err) 
                    resolve();}
                
                filtered_rows = records.filter(row => row[col] === value);
                resolve({ filtered_rows: filtered_rows });
            })
    });
};

async function fetch_parse(filepath, col, value) {
    response = await fetch(filepath);
    str = await response.text()

    res = await txt_parse(str, col, value);
    return res["filtered_rows"]
}

function exists(filepath) {
    var http = new XMLHttpRequest();
    http.open('HEAD', url, false);
    http.send();
    return http.status!=404;   
}

module.exports = { fetch_parse, txt_parse, parse_dc, exists };