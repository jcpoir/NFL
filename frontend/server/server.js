/* server.js
*  @author jcpoir
*  My first frontend script (for this project), based on node.js!
*/ 

const express = require('express')
const app = express();
const dirname = "../client/public/"
const hostname = '127.0.0.1';
port = 8000;

app.use(express.static(dirname));

app.get("/", (req,res) => {
    res.sendFile(dirname + "index.html")
});

app.listen(port, () => {
    console.log("Server is running on http://" + hostname + ":" + port)
})