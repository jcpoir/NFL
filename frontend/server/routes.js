const path = require('path');
const fs = require('fs');
// import fetch from 'node-fetch';
const fetch = require('node-fetch');
const { parse } = require('csv-parse')
const baseURL = "http://127.0.0.1:8000"

// local imports
const tools = require("./tools")

p = "<p>"; p_ = "</p>"; h1 = "<h1>"; h1_ = "</h1>"; h2 = "<h2>"; h2_ = "</h2>"; br = "</br>";
tr = "<tr>"; tr_ = "</tr>"; td = "<td>"; td_ = "</td>"; th = "<th>"; th_ = "</th>"; tab = "   ";

const html_filepath = "../client/html/components/"
const script_filepath = "../client/scripts/"
const content_filepath = "../client/html/pages/"

async function serve(req, res) {

    const page = req.params.page
    const content = content_filepath + page + ".html"

    filepaths = [
        html_filepath + "main_header.html",
        content
    ]

    fileContent = "";
    for (fp of filepaths) {

        fp = path.join(__dirname, fp);
        fileContent += fs.readFileSync(fp, "utf-8")
    }

    // Add additional files for specified filepaths
    if (page == "weekly_predictions") {

        fp = path.join(__dirname, "../../java_outputs/summary.html");
        fileContent += "<p style='font-size: 22px;'>" + fs.readFileSync(fp, "utf-8") + p_;
    }

    res.send(fileContent);
}

async function gamescript(req, res) {

    const matchup = req.query.matchup ? req.query.matchup : "NEvsATL";
    const sim_idx = req.query.sim_idx ? req.query.sim_idx : "1";
    const data_type = req.query.data_type ? req.query.data_type : "pbp"

    filename = "pbp.html"
    if ("pass" === data_type) {filename = "pass.html"}
    else if ("rush" === data_type) {filename = "rush.html"}
    else if ("rec" === data_type) {filename = "rec.html"}
    else if ("fantasy" === data_type) {filename = "fantasy.html"}
    else if ("summary" == data_type) {filename = "summary.html"}

    // define the list of input files, in this case the plain-ish text of interest (gamescript, box score etc.) 
    // plus the predefined header/footer htmls
    
    filepaths = [
        html_filepath + "narrative_header_p1.html",
        -1,
        html_filepath + "narrative_header_p2.html",
        `../../java_outputs/matchups/${matchup}/simulations/${sim_idx}/${filename}`,
        html_filepath + "narrative_footer.html"
    ];

    // Title formatting
    components = matchup.split("vs")
    matchup_str = components[0] + " vs " + components[1]

    fileContent = br + h2 + matchup_str + " #" + sim_idx + h2_;
    for (fp of filepaths) {

        // Add custom URLs in the narrative header (requires qparams from route)
        is_top_bar = fp == -1
        if (is_top_bar) {
            custom_urls = `<a href = "?sim_idx=${sim_idx}&matchup=${matchup}&data_type=summary">Summary</a> >> `
            custom_urls += `<a href = "?sim_idx=${sim_idx}&matchup=${matchup}&data_type=pbp">Play-by-Play</a> >> `
            custom_urls += `<a href = "/simulations/matchup?matchup=${matchup}">Return to Matchup</a>`
            fileContent += custom_urls
            continue;
        }

        fp = path.join(__dirname, fp);

        // catch potential filenotfound errors!
        try {fileContent += fs.readFileSync(fp, "utf-8");}
        catch (err) {err_msg = "404: Not Found"; console.error(err_msg); res.send(err_msg)}
    }

    // Send file with error handling
    res.send(fileContent);
}

async function matchup(req, res) {

    const matchup = req.query.matchup ? req.query.matchup : "NEvsSEA";

    fileContent = fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html")),
    fileContent += p + fs.readFileSync(path.join(__dirname, `../../java_outputs/matchups/${matchup}/summary.html`)) + p_

    // Send file with error handling
    res.send(fileContent);
}

async function player(req, res) {

    const player_id = req.query.id ? req.query.id : "-1";
    const int_pid = parseInt(player_id);
    const str_pid = int_pid.toString();

    fileContent = "";
    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html"));

    // Add custom script
    filepath = `/java_outputs/fantasy/${player_id}.csv`;
    dc_filepath = path.join(baseURL, "/pipeline/depth_charts.csv");

    // Attempt to load player data
    dc_response = await fetch(dc_filepath);
    dc_str = await dc_response.text()

    out = await tools.parse_dc(dc_str, str_pid);

    result = out["filtered_rows"]
    entry = result[0]

    // Formulate position string i.e. "KR1, RB2"
    pos_str = "";
    for (role of result) {
        pos_str += role["Position"].toUpperCase() + role["Rank"] + ", ";
    }
    pos_str = pos_str.substring(0,pos_str.length - 2);
    
    // Draft info: handle the case where a player is undrafted
    draft_str = "UDFA"
    if (entry["Pick"] != -1) {
        draft_str = "RD " + entry["Round"] + ", PICK " + entry["Pick"];
    }

    // Unpack and format player data, with headshot image
    t = "<table border=\"0\" style=\"text-align: center; vertical-align: bottom; width: 1000\">";
    t += tr + th + `<img src="/data/pictures/players/${player_id}.png" width=300 height=218 style="fill:white">` + th_;
    t += "<th width=\"33%\">" + h1 + entry["Long_Name"] + h1_;

    t += p + "Pos: " + pos_str + tab + "Team: " + entry["Team"] + tab + "YoE: " + entry["YOE"] 
    t += br + br + "Draft: " + draft_str + br + br;
    t += "Injury Status: " + entry["Injury_Status"]
    
    is_injured = entry["Injury_Status"] != "H"
    if (is_injured) t += tab + "Return Date: " + entry["Return_Date"];

    t += p_ + th_;
    t += "<th width=\"33%\">" + `<img src="/data/pictures/teams/${entry["Team_id"]}.png" width=218 height=218 style="fill:white">` + th_ + tr_;

    fileContent += t;

    // fileContent += br + br
    fileContent += "<script src=\"" + "/frontend/server/scripts/swarmplot.js\"" + " data-filepath=" + `\"${filepath}\"` + "\"></script>"
    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_footer.html"));

    // fileContent += fs.readFileSync(filepath);
    res.send(fileContent);
}

module.exports = { matchup, serve, gamescript, player };