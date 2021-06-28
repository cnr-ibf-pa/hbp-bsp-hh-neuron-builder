const SHOW_FADED = 0.2;
const SHOW_CHECK = 0.8;
const SHOW_HOVER = 1.0;

var plotData = {}
var num = 0;

var minibatch_size = 5;
var n_plots = 0;

// refresh the plot with new opacities
function refreshPlot(plot_id) {

    // restyle the plot with new opacities
    Plotly.restyle(plot_id, {
        opacity: plotData[plot_id]["opacities"]
    })
    Plotly.redraw(plot_id);

    // set the opacities of the legend's labels
    Plotly.d3.select('div#' + plot_id + ' g.legend').selectAll('g.traces').each(function (item, i) {
        Plotly.d3.select(this).style('opacity', 1);
    })
}


// refresh the plot considering the voltage correction
function plotVoltageCorrection(plot_id, correction) {
    var correctedSegments = plotData[plot_id]["segments"];
    correctedSegments.forEach(segment => {
        y = segment["y"];
        for (var i = 0; i < y.length; i++) {
            y[i] += correction;
        }
    });
    refreshPlot(plot_id);
}

// plot all cells contained in cells
function plotCells(cells, isUploaded, id) {
    if (cells.length > 5) {
        loadMore(cells, isUploaded, id);
    } else {
        $("#load-more-button").remove()
        sendParallelRequests(plotMinibatch(cells, isUploaded, id));
    }
}

async function sendParallelRequests(promises) {
    writeMessage("wmd-first", "Loading traces");
    writeMessage("wmd-second", "Please wait...");
    openMessageDiv("wait-message-div", "main-e-st-div");
    await Promise.all(promises);
    closeMessageDiv("wait-message-div", "main-e-st-div");
    writeMessage("wmd-first", "");
    writeMessage("wmd-second", "");
}

function loadMore(cells, isUploaded, id) {
    n_plots = 1;
    var promises = plotMinibatch(cells.slice((n_plots - 1) * minibatch_size,  n_plots * minibatch_size), isUploaded, id);
    $("#charts").append("<button id='load-more-button' class='btn btn-outline-primary w-25 mt-3'>Load more</button>");
    $("#load-more-button").click(() => {
        n_plots++;
        sendParallelRequests(plotMinibatch(cells.slice((n_plots - 1) * minibatch_size,  n_plots * minibatch_size), isUploaded, id));
        if (cells.length > n_plots * minibatch_size) {
            $("#charts").append($("#load-more-button"));
        } else {
            $("#load-more-button").remove();
        }
        
    });
    sendParallelRequests(promises)
}


function createCellHeader(cell_name, cell_id, cellHeaderIds) {
        
    var cell_container;
    if (cellHeaderIds.includes(cell_id)) {
        cell_container = $('<div id="cell-' + cell_id + '"class=text-center" style="display: none"/>');
    } else {
        cell_container = $('<div id="cell-' + cell_id + '"class="text-center"/>');
    }) 
    
    cell_container.append(' \
            <div class="row bg-light-grey mx-auto py-2"> \
                <div class="col-12 my-2"> \
                    <a> \
                        Cell: ' + cell_name + ' <br>Cell id: ' + cell_id + ' \
                    </a> \
                </div> \
                <div class="col-12" my-2> \
                    <a class="cell_selall clickable mx-2">Select all traces</a> \
                    <a class="cell_dselall clickable mx-2">Deselect all traces</a> \
                    <a class="cell_invsel clickable mx-2">Invert selection</a> \
                </div> \
            </div>'
    );
    cell_container.find('.cell_selall').click(() => {
        $('#cell-' + cell_id).find('.selall').click();
    });
    cell_container.find('.cell_dselall').click(() => {
        $('#cell-' + cell_id).find('.dselall').click();
    });
    cell_container.find('.cell_invsel').click(() => {
        $('#cell-' + cell_id).find('.invsel').click();
    });
    return cell_container;
}

function createCellPlotBox(id, container, currentPlotData, xLabel, yLabel, cellInfo, contributors) {

    var infobox = $('<div/>', {
        'id': 'info_' + id,
        'class': 'row px-4',
    }).appendTo(container);

    var inputbox = $('<div/>', {
        'id': 'input_' + id,
        'class': 'input_box',
    }).appendTo(container);

    var plot_id = 'plot_' + id;
    $('<div/>', {
        'id': plot_id,
        'class': 'table-responsive',
    }).appendTo(container);

    plot(plot_id, 'input_' + id, {
        data: currentPlotData,
        x_label: xLabel,
        y_label: yLabel,
        plot_width: container.width()
    });

    // create the infobox
    infobox.append(' \
        <div class="col-12 mb-2"> \
            <a> \
                Cell properties: ' + cellInfo.join(' > ') + '   [' + contributors + '] \
            </a> \
        </div> \
        <div class="col-12 mb-2"> \
            <a class="selall clickable mx-2">Select all</a> \
            <a class="dselall clickable mx-2">Deselect all</a> \
            <a class="invsel clickable mx-2">Invert selection</a> \
        </div> \
    ');
    var settingsMenu = inputbox.append(createSettingsMenu());

    //add listener to the voltage correction input
    $('#vcorr_' + num).on("change", function() {
        plotVoltageCorrection(plot_id, parseFloat($(this).val()))
    });

    // menus is defined in show_traces.js
    menus.push($(settingsMenu));

    // Select every trace
    infobox.find('.selall').click(() => { 
        plotData[plot_id]["opacities"].fill(SHOW_CHECK);
        inputbox.find('input').prop('checked', true);
        refreshPlot(plot_id);
    });

    // Deselect all traces
    infobox.find('.dselall').click(() => {
        plotData[plot_id]["opacities"].fill(SHOW_FADED);
        inputbox.find('input').prop('checked', false);
        refreshPlot(plot_id);
    });

    // Invert the selection
    infobox.find('.invsel').click(() => {
        var opacities = plotData[plot_id]["opacities"];
        for (var i = 0; i < opacities.length; i++) {
            opacities[i] = opacities[i] == SHOW_FADED ? SHOW_CHECK : SHOW_FADED;
            var checkbox = inputbox.find('input')[i];
            checkbox.checked = !checkbox.checked;
        }
        refreshPlot(plot_id);
    });
}

function plotMinibatch(cells, isUploaded, id) {
    var promises = [];
    var cellHeaderIds = [];
    for (var i = 0; i < cells.length; i++) {
        var cell = null;
        var cell_name = null;
        var files = [];
        var divId = "#charts";
        if (isUploaded) {
            var cell_info = cells[i].split("____");
            cell = cell_info[5]
            cell_name = cell_info.slice(0, 6).join(" > ");
            divId += "_upload_" + id;
            files = files.concat(cells[i]);
        } else {
            cell = cells[i];
            cell_name = contributor + ' > ' + specie + ' > ' + structure + ' > ' + region + ' > ' + type + ' > ' + etype + ' > ' + cell;
            files = files.concat(Object.values(json['Contributors'][contributor][specie][structure][region][type][etype][cell]));
        }
      
        var cellHeader = createCellHeader(cell_name, cell, cellHeaderIds)
        cellHeader.addClass("mt-4");
        cellHeader.append('<div id="charts-' + cell + '"></div>');
        $(divId).append(cellHeader);
        files.forEach(file => {
            var fileName = file.split('.')[0];
            $('#charts-' + cell).append('<div id="' + fileName + '" class="border border-primary rounded-3 my-4 mx-1 p-2"></div>');
            var container = $("#" + fileName);
            promises.push(new Promise((resolve, reject) => {
                $.getJSON('/efelg/get_data/' + fileName, data => {
                    var dict = JSON.parse(data);
                    var currentPlotData = [];
                    Object.keys(dict["traces"]).forEach(label => {
                        y = dict["traces"][label];
                        x = Array
                            .apply(null, {length: y.length})
                            .map(Number.call, Number)
                            .map(x => x * 1000 / dict['disp_sampling_rate']);
                        currentPlotData.push({
                            x: x,
                            y: y,
                            label: label
                        });
                    });
                    currentPlotData = currentPlotData.sort((dict1, dict2) => parseFloat(dict1["label"]) - parseFloat(dict2["label"]));
                    currentPlotData.forEach(d => d["label"] += " " + dict["stimulus_unit"]);
                    var new_keys = {
                        "species": "animal_species",
                        "area": "brain_structure",
                        "region": "cell_soma_location",
                        "type": "type",
                        "etype": "etype",
                        "name": "cell_id",
                        "sample": "filename",
                    }
                    var cellinfo = [];
                    for (key of Object.keys(new_keys)) {
                        if (new_keys[key] in dict) {
                            cellinfo.push(dict[new_keys[key]]);
                        } else {
                            cellinfo.push(dict[key]);
                        }
                    }
                    ccc = ""
                    if (dict.contributors_affiliations) {
                        ccc = "Data contributors: " + dict.contributors_affiliations;
                    } else if (dict.contributors.message) {
                        ccc = dict.contributors.message;
                    } else {
                        ccc = "N/A";
                    }
                   // createCellPlotBox(fileName, container, currentPlotData, "ms", dict["voltage_unit"], cellinfo, dict['contributors']['message']);
                    createCellPlotBox(fileName, container, currentPlotData, "ms", dict["voltage_unit"], cellinfo, ccc);
                    resolve();
                });
            }));
        });
    }
    return promises
}


/*
Plot the data using Plotly. Requires a dictionary containing the following keys:
- data: array of dictionaries containing the following keys: x, y, label
- x_label: label of x axis
- x_label: label of y axis
- plot_width: the width of the plot
*/
function plot(plot_id, input_id, data) {

    function manageLegend() {

        var legend =  Plotly.d3.select('div#' + plot_id + ' g.legend');
        
        // save the opacity value before the mousehover
        function savePrevious(item) {
            var i = item[0].trace.index;
            previousOpacity = opacities[i];
            opacities[i] = SHOW_HOVER;
            refreshPlot(plot_id);
        }
    
        // restore the opacity value after the mouseleave
        function restorePrevious(item) {
            var i = item[0].trace.index;
            opacities[i] = previousOpacity;
            refreshPlot(plot_id);
        }
    
        // toggle the opacity value of the specified trace
        function onclick(item) {
            var name = item[0]["trace"]["name"];
            var checkbox = $("#" + input_id + "_segment" + name.substring(0, name.lastIndexOf(" ")).replace(".", ""));
            if (previousOpacity == SHOW_FADED) {
                checkbox.prop('checked', true);
                previousOpacity = SHOW_CHECK;
            } else {
                checkbox.prop('checked', false);
                previousOpacity = SHOW_FADED;
            }
        }        
    
        // bind the events for each legend item
       legend.selectAll('g.traces rect').each(function () {
            Plotly.d3.select(this).on('click', onclick);
            Plotly.d3.select(this).on('mouseenter', savePrevious);
            Plotly.d3.select(this).on('mouseleave', restorePrevious);
        })

    }

    plotData[plot_id] = {};
    plotData[plot_id]["segments"] = [];
    plotData[plot_id]["opacities"] = [];
    var currentPlotData = plotData[plot_id]["segments"];
    var opacities = plotData[plot_id]["opacities"];
    var previousOpacity = null;
    
    $("<form id='" + input_id + "-form'></form>").appendTo($("#" + input_id));
    var form = $("#" + input_id + "-form");
    data["data"].forEach(segment => {
        var label = segment["label"];
        form.append("<input id='" + input_id + "_segment" + label.substring(0, label.lastIndexOf(" ")).replace(".", "") +
                    "' type='checkbox' name='" + label + "' style='display: none'>");
            currentPlotData.push({
                x: segment["x"],
                y: segment["y"],
                name: segment["label"],
                mode: 'lines',
                hoverinfo: 'none',
                opacity: SHOW_FADED
            });
        opacities.push(SHOW_FADED);
    });
    var layout = {
        legend: {
            orientation: 'h',
            x: 0,
            y: 1.2,
            itemclick: false
        },
        xaxis: {
            title: data["x_label"],
        },
        yaxis: {
            title: data["y_label"],
        },
        margin: {
            l: 50,
            r: 50,
            b: 50,
            t: 50,
        },
        showlegend: true,
        width: data["plot_width"] * 0.99
    }; 

    Plotly.newPlot(plot_id, currentPlotData, layout, {
        scrollZoom: false,
        displayModeBar: false
    }).then(manageLegend);
}


function createSettingsMenu() {
    num += 1;
    return ' \
        <div class="border border-primary rounded-3 text-start my-2 mx-5 py-1"> \
            <div class="clickable px-3" onclick="toggleMenu(this, id)"> \
                <div class="row"> \
                    <div class="col-11"> \
                        <strong>Settings</strong> \
                    </div> \
                    <div class="col-1 text-end"> \
                        <i class="fas fa-lg fa-angle-down"></i> \
                    </div> \
                </div> \
            </div> \
            <div id="contents_menu" class="openable px-3"> \
                <div class="row"> \
                    <div class="col-xl-3 col-lg-5 col-md-12 col-sm-12"> \
                        <label class="form-label mb-0">Voltage correction (mV): </label> \
                    </div> \
                    <div class="col-xl-8 col-lg-6 col-md-10 col-sm-10"> \
                        <input id="vcorr_' + num + '" class="vcorr-value form-control d-inline" type="number" value=0> \
                        <i class="fas fa-minus ms-5" onclick="updateVoltageCorrection(this, -5)"></i> \
                        <i class="fas fa-plus ms-3" onclick="updateVoltageCorrection(this, 5)"></i> \
                    </div> \
                    <div class="col-xl-1 col-lg-1 col-md-2 col-sm-2 text-end"> \
                        <i class="far fa-question-circle fa-lg" onclick="openInfoPanel(vcorrTitle, vcorrText)"></i> \
                    </div> \
                </div> \
            </div> \
        </div> \
    ';
}


vcorrTitle = "Voltage Correction";
vcorrText = "The voltage correction value inserted by the user is added to all the  voltage values (i.e., all the sweeps) of the related file.";
