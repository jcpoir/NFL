const path = require('path');
const fs = require('fs');

p = "<p>"; p_ = "</p>";

const html_filepath = "../client/html/components/"
const content_filepath = "../client/html/pages/"

async function serve(req, res) {

    const page = req.params.page
    const content = content_filepath + page + ".html"

    filepaths = [
        html_filepath + "main_header.html",
        content
    ]

    console.log(page)

    fileContent = "";
    for (fp of filepaths) {

        fp = path.join(__dirname, fp);
        fileContent += fs.readFileSync(fp, "utf-8")
    }

    // Add additional files for specified filepaths
    if (page == "weekly_predictions") {

        fp = path.join(__dirname, "../../java_outputs/summary.html");
        fileContent += p + fs.readFileSync(fp, "utf-8") + p_;
    }

    // Send file with error handling
    res.send(fileContent);
    console.log(fileContent);
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
    const filepaths = [
        html_filepath + "narrative_header.html",
        `../../java_outputs/matchups/${matchup}/simulations/${sim_idx}/${filename}`,
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

module.exports = { serve, gamescript, player };