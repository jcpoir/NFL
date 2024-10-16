// swarmplot.js
// @author jcpoir
// Generates a swarmplot using d3's force algorithm. Optimized for
// the matchup stat use case

// unpack arguments
const scriptTag = document.querySelector('script[src*="matchup_swarm.js"]');
const filepath = scriptTag.getAttribute('data-filepath');
const active_col = scriptTag.getAttribute('data-active_col')
const matchup_str = scriptTag.getAttribute("data-matchup")

c1 = scriptTag.getAttribute("data-color1"); c2 = scriptTag.getAttribute("data-color2");

components = matchup_str.split("vs");
const team1 = components[0]; const team2 = components[1];
pretty_matchup = `${team1} vs ${team2}`

// Define a mapping between column names, formal names for stat categories
const cm = new Map();
cm.set("PTS DIFF", "Win/Loss Margin"); cm.set("TOTAL PTS", "Scoring Total");
cm.set(team1, `Points Scored, ${team1}`); cm.set(team2, `Points Scored, ${team2}`);

const long_name = cm.get(active_col);

// Build an html dropdown menu for the above columns
d = `<div class='dropdown'><button class='dropbtn'>▼ ${long_name}</button><div class='dropdown-content'>`;
for (const [col_name, long_name] of cm.entries()) {
    d += `<a href='/simulations/matchup?matchup=${matchup_str}&active_col=${col_name}'>${long_name}</a>`
}
d += "</div></div>"

const width = 1000;
const height = 500;
const x_margin = 50; const y_margin = 50;
const x_range = [x_margin, width - x_margin]
const y_range = [y_margin, height - y_margin]

const circle_r = 3; const circle_r2 = 10;
const text_top = 10; const text_left = 10;

const average = array => array.reduce((a, b) => a + b) / array.length;

function exists(fp) {
    var http = new XMLHttpRequest();
    http.open('HEAD', fp, false);
    http.send();
    return http.status!=404;   
}

let svg = d3
    .select("body")
    .append("svg")
    .attr("height", height)
    .attr("width", width);

let background = svg.append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", 1000)
    .attr("height", 500)
    .attr("fill", "#101010")
    .attr("stroke", "gray")
    .attr("stroke-width", "0.5")

if (!exists(filepath)) {
    svg.append("text")
    .attr("class", "title")
    .attr("text-anchor", "middle")
    .attr("x", width / 2)
    .attr("y", 250)
    .style("fill", "white")
    .text(`No Data Available`)
    .style("font-size", "23")
    console.log("404: Player Data Not Found")
}

else {

    d3.csv(filepath).then((data) => {

        function calc_greater_than(x) {

            total = 0.0; n = 0.0;
            for (row of data) {
                if (row[active_col] >= x) total += 1;
                n += 1.0;
            }
            ans = total / n;

            return ans;
        }

        // Find the sample mean
        total = 0; n = 0;
        for (row of data) {
            total += parseFloat(row[active_col])
            n += 1;
        }
        mean = Math.round(total/n * 100) / 100;

        console.log(mean)

        data = data.slice(0, 1000)

        // Unpack column names by inspecting the first row of the table
        let cols = data.length > 0 ? Object.keys(data[0]) : [];

        console.log(cols)

        // Scales for position (y for delta, cx is randomized or based on some other attribute)
        let xScale = d3
            .scaleLinear()
            .range(x_range);

        if (active_col == "PTS DIFF") {xScale.domain([-60, 60]);}
        else {xScale.domain(d3.extent(data, (d) => +d[active_col]))}

        let xScaleInv = xScale.invert();

        // Initialize mouse-controlled line
        x_start = xScale(25)
        let drag_line = svg.append("line")
            .attr("class", "drag_line")
            .attr("x1",x_start)
            .attr("y1",100)
            .attr("x2",x_start)
            .attr("y2",400)
            .attr("stroke", "white")
            .attr("stroke-width", "2")
            .style("visibility", "hidden")   

        let drag_text = svg.append("text")
            .attr("class", "mean-line text")
            .attr("text-anchor", "start")
            .attr("x", x_start + 10)
            .attr("y", 110)
            .style("fill", "white")
            .text(`x = ${null}`)
            .style("font-size", "16") 
            .style("visibility", "hidden")

        let d_bottom_text_r = svg.append("text")
            .attr("class", "mean-line text")
            .attr("text-anchor", "start")
            .attr("x", x_start + 10)
            .attr("y", 390)
            .style("fill", "white")
            .text(`x = ${null}`)
            .style("font-size", "12") 
            .style("visibility", "hidden")

        let d_bottom_text_l = svg.append("text")
            .attr("class", "mean-line text")
            .attr("text-anchor", "end")
            .attr("x", x_start + 10)
            .attr("y", 390)
            .style("fill", "white")
            .text(`x = ${null}`)
            .style("font-size", "12") 
            .style("visibility", "hidden")

        console.log("c1: " + c1 + "\nc2: " + c2);
        fade_dist = 10

        // Define color gradients
        const activeScale = d3.scaleLinear()
            .domain([-1000, -fade_dist, 0, fade_dist, 1000])
            .range([c1, c1, "white", c2, c2])

        const defaultScale = d3.scaleLinear()
            .domain(d3.extent(data, (d) => +d[active_col]))
            .range(["red", "yellow"])

        // Append circles
        let circles = svg.selectAll(".circ")
            .data(data)
            .enter()
            .append("circle")
            .attr("class", "circ")
            .attr("stroke", "black")
            .attr("stroke-width", 0.25)
            .attr("r", circle_r) // Circle radius
            .attr("cx", (d) => xScale(d[active_col]))
            .attr("fill", d => defaultScale(d[active_col]));

        if (active_col == "PTS DIFF") {circles.attr("fill", d => activeScale(d[active_col]))}


        // Append the x-axis
        let x_axis = d3.axisBottom(xScale);

        var axis = svg.append("g")
            .attr("transform", `translate(0, 400)`) // Position at the bottom of the svg
            .call(x_axis)

        // mean_line.moveToFront()
        // ml_text.moveToFront()
        
        // customize horizontal axis
        axis.select(".domain")
            .attr("stroke", "white")
            .attr("stroke-width", "2")
        axis.selectAll(".tick")
            .attr("stroke", "white")
            .attr("fill", "white")
            .attr("stroke-width", "1")
            .attr("font-family","andale mono")
            .attr("font-size","12")
        axis.selectAll(".tick line")
            .attr("stroke", "white")
            .attr("fill", "white")
            .attr("stroke-width", "1")
            .attr("font-family","andale mono")
            .attr("font-size","12")
        axis.select(".domain")
            .attr("fill", "dark gray")

        svg.append("text")
            .attr("class", "x label")
            .attr("text-anchor", "middle")
            .attr("x", width / 2)
            .attr("y", 450)
            .style("fill", "white")
            .text(active_col)
        
        // Hyper-annoying jumping dropdown
        let dropdown = d3.select("body").append("div")
            .attr("class", "dropdown")
            .style("visibility", "visible")

        dropdown.html(d)
            .style("left", "300px")
            .style("top", "-448px")

        // Add effects, tooltips
        let div = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("visibility", "hidden")
            .style("opacity", 0);

        // add mean line
        mean_x = xScale(mean)
        let mean_line = svg.append("line")
            .attr("x1",mean_x)
            .attr("y1",100)
            .attr("x2",mean_x)
            .attr("y2",400)
            .attr("stroke", "white")
            .attr("stroke-width", "2")

        let ml_text = svg.append("text")
            .attr("class", "mean-line text")
            .attr("text-anchor", "start")
            .attr("x", mean_x + text_left)
            .attr("y", 110)
            .style("fill", "white")
            .style("font-size", "16")
            .style("font-weight", "bold")

        if (active_col == "PTS DIFF") {
            if (mean < 0) {ml_text.text(team1 + " -" + Math.abs(mean));}
            else if (mean > 0) {ml_text.text(team2 + " -" + Math.abs(mean));}
            else {ml_text.text("EVEN")}
        }
        else {ml_text.text(`x̅ = ${mean}`)}

        // Add title, x-label
        svg.append("text")
            .attr("class", "title")
            .attr("text-anchor", "left")
            .attr("x", 165)
            .attr("y", 75)
            .style("fill", "white")
            .text(`Projected xxxxxxxxxxxxxxxxxxxxx.: ${pretty_matchup}`)
            .style("font-size", "23")

        circles.on("mouseover", function (event, d) {

            // circle behavior
            d3.select(this).transition()
                .duration(100)
                .attr("r", circle_r2);

            // tooltip
            div.transition()
                .duration(100)
                .style("opacity", 1)
                .style("visibility", "visible");
            
            rounded_pts = Math.round(d[active_col] * 100) / 100;
            box_txt = active_col + ": " + rounded_pts + `\n${team1} ` + d[team1] + " - " + d[team2] + ` ${team2}` + "\n#" + d.ID

            div.html(box_txt)
                .style("left", (event.pageX + text_left) + "px")
                .style("top", (event.pageY - text_top) + "px");
        })
        .on("mouseout", function (event, d) {

            d3.select(this).transition()
                .duration(100)
                .attr("r", circle_r);

            // tooltip
            div.transition()
                .duration(100)
                .style("opacity", 0)
                .style("visibility", "hidden");

        })

        .on("click", function (event, d) {
            d3.select(this).transition()
                .duration(0)
                .attr("fill", "red")
                window.location = "/simulations/gamescript?matchup=" + matchup_str + "&sim_idx=" + d.ID
        })
        
        svg.on("mousemove", function (event, d) {
            const [x] = d3.pointer(event);

            drag_line.transition()
                .duration(0)
                .attr("x1", x)
                .attr("x2", x)
                .style("visibility", "visible");

            x_pts = Math.round(xScale.invert(x) * 100) / 100
            drag_text.transition()
                .duration(0)
                .attr("x", x + text_left)
                .text(`x = ${x_pts}`)
                .style("visibility", "visible");

            r = (calc_greater_than(x_pts) * 100).toFixed(2)
            d_bottom_text_r.transition()
                .duration(0)
                .attr("x", x + text_left)
                .text(`${r}%`)
                .style("visibility", "visible");

            d_bottom_text_l.transition()
                .duration(0)
                .attr("x", x - text_left)
                .text(`${(100 - r).toFixed(2)}%`)
                .style("visibility", "visible");

            mean_line.transition()
                .duration(0);
        });
        
        // Begin collision forcing (to form swarm plot from linear)
        let simulation = d3.forceSimulation(data)

            .force("x", d3.forceX((d) => {
                return xScale(d[active_col]);
                }).strength(0.35))

            .force("y", d3.forceY((d) => {
                return 250;
                }).strength(0.04))
            
            .force("collide", d3.forceCollide((d) => {
                return circle_r;
                }).strength(1.3))
            
            .alphaDecay(0.008)
            .alpha(1)
            .on("tick", tick);
        });

        function tick() {
            d3.selectAll(".circ")
                .attr("cx", (d) => d.x)
                .attr("cy", (d) => d.y);
            }
        
        let init_decay = setTimeout(function () {
            }, 0); // start decay x ms
}