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
    components = matchup.split("vs"); team1 = components[0]; team2 = components[1];

    const active_col = req.query.active_col ? req.query.active_col : "PTS DIFF";
    const filepath = `/java_outputs/matchups/${matchup}/scores.csv`

    // Get display colors, team IDs from csv
    team1_info = await tools.fetch_parse(baseURL + "/data/Team_Colors.csv", "Team", team1); team1_info = team1_info[0];
    team2_info = await tools.fetch_parse(baseURL + "/data/Team_Colors.csv", "Team", team2); team2_info = team2_info[0];

    fileContent = fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html"));

    // Add team info at the page top
    logo_size = 220
    th25 = "<th width=\"25%\">" 
    t = "<table border=\"0\" style=\"text-align: center; vertical-align: bottom; width: 1000\">" + tr + th25;
    t += `<img src="/data/pictures/teams/${team1_info["ID"]}.png" width=${logo_size} height=${logo_size}>` 
    t += h2 + team1_info["Full_Name"] + h2_ + th_ + th25 + th_ + th25 + h2_ + th_ + th25;
    t += `<img src="/data/pictures/teams/${team2_info["ID"]}.png" width=${logo_size} height=${logo_size}>`;
    t += h2 + team2_info["Full_Name"] + th_ + tr_;

    fileContent += t;

    // Send all necessary data to the swarmplot script!
    fileContent += "<script src=\"" + "/frontend/server/scripts/matchup_swarm.js\"" + " data-filepath=" + `\"${filepath}\"` 
    + " data-active_col=" + `\"${active_col}\"` + " data-matchup=" + `\"${matchup}\"`+ ` data-color1=\"${team1_info["Display"]}\"` 
    + ` data-color2=\"${team2_info["Display"]}\"` + "\"></script>"

    // fileContent += p + fs.readFileSync(path.join(__dirname, `../../java_outputs/matchups/${matchup}/summary.html`)) + p_

    // Send file with error handling
    res.send(fileContent);
}

async function player(req, res) {

    const player_id = req.query.id ? req.query.id : "-1";
    const active_col = req.query.active_col ? req.query.active_col : "PTS"

    // Define a mapping between column names, formal names for player stat categories
    const cm = new Map();
    cm.set("PTS", "Fantasy Points"); cm.set("Pass YD", "Passing Yards"); cm.set("Pass TD", "Passing Touchdowns");
    cm.set("Rush YD", "Rushing Yards"); cm.set("Rush TD", "Rushing Touchdowns"); cm.set("Rec YD", "Receiving Yards");
    cm.set("Rec TD", "Receiving Touchdowns"); cm.set("INT", "Interceptions"); cm.set("FUM", "Fumbles");

    long_name = cm.get(active_col)

    fileContent = "";
    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html"));

    // Add custom script
    filepath = `/java_outputs/fantasy/${player_id}.csv`;
    dc_filepath = path.join(baseURL, "/pipeline/depth_charts.csv");

    // Attempt to load player data
    dc_response = await fetch(dc_filepath);
    dc_str = await dc_response.text()
    out = await tools.parse_dc(dc_str, player_id);
    result = out["filtered_rows"]; entry = result[0];

    // Get display colors, team IDs from csv
    team_info = await tools.fetch_parse(baseURL + "/data/Team_Colors.csv", "Team", entry["Team"]); color = team_info[0]["Display"];

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
    t += tr + th + `<img src="/data/pictures/teams/${entry["Team_id"]}.png" width=218 height=218 style="fill:white">` 
    + `<img src="/data/pictures/players/${player_id}.png" width=300 height=218 style="fill:white">` + th_;
    t += "<th width=\"33%\">" + h1 + entry["Long_Name"] + h1_;

    t += p + "Pos: " + pos_str + tab + "Team: " + entry["Team"] + tab + "YoE: " + entry["YOE"] 
    t += br + br + "Draft: " + draft_str + br + br;
    t += "Injury Status: " + entry["Injury_Status"]
    
    is_injured = entry["Injury_Status"] != "H"
    if (is_injured) t += tab + "Return Date: " + entry["Return_Date"];

    t += p_ + th_;
    t += "<th width=\"33%\">" + th_ + tr_;

    fileContent += t;

    // fileContent += br + br
    fileContent += "<script src=\"" + "/frontend/server/scripts/player_swarm.js\"" + " data-filepath=" 
    + `\"${filepath}\"` + " data-active_col=" + `\"${active_col}\"` + " data-player_id=" + `\"${player_id}\"` +
    ` data-color="${color}"` + "\"></script>"
    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_footer.html"));

    // fileContent += fs.readFileSync(filepath);
    res.send(fileContent);
}

module.exports = { matchup, serve, gamescript, player };