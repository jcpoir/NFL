const width = 1000;
const height = 500;
const x_margin = 50; const y_margin = 50;
const x_range = [x_margin, width - x_margin]
const y_range = [y_margin, height - y_margin]

const circle_r = 3; const circle_r2 = 10;

let svg = d3
    .select("body")
    .append("svg")
    .attr("height", height)
    .attr("width", width);

// Ensure your CSV data path is correct
d3.csv("12483.csv").then((data) => {

    data = data.slice(0, 2000)

    // Scales for position (y for delta, cx is randomized or based on some other attribute)
    let xScale = d3
        .scaleLinear()
        .domain(d3.extent(data, (d) => +d["PTS"]))
        .range(x_range);
    
    let background = svg.append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", 1000)
        .attr("height", 500)
        .attr("fill", "#161616")
        .attr("stroke", "white")
        .attr("stroke-width", "3")

    // Append the x-axis
    let x_axis = d3.axisBottom(xScale);

    var axis = svg.append("g")
        .attr("transform", `translate(0, 400)`) // Position at the bottom of the svg
        .call(x_axis)

    // add mean line
    mean = 18.1
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
        .attr("x", mean_x + 10)
        .attr("y", 110)
        .style("fill", "white")
        .text(`x̅ = ${mean}`)
        .style("font-size", "12")

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

    // Add title, x-label
    svg.append("text")
        .attr("class", "title")
        .attr("text-anchor", "middle")
        .attr("x", width / 2)
        .attr("y", 75)
        .style("fill", "white")
        .text("Total Fantasy Points: Matthew Stafford")
        .style("font-size", "23")

    svg.append("text")
        .attr("class", "x label")
        .attr("text-anchor", "middle")
        .attr("x", width / 2)
        .attr("y", 450)
        .style("fill", "white")
        .text("FPTS")

    // Append circles
    let circles = svg.selectAll(".circ")
        .data(data)
        .enter()
        .append("circle")
        .attr("class", "circ")
        .attr("stroke", "black")
        .attr("fill", "dodgerBlue") // Added fill for better visibility
        .attr("fill-opacity", 0.9)
        .attr("r", circle_r) // Circle radius
        .attr("cx", (d) => xScale(d.PTS))

    // Add effects, tooltips
    let div = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("visibility", "hidden")
        .style("opacity", 0);

    circles.on("mouseover", function (event, d) {

        // circle behavior
        d3.select(this).transition()
            .duration(100)
            .attr("fill", "white")
            .attr("r", circle_r2);

        // tooltip
        div.transition()
            .duration(100)
            .style("opacity", 1)
            .style("visibility", "visible");
        
        rounded_pts = Math.round(d.PTS * 100) / 100;
        box_txt = "FPTS: " + rounded_pts + "\nARI: " + d.ARI + "\nLAR: " + d.LAR

        div.html(box_txt)
            .style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 10) + "px");
    })
    .on("mouseout", function (event, d) {

        d3.select(this).transition()
            .duration(100)
            .attr("fill", "dodgerBlue")
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
            window.location = "/simulations/gamescript?matchup=" + d.matchup + "&sim_idx=" + d.game_ID
    });
    
    // Begin collision forcing (to form swarm plot from linear)
    let simulation = d3.forceSimulation(data)

        .force("x", d3.forceX((d) => {
            return xScale(d.PTS);
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
        console.log("start alpha decay");
        }, 0); // start decay x ms