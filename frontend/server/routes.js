const path = require('path');
const fs = require('fs');
// import fetch from 'node-fetch';

const fetch = require('node-fetch');

// Requirements for DataTables
// const $ = require('jquery');
// require('datatables.net')();
// require('datatables.net-dt')(); 

const baseURL = "http://127.0.0.1:8000"

// local imports
const tools = require("./tools")
const table = require("./scripts/table")

p = "<p>"; p_ = "</p>"; h1 = "<h1>"; h1_ = "</h1>"; h2 = "<h2>"; h2_ = "</h2>"; br = "</br>";
tr = "<tr>"; tr_ = "</tr>"; td = "<td>"; td_ = "</td>"; th = "<th>"; th_ = "</th>"; tab = "   ";
h6 = "<h6>"; h6_ = "</h6>"; // For making text huge (!!)

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

async function playoff_odds(req, res) {

    // Get header
    fileContent = fs.readFileSync(__dirname + "/" + html_filepath + "main_header.html")
    fileContent += h1 + "Playoff Odds" + h1_ + br

    // Load data
    data = await tools.fetch_parse(baseURL + "/pipeline/season_projections.csv")

    // Build table
    html_table = table.simple_table(data);
    fileContent += "<th style=\"vertical-align:top\">" + html_table + th_ + "</table>";

    res.send(fileContent);
}

async function fantasy(req, res) {

    const active_view = req.query.active_view ? req.query.active_view : "Fantasy";
    const active_pos = req.query.active_pos ? req.query.active_pos : "ALL";
    const active_team = req.query.active_team ? req.query.active_team : "ALL";
    
    // Get header
    fileContent = fs.readFileSync(__dirname + "/" + html_filepath + "main_header.html")
    fileContent += h1 + "Fantasy Projections" + h1_ + br

    // Load in fantasy data
    data = await tools.fetch_parse(baseURL + "/pipeline/fantasy_final.csv")

    // Construct the table element
    cols = new Map();
    cols.set("Team_img", "Team"); cols.set("Player_img", "Player"); cols.set("Injury_Status", "Injury Status"); cols.set("Position", "Position");
    if (active_view == "Fantasy") cols.set("PTS", "Fantasy Projection");
    if (active_view == "Passing") {cols.set("Pass YD", "Passing Yards"); cols.set("Pass TD", "Passing Touchdowns"); cols.set("Pass ATT", "Passing Attempts"); cols.set("CMP%","Completion Percentage"); cols.set("Passer RTG", "Passer Rating"); cols.set("INT","Interceptions")}
    if (active_view == "Rushing") {cols.set("Rush YD", "Rushing Yards"); cols.set("Rush TD", "Rushing Touchdowns"); cols.set("Rush ATT", "Rush Attempts"); cols.set("FUM", "Fumbles")}
    if (active_view == "Receiving") {cols.set("Rec YD", "Receiving Yards"); cols.set("Rec TD", "Receiving Touchdowns"); cols.set("TGT", "Targets"); cols.set("REC", "Receptions"); cols.set("FUM", "Fumbles")}
    if (active_view == "Defense") {cols.set("Def YD", "Yards Against"); cols.set("PA", "Points Against"); cols.set("Def TD", "Defensive/Special Teams TDs"); cols.set("SFTY", "Safties"); cols.set("FUM", "Fumbles")}
    if (active_view == "Kicking") {cols.set("FG%", "Field Goal Percentage"); cols.set("XPA", "Extra Points Attempted"); cols.set("XPM", "Extra Points Made"); cols.set("XPA", "Extra Points Attempted"); cols.set("FGM", "FGs Made"); cols.set("FG0_39", "FGs Made, < 40 Yd"); cols.set("FG40_49", "FGs Made, 41 – 50 Yd"); cols.set("FG50plus", "FGs Made, 50+ Yd"); }

    // Create a set of dropdowns
    views = ["Fantasy", "Passing", "Rushing", "Receiving", "Defense", "Kicking"]

    // Build an html dropdown menu for the above columns
    d = `<div class='dropdown2' style="xsborder-collapse: separate; border-spacing:20"><button class='dropbtn2'>▼ ${active_view}</button><div class='dropdown-content2'>`;
    for (curr_view of views) {
        d += `<a href='/home/fantasy?active_view=${curr_view}&active_pos=${active_pos}&active_team=${active_team}'>${curr_view}</a>`
    }
    fileContent += "<table style=\"text-align:left\">" + "<th style=\"vertical-align:top; min-width:200px\">" + h2 + "Select View:" + h2_ + d + "</div></div>"
    
    // Dropdown for filtering on position
    pos = ["ALL", "QB", "RB", "WR", "TE", "K", "D/ST", "FLEX"]
    d = `<div class='dropdown2' style="xsborder-collapse: separate; border-spacing:20"><button class='dropbtn2'>▼ ${active_pos}</button><div class='dropdown-content2'>`;
    for (curr_pos of pos) {
        d += `<a href='/home/fantasy?active_view=${active_view}&active_pos=${curr_pos}&active_team=${active_team}'>${curr_pos}</a>`
    }
    fileContent += h2 + "Filter by </br>Position:" + h2_ + d + "</div></div>"

    // Create a list of individual seraches in the html_table function. For team/position filtering
    pos_regex = active_pos;
    if (active_pos == "FLEX") {pos_regex = "(RB)|(TE)|(WR)"}
    else if (active_pos == "K") {pos_regex = "PK"}

    filters = []
    if (active_pos != "ALL") {filters.push(`.column(3).search("${pos_regex}", true, false)`);}

    // Dropdown for filtering by team
    nfl_teams = ["ALL", "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WSH"];
    d = `<div class='dropdown2' style="xsborder-collapse: separate; border-spacing:20"><button class='dropbtn2'>▼ ${active_team}</button><div class='dropdown-content2'>`;
    for (curr_team of nfl_teams) {
        d += `<a href='/home/fantasy?active_view=${active_view}&active_pos=${active_pos}&active_team=${curr_team}'>${curr_team}</a>`
    }
    fileContent += h2 + "Filter by </br>Team:" + h2_ + d +"</div></div>" + th_;

    if (active_team != "ALL") {filters.push(`.column(0).search("${active_team}", true, false)`);}

    html_table = table.html_table(data, cols, filters);
    fileContent += "<th style=\"vertical-align:top\">" + html_table + th_ + "</table>";

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

    // Get matchup stats
    team1_matchup = await tools.fetch_parse(baseURL + `/java_outputs/matchups/${matchup}/matchup_stats.csv`, "Team", team1); team1_matchup = team1_matchup[0];
    team2_matchup = await tools.fetch_parse(baseURL + `/java_outputs/matchups/${matchup}/matchup_stats.csv`, "Team", team2); team2_matchup = team2_matchup[0];

    fileContent = fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html"));

    // Add team info at the page top
    w1 = Math.round(team1_matchup["Win%"] * 100) / 100 + "%"; w2 = Math.round(team2_matchup["Win%"] * 100) / 100 + "%";
    
    // Mark winner
    name1 = team1_info["Full_Name"]; name2 = team2_info["Full_Name"];
    if (w1 > w2) {name1 += " ✓"}
    else {name2 += " ✓"}

    logo_size = 120
    thw = "<th width=\"33%\">" 
    t = "<table border=\"0\" style=\"text-align: center; vertical-align: middle; width: 1000\">" + tr;
    t += thw + br + h2 + name1 + h2_ + br + h6 + w1 + h6_ + br + br + th_;
    t += th + `<img src="/data/pictures/teams/${team1_info["ID"]}.png" width=${logo_size} height=${logo_size}>` + th_;
    t += th + "<h2><strong>vs</strong></h2>" + th_;
    t += th + `<img src="/data/pictures/teams/${team2_info["ID"]}.png" width=${logo_size} height=${logo_size}>` + th_;
    t += thw + br + h2 + name2 + h2_ + br + h6 + w2 + h6_ + br + br + th_;
    t += "</table>";

    fileContent += t;

    // Send all necessary data to the swarmplot script!
    fileContent += "<script src=\"" + "/frontend/server/scripts/matchup_swarm.js\"" + " data-filepath=" + `\"${filepath}\"` 
    + " data-active_col=" + `\"${active_col}\"` + " data-matchup=" + `\"${matchup}\"`+ ` data-color1=\"${team1_info["Display"]}\"` 
    + ` data-color2=\"${team2_info["Display"]}\"` + "\"></script>"

    // fileContent += p + fs.readFileSync(path.join(__dirname, `../../java_outputs/matchups/${matchup}/summary.html`)) + p_

    // Send file with error handling
    res.send(fileContent);
}

async function defense(req, res) {

    // Unpack defensive team tag
    const def_id = req.query.defense_id ? req.query.defense_id : "NE D/ST"
    const active_col = req.query.active_col ? req.query.active_col : "PTS"
    const team = def_id.split(" ")[0]

    // Get team colors, long name, id for image inclusion
    team_info = await tools.fetch_parse(baseURL + "/data/Team_colors.csv", "Team", team); entry = team_info[0];
    color = entry["Display"]; longname = entry["Full_Name"]; team_id = entry["ID"];

    fileContent = "";
    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html"));

    // Build metadata table
    logo_size = 180;

    th2 = "<th width=33%>"; // 

    t = "<table border=\"0\" style=\"text-align: center; vertical-align: bottom; width: 1000\">";
    t += tr + th2 + `<img src="/data/pictures/teams/${team_id}.png" width=${logo_size} height=${logo_size}>` + th_;
    t += th2 + h2 + longname + " Defense and Special Teams</br>(D/ST)" + h2_ + th_
    t += th2 + th_ + tr_ + "</table>";

    fileContent += t

    // Embed swarmplot script
    filepath = `/java_outputs/fantasy/${team + "+DST"}.csv`;
    fileContent += "<script src=\"" + "/frontend/server/scripts/player_swarm.js\"" + " data-filepath=" 
    + `\"${filepath}\"` + " data-active_col=" + `\"${active_col}\"` + " data-player_id=" + `\"${def_id}\"` +
    ` data-color="${color}"` + ` data-is_DST="true"`+ "\"></script>"

    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_footer.html"));
    res.send(fileContent);
    return;
}

async function player(req, res) {

    const player_id = req.query.id ? req.query.id : "-1";
    const active_col = req.query.active_col ? req.query.active_col : "PTS"

    is_DST = req.query.id.includes("DST")
    if (is_DST) {res.redirect(`/simulations/defense?defense_id=${player_id}&active_col=${active_col}`); return;}

    fileContent = "";
    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html"));

    // Add custom script
    filepath = `/java_outputs/fantasy/${player_id}.csv`;
    dc_filepath = path.join(baseURL, "/pipeline/depth_charts.csv");

    // Attempt to load player data
    dc_response = await fetch(dc_filepath); dc_str = await dc_response.text()
    out = await tools.parse_dc(dc_str, player_id); result = out["filtered_rows"]; entry = result[0];

    // Get defensive stat (D/ST) filepath for D/ST players
    alt_filepath = `/java_outputs/fantasy/${entry["Team"]}+DST.csv`

    // Get display colors, team IDs from csv
    team_info = await tools.fetch_parse(baseURL + "/data/Team_Colors.csv", "Team", entry["Team"]); color = team_info[0]["Display"];

    // Formulate position string i.e. "KR1, RB2". Also get positional booleans
    is_QB=false; is_skill=false; is_K=false; is_DST=false

    pos_str = "";
    for (role of result) {
        pos = role["Position"].toUpperCase();
        pos_str += pos + role["Rank"] + ", ";

        if (pos == "QB") {is_QB=true}
        else if ((pos == "RB") | (pos == "WR") | (pos == "TE")) {is_skill=true}
        else if ((pos == "PK")) {is_K=true}
        else {is_DST=true}
    }
    pos_str = pos_str.substring(0,pos_str.length - 2);
    
    // Draft info: handle the case where a player is undrafted
    draft_str = "UDFA"
    if (entry["Pick"] != -1) {
        draft_str = "RD " + entry["Round"] + ", PICK " + entry["Pick"];
    }

    // Unpack and format player data, with headshot image
    logo_size = 100; player_size = 220;
    t = "<table border=\"0\" style=\"text-align: center; vertical-align: bottom; width: 1000\">";
    t += tr + th + `<img src="/data/pictures/teams/${entry["Team_id"]}.png" width=${logo_size} height=${logo_size} style="vertical-align: top">` 
    + `<img src="/data/pictures/players/${player_id}.png" width=${player_size} height=${player_size * 218/300}>` + th_;
    t += "<th width=\"33%\">" + h1 + entry["Long_Name"] + h1_;

    t += p + "Pos: " + pos_str + tab + "Team: " + entry["Team"] + tab + "YoE: " + entry["YOE"] 
    t += br + "Draft: " + draft_str + br;
    t += "Injury Status: " + entry["Injury_Status"]
    
    is_injured = entry["Injury_Status"] != "H"
    if (is_injured) t += tab + "Return Date: " + entry["Return_Date"];

    t += p_ + th_;
    t += "<th width=\"33%\">" + th_ + tr_;

    fileContent += t;

    // fileContent += br + br
    fileContent += "<script src=\"" + "/frontend/server/scripts/player_swarm.js\"" + " data-filepath=" 
    + `\"${filepath}\" data-alt_filepath="${alt_filepath}"` + " data-active_col=" + `\"${active_col}\"` + " data-player_id=" + `\"${player_id}\"` +
    ` data-color="${color}"`
    + ` data-is_QB="${is_QB}"` + ` data-is_skill="${is_skill}"` + ` data-is_K="${is_K}"` + ` data-is_DST="${is_DST}"`
    + "\"></script>"
    fileContent += fs.readFileSync(path.join(__dirname, html_filepath + "main_footer.html"));

    // fileContent += fs.readFileSync(filepath);
    res.send(fileContent);
}

module.exports = { matchup, serve, gamescript, player, defense, fantasy, playoff_odds };