const path = require('path');
const fs = require('fs');

p = "<p>"; p_ = "</p>"; h1 = "<h1>"; h1_ = "</h1>";

const html_filepath = "../client/html/components/"
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

    // Send file with error handling
    console.log("Serving: " + page);
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

    console.log(filename);

    // define the list of input files, in this case the plain-ish text of interest (gamescript, box score etc.) 
    // plus the predefined header/footer htmls
    
    // Use path.join for cross-platform compatibility
    filepaths = [
        html_filepath + "narrative_header.html",
        `../../java_outputs/matchups/${matchup}/simulations/${sim_idx}/${filename}`,
        html_filepath + "narrative_footer.html"
    ];

    fileContent = "";
    for (fp of filepaths) {

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
    console.log("HERE")

    fileContent = fs.readFileSync(path.join(__dirname, html_filepath + "main_header.html")),
    fileContent += p + fs.readFileSync(path.join(__dirname, `../../java_outputs/matchups/${matchup}/summary.html`)) + p_

    // Send file with error handling
    res.send(fileContent);
}

async function player(req, res) {

    const player_id = req.query.id ? req.query.id : "-1";

    const filepaths = [
        html_filepath + "narrative_header.html",
        `../../java_outputs/fantasy/${player_id}.html`,
        html_filepath + "narrative_footer.html"
    ];

    fileContent = "";
    for (fp of filepaths) {

        fp = path.join(__dirname, fp);
        fileContent += fs.readFileSync(fp, "utf-8");
    }

    // Send file with error handling
    res.send(fileContent);
}

module.exports = { matchup, serve, gamescript, player };