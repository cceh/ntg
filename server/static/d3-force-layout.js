// var d3_attestation_color = d3.scale.category20 ();

var d3_attestation_color = d3.scale.ordinal ()
    .domain (d3.range(20))
    .range (['#ccc', '#1f77b4', '#2ca02c', '#d62728', '#e7ba52', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#dbdb8d', '#9edae5', '#7f7f7f']);



function d3_init () {

    var width  = jQuery ("#svg-wrapper").width ();
    var height = width * 0.667;

    // color = d3.scale.category20 ();

    var color = d3.scale.ordinal ()
        .domain ([0,      1,      2,      3,      4])
        .range  (["#F88", "#FF8", "#88F", "#8F8", "#ccc"]);

    var svg = d3.select ("#svg-wrapper")
        .append ("svg")
        .attr ("width", width)
        .attr ("height", height);

    var force = d3.layout.force()
        .charge(-800)
        .linkDistance (40) // function (link) { return 200 / (link.equal * Math.log (link.common) / link.common); })
        .linkStrength (0.1)
        .size([width, height]);

    d3.json ("/affinity.json", function(error, json) {
        if (error) throw error;

        force
            .nodes(json.nodes)
            .links(json.links)
            .start();

        var link = svg.selectAll(".link")
            .data(json.links)
            .enter().append("line")
            .attr("class", function(d) { return "link sid_" + d.source.id + " tid_" + d.target.id; });

        var node = svg.selectAll(".node")
            .data(json.nodes)
            .enter().append("g")
            .attr ("class", "node")
            .attr ("id",    function(d) { return "n" + d.id; })
            .on("mouseover", function(d) {
                d3.selectAll ("line.link.sid_" + d.id).classed ("hover", true);
                d3.selectAll ("g.node.sid_" + d.id).classed ("hover", true);
                d3.select (this).classed ("hover", true);
            })
            .on("mouseout", function(d) {
                d3.selectAll ("line.link.sid_" + d.id).classed ("hover", false);
                d3.selectAll ("g.node.sid_" + d.id).classed ("hover", false);
                d3.select (this).classed ("hover", false);
            })
            .call(force.drag);

        var foci = [{ x: width / 3, y: height / 2}, { x: width * 2 / 3, y: height / 2}];
        // var foci = [];

        node.append("circle")
            .attr  ("r",     function(d) { return d.radius; })
            .attr  ("class", function(d) { return "node group_" + d.group + " hsnr_" + d.hsnr; })
            .style ("fill",  function(d) { return color (d.group); });

        node.append("text")
            .text(function(d) { return d.hs })

        var links_by_target = _.groupBy (
            _.sortBy (
                json.links, function (o) { return o.target.id; }
            ),
            function (o) { return o.target.id; }
        );

        _.forEach (links_by_target, function (value, key) {
            var targetNode = d3.select ("#n" + key);
            _.forEach (value, function (v) {
                targetNode.classed ("sid_" + v.source.id, true);
            });
        });

        force.on("tick", function(e) {
            var q = d3.geom.quadtree(json.nodes),
                i = 0,
                len = json.nodes.length,
                flen = foci.length,
                k = 0 * e.alpha;

            while (i < len) {
                var n = json.nodes[i];
                if (e.alpha < 0.01) {
                    q.visit (collide (n));
                }
                if (i < flen) {
                    n.x += (foci[i].x - n.x) * k;
                    n.y += (foci[i].y - n.y) * k;
                }
                i++;
            }

            link.attr ("x1", function (d) { return d.source.x; })
                .attr ("y1", function (d) { return d.source.y; })
                .attr ("x2", function (d) { return d.target.x; })
                .attr ("y2", function (d) { return d.target.y; });

            node.attr ("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
        });
    });

    function collide(node) {
        var r = node.radius + 16,
            nx1 = node.x - r,
            nx2 = node.x + r,
            ny1 = node.y - r,
            ny2 = node.y + r;

        return function(quad, x1, y1, x2, y2) {
            if (quad.point && (quad.point !== node)) {
                var dx = node.x - quad.point.x,
                    dy = node.y - quad.point.y,
                    d = Math.sqrt(dx * dx + dy * dy),
                    r = node.radius + quad.point.radius + 4;

                if (d < r) {
                    var l = (d - r) / d * .5;
                    dx *= l;
                    dy *= l;
                    node.x -= dx;
                    node.y -= dy;
                    quad.point.x += dx;
                    quad.point.y += dy;
                }
            }
            return x1 > nx2
                || x2 < nx1
                || y1 > ny2
                || y2 < ny1;
        };
    }

}

function d3_set_attestation (pass_id) {
    d3.json ("/coherence/attestation.json/" + pass_id, function (error, json) {
        if (error) throw error;

        var circles = d3.selectAll ("#svg-wrapper circle.node")
            .style ("fill", function (d) {
                var color = _.get (json.attestations, d.id, 1);
                return d3_attestation_color (color);
            })
    })

    jQuery ("#attestations tr").each (function (i, e) {
        e = jQuery (e);
        e.css ("color", d3_attestation_color (e.attr ("data-labez")));
    });
}
