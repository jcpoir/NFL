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

app.use(express.static(dirname));

app.get("/", (req,res) => {res.sendFile(dirname + "/frontend/client/index.html")});

app.get("/gamescript", routes.gamescript);

app.get("/player", routes.player);

app.listen(port, () => {
    console.log("Server is running on http://" + hostname + ":" + port)
})