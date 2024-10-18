/* server.js
*  @author jcpoir
*  My first frontend script (for this project), based on node.js!
*/ 

const express = require('express')
const path = require('path');

const app = express();
const hostname = '127.0.0.1';
port = 8000;
console.log("__dirname: " + __dirname)

dirname = path.join(__dirname, '../../')

// Imports
const routes = require('./routes')

// Ensure that the default file type is plain text
app.use(express.static(dirname, {
    setHeaders: (res, filepath) => {
        res.removeHeader('Content-Type');
        res.setHeader('Content-Type', 'text/plain')
    }
}));

app.get("/", (req, res) => {
    res.redirect("/about");
});

app.get("/simulations/matchup", routes.matchup);

app.get("/home/fantasy", routes.fantasy);
app.get("/home/:page", routes.serve);

app.get("/simulations/gamescript", routes.gamescript);

app.get("/simulations/player", routes.player);
app.get("/simulations/defense", routes.defense);

app.listen(port, () => {
    console.log("Server is running on http://" + hostname + ":" + port)
})