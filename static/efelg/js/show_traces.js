// show "check permissions" message
//writeMessage("wmd-first", "Checking data permissions. This may take 30s to 50s");
writeMessage("wmd-first", "Loading");
writeMessage("wmd-second", "Please wait...");
openMessageDiv("wait-message-div", "main-e-st-div");

menus = []
menus.push($('#parameters_menu'));
$(window).resize(() => menus.forEach(menu => {
    if (menu.css('maxHeight') != "0px") {
        menu.css({ maxHeight: menu[0].scrollHeight + "px" });
    }
}));

//
function submitAll() {
    var $submitForm = $('#gonextform');
    $submitForm.submit(function (e) {
        var data = serializeAll();
        var parameters = getParameters();
        var form = $('#gonextform')[0];
        form[1].value = JSON.stringify(data);
        form[2].value = JSON.stringify(parameters);
        list_len = Object.keys(data).length;
        e.preventDefault();
        if (list_len == 0) {
            openWarning("No data selected");
        } else {
            openMessageDiv("e-st-user-choice-div", "main-e-st-div");
            var list_div = document.getElementById("e-st-user-choice");
            while (list_div.firstChild) {
                list_div.removeChild(list_div.firstChild);
            }
            for (var i = 0; i < list_len; i++) {
                var crr_key = Object.keys(data)[i];
                var crr_stim = data[Object.keys(data)[i]]['stim'];
                var crr_div = document.createElement("DIV");
                if (i % 2 == 0) {
                    crr_div.style.backgroundColor = 'rgb(220, 220, 220)';
                } else {
                    crr_div.style.background = 'rgb(240, 240, 240)';
                }
                var cellname_span = document.createElement("SPAN");
                var cell_title_text = document.createTextNode("Cell details: ");
                var splitted_string = crr_key.split("____");
                cellname_span.className = "simple-span";
                cellname_span.appendChild(cell_title_text);
                for (var jj = 0; jj < splitted_string.length; jj++) {
                    var textnode = document.createTextNode(splitted_string[jj]);
                    var separator = document.createTextNode(" - ");
                    cellname_span.appendChild(textnode);
                    cellname_span.appendChild(separator);
                }
                cellname_span.removeChild(cellname_span.lastChild);

                crr_div.appendChild(cellname_span);
                var stim_span = document.createElement("SPAN");
                stim_span.className = "simple-span";

                var stimtext = document.createTextNode("Stimuli: ");
                stim_span.appendChild(stimtext);

                var sorted_stim = [];
                for (var ii = 0; ii < crr_stim.length; ii++) {
                    sorted_stim.push(parseFloat(crr_stim[ii]));
                }
                sorted_stim_fin = sorted_stim.sort(function (a, b) { return a - b });
                for (var j = 0; j < sorted_stim_fin.length; j++) {
                    var stimtextnode = document.createTextNode(sorted_stim_fin[j] + "; ");
                    stim_span.appendChild(stimtextnode);
                }
                crr_div.appendChild(stim_span);
                list_div.appendChild(crr_div);
            }
        }
    });
}

//
function serializeAll() {
    var obj = {};
    var forms = $('[id^="form_"]');
    var infos = $('[id^="info_"]');
    for (var i = 0; i < forms.length; i++) {
        var cell_name = $(forms[i]).parent()[0].id;
        var cboxes = $(forms[i]).find('[type="checkbox"]');
        var traces = [];
        for (var j = 0; j < cboxes.length; j++) {
            if (cboxes[j].checked)
                traces.push(cboxes[j].name);
        }
        if (traces.length != 0) {
            var sampleObj = {};
            sampleObj['stim'] = traces;
            sampleObj['v_corr'] = $(infos[i]).find('#vcorr_value').val();
            obj[cell_name] = sampleObj;
        }
    }
    return obj
}

//
function getParameters() {
    var parameters = {};
    parameters['threshold'] = $('#threshold_value').val();
    parameters['zero_std'] = $('input[type=radio][name=zero_std]:checked').val();
    parameters['value'] = $('#zero_value').val();
    parameters['num_events'] = $('#events_value').val();
    if (parameters['value'] == "null") {
        parameters['zero_to_nan'] = "False";
    } else {
        parameters['zero_to_nan'] = "True";
    }
    var mean_features_no_zeros = [];
    $('input[type=checkbox][name=mean_features_no_zeros]:checked').each(function () {
        if (this.value != "all") {
            mean_features_no_zeros.push(this.value);
        }
    });
    parameters['mean_features_no_zeros'] = mean_features_no_zeros;
    return parameters;
}

//
function splitFilename(cellname) {
    var filenameTokens = cellname.split('____');
    return filenameTokens
}

//
function acceptUserChoiceList() {
    var crr_div = document.getElementById("e-st-user-choice");
    while (crr_div.firstChild) {
        crr_div.removeChild(crr_div.firstChild);
    }
    var form = $('#gonextform')[0];
    closeMessageDiv("e-st-user-choice-div", "main-e-st-div");
    writeMessage("wmd-first", "");
    writeMessage("wmd-second", "");
    form.submit();
}

//
function closeUserChoiceList() {
    closeMessageDiv("e-st-user-choice-div", "main-e-st-div");
    var crr_div = document.getElementById("e-st-user-choice");
    while (crr_div.firstChild) {
        crr_div.removeChild(crr_div.firstChild);
    }
}

//
function TracePlot(container_id, cell_obj) {
    const SHOW_FADED = 0.15;
    const SHOW_CHECK = 0.65;
    const SHOW_HOVER = 1.0;
    var temp = Object.keys(cell_obj);
    var n_traces = Object.keys(cell_obj['traces']).length;
    var self = this;
    this.container = $('#' + container_id);
    this.container.addClass("border border-primary rounded-3 my-4 mx-1 p-2");

    this.cell_obj = cell_obj;

    this.appearance = new Array(n_traces);
    this.appearance.fill(SHOW_FADED);

    this.tmp_appearance_hover = null;

    function init() {
        var md5 = cell_obj['md5'];
        var timestamp = Date.now();

        new_keys = {
            "species": "animal_species",
            "area": "brain_structure",
            "region": "cell_soma_location",
            "type": "type",
            "etype": "etype",
            "name": "cell_id",
            "sample": "filename",
        }
        self.cellinfo = [];
        for (key of Object.keys(new_keys)) {
            if (new_keys[key] in self.cell_obj) {
                self.cellinfo.push(self.cell_obj[new_keys[key]]);
            } else {
                self.cellinfo.push(self.cell_obj[key]);
            }
        }
        /*
        self.cellinfo = [
            self.cell_obj['species'],
            self.cell_obj['area'],
            self.cell_obj['region'],
            self.cell_obj['type'],
            self.cell_obj['etype'],
            self.cell_obj['name'],
            self.cell_obj['sample']
        ];
        */
        self.contributors = self.cell_obj['contributors']['message'];

        // Erase everything
        self.container.empty();

        // Creates the boxes that will host info and data
        self.infobox = $('<div/>', {
            'id': 'info_' + md5 + timestamp,
            'class': 'row px-4',
        }).appendTo(self.container);

        self.formbox = $('<div/>', {
            'id': 'form_' + md5 + timestamp,
            'class': 'd-none',
        }).appendTo(self.container);

        self.plotbox = $('<div/>', {
            'id': 'plot_' + md5 + timestamp,
            'class': 'table-responsive',
        }).appendTo(self.container);

        // Populates the boxes
        self.infobox.append(' \
                            <div class="col-12 mb-2"> \
                                <a> \
                                    Cell properties: ' + self.cellinfo.join(' > ') + '   [' + self.contributors + '] \
                                </a> \
                            </div> \
                            <div class="col-12 mb-2"> \
                                <a class="selall clickable mx-2">Select all</a> \
                                <a class="dselall clickable mx-2">Deselect all</a> \
                                <a class="invsel clickable mx-2">Invert selection</a> \
                            </div> \
                            ');
        var settingsMenu = createSettingsMenu();
        self.infobox.append(settingsMenu);
        menus.push($(settingsMenu));
    }

    function manageLegend() {
        var legend = Plotly.d3.select('#' + self.plotbox.attr('id') + ' g.legend');
        var elems = legend.selectAll('.traces rect');

        // Saves the value of the opacity before the mousehover
        function savePrevious(d) {
            var i = d[0].trace.index;

            self.tmp_appearance_hover = self.appearance[i];

            self.appearance[i] = SHOW_HOVER;

            self.refresh();
        }

        // Restores the value of the opacity after the mouseleave
        function restorePrevious(d) {
            var i = d[0].trace.index;

            self.appearance[i] = self.tmp_appearance_hover;
            self.refresh();
        }

        // Allows to toggle the opacity of the specified trace
        function setOpacity(d) {
            var check_name = 'input[name^="' + d[0].trace.name.slice(0, -3) + '"]';

            if (self.tmp_appearance_hover == SHOW_FADED) {
                self.formbox.find(check_name)[0].checked = true;
                self.tmp_appearance_hover = SHOW_CHECK;
            } else {
                self.formbox.find(check_name)[0].checked = false;
                self.tmp_appearance_hover = SHOW_FADED;
            }
        }

        // Binds the events to every element of the legend
        elems.each(function () {
            Plotly.d3.select(this).on('click', setOpacity);
            Plotly.d3.select(this).on('mouseenter', savePrevious);
            Plotly.d3.select(this).on('mouseleave', restorePrevious);
        })

    }

    function plot(w) {
        var plotdata = [];

        $.each(self.cell_obj['traces'], function (key, trace) {
            self.formbox.append('<input type="checkbox" name="' + key + '" />');
            var trace_len = trace.length;
            var a = Array.apply(null, { length: trace_len }).map(Number.call, Number);
            var b = a.map(x => x * 1000 / self.cell_obj['disp_sampling_rate']);

            var unit = ""
            if ("stimulus_unit" in self.cell_obj) {
                unit = self.cell_obj["stimulus_unit"]
            } else {
                unit = self.cell_obj["amp_unit"]
            }

            // Defines what is about to be plotted
            var newTrace = {
                y: trace,
                x: b,
                name: key + ' ' + unit,
                mode: 'lines',
                hoverinfo: 'none',
                opacity: SHOW_FADED,
            }
            plotdata.push(newTrace);
        })

        // Sorts the traces names (mathematical order)
        plotdata.sort(function (a, b) {
            var a = parseFloat(a.name);
            var b = parseFloat(b.name);

            if (a == b) {
                return 0
            } else if (a < b) {
                return 1
            } else {
                return -1
            }
        })

        var layout = {
            legend: {
                orientation: "h",
                x: 0,
                y: 1.1,
            },
            yaxis: {
                title: self.cell_obj['volt_unit'],
            },
            xaxis: {
                title: 'ms',
            },
            showlegend: true,
            margin: {
                l: 50,
                r: 50,
                b: 50,
                t: 50,
            },
            width: w,
            height: 450,
        }

        Plotly.newPlot(self.plotbox.attr('id'), plotdata, layout, { displayModeBar: false }).then(manageLegend);
        self.refresh();
    }

    function bindEvents() {
        self.plotbox.on('plotly_relayout', function (ev) {
            self.refresh();
        })


        // Select every trace
        self.infobox.find('.selall').click(function (ev) {
            self.appearance.fill(SHOW_CHECK);
            self.formbox.find('input').prop('checked', true);
            self.refresh();
        })

        // Deselect all traces
        self.infobox.find('.dselall').click(function (ev) {
            self.appearance.fill(SHOW_FADED);
            self.formbox.find('input').prop('checked', false);
            self.refresh();
        })

        // Invers the selection
        self.infobox.find('.invsel').click(function (ev) {
            for (var i = 0; i < self.appearance.length; i++) {
                self.appearance[i] = self.appearance[i] == SHOW_FADED ? SHOW_CHECK : SHOW_FADED;

                var cb = self.formbox.find('input')[i];
                cb.checked = !cb.checked;
            }

            self.refresh();
        })

    }

    this.refresh = function () {
        var update = {
            opacity: self.appearance
        }

        Plotly.restyle(self.plotbox.attr('id'), update).then(manageLegend);

        // Sets the opacities of the legend's labels
        legend = Plotly.d3.select('#' + self.plotbox.attr('id') + ' g.legend');
        legend.selectAll('.traces').each(function (d, i) {
            Plotly.d3.select(this).style('opacity', update.opacity[i] + 0.4);
        })
    }

    init();
    plot(this.container.width() * 0.99);
    bindEvents();
}

/*
// Plotting class
function TracePlot(container_id, cell_obj) {
    const SHOW_FADED = 0.15;
    const SHOW_CHECK = 0.65;
    const SHOW_HOVER = 1.0;
    var temp = Object.keys(cell_obj);
    var n_traces = Object.keys(cell_obj['traces']).length;
    var self = this;

    this.container = $('#' + container_id);
    this.cell_obj = cell_obj;

    this.appearance = new Array(n_traces);
    this.appearance.fill(SHOW_FADED);

    this.tmp_appearance_hover = null;

    function init() {
        var md5 = cell_obj['md5'];
        var timestamp = Date.now();

        self.cellinfo = [self.cell_obj['species'], self.cell_obj['area'],
        self.cell_obj['region'], self.cell_obj['type'],
        self.cell_obj['etype'], self.cell_obj['name'],
        self.cell_obj['sample']];
        self.contributors = self.cell_obj['contributors']['message'];

        // Erase everything
        self.container.empty();

        // Creates the boxes that will host info and data

        self.infobox = $('<div/>', {
            'id': 'info_' + md5 + timestamp,
            'class': 'panel-heading fn-container',
        }).appendTo(self.container);

        self.formbox = $('<div/>', {
            'id': 'form_' + md5 + timestamp,
            'class': 'hidden',
        }).appendTo(self.container);

        self.plotbox = $('<div/>', {
            'id': 'plot_' + md5 + timestamp,
        }).appendTo(self.container);

        // Populates the boxes
        self.infobox.append('<span class="single-cell" style="font-size:8px"></span>').text('Cell properties: ' + self.cellinfo.join(' > ') + '   [' + self.contributors + ']');
        self.infobox.append('<br>');
        self.infobox.append('<button class="selall btn btn-link btn-default">Select all</button>');
        self.infobox.append('<button class="dselall btn btn-link btn-default">Deselect all</button>');
        self.infobox.append('<button class="invsel btn btn-default btn-link">Invert selection</button>');
    }

    function manageLegend() {
        var legend = Plotly.d3.select('#' + self.plotbox.attr('id') + ' g.legend');
        var elems = legend.selectAll('.traces rect');

        // Saves the value of the opacity before the mousehover
        function savePrevious(d) {
            var i = d[0].trace.index;

            self.tmp_appearance_hover = self.appearance[i];

            self.appearance[i] = SHOW_HOVER;

            self.refresh();
        }

        // Restores the value of the opacity after the mouseleave
        function restorePrevious(d) {
            var i = d[0].trace.index;

            self.appearance[i] = self.tmp_appearance_hover;
            self.refresh();
        }

        // Allows to toggle the opacity of the specified trace
        function setOpacity(d) {
            var check_name = 'input[name^="' + d[0].trace.name.slice(0, -3) + '"]';

            if (self.tmp_appearance_hover == SHOW_FADED) {
                self.formbox.find(check_name)[0].checked = true;
                self.tmp_appearance_hover = SHOW_CHECK;
            } else {
                self.formbox.find(check_name)[0].checked = false;
                self.tmp_appearance_hover = SHOW_FADED;
            }
        }

        // Binds the events to every element of the legend
        elems.each(function() {
            Plotly.d3.select(this).on('click', setOpacity);
            Plotly.d3.select(this).on('mouseenter', savePrevious);
            Plotly.d3.select(this).on('mouseleave', restorePrevious);
        })

    }

    function plot() {
        var plotdata = [];

        $.each(self.cell_obj['traces'], function(key, trace) {
            self.formbox.append('<input type="checkbox" name="' + key + '" />');
            var trace_len = trace.length;
            var a = Array.apply(null, {length: trace_len}).map(Number.call, Number);
            var b = a.map(x => x * 1000 / self.cell_obj['disp_sampling_rate']);

            // Defines what is about to be plotted
            var newTrace = {
                y: trace,
                x: b,
                name: key + ' ' + self.cell_obj['amp_unit'],
                mode: 'lines',
                hoverinfo: 'none',
                opacity: SHOW_FADED,
            }
                plotdata.push(newTrace);
        })

        // Sorts the traces names (mathematical order)
        plotdata.sort(function(a, b) {
            var a = parseFloat(a.name);
            var b = parseFloat(b.name);

            if (a == b) {
                return 0	
            } else if (a < b) {
                return 1
            } else {
                return -1
            }                     
        })

        var layout = {
            legend: {
                orientation: "h",
                x: 0,
                y: 1.1,
            },
            yaxis: {
                title: self.cell_obj['volt_unit'],
            },
            xaxis: {
                title: 'ms',
            },
            showlegend: true,
            margin: {l: 50, b: 35, t: 0} 
        }

            Plotly.newPlot(self.plotbox.attr('id'), plotdata, layout, {displayModeBar: false}).then(manageLegend);
        self.refresh();
    }

    function bindEvents() {
        self.plotbox.on('plotly_relayout', function(ev) {
            self.refresh();
        })


        // Select every trace
        self.infobox.find('.selall').click(function(ev) {
            self.appearance.fill(SHOW_CHECK);
            self.formbox.find('input').prop('checked', true);
            self.refresh();
        })

        // Deselect all traces
        self.infobox.find('.dselall').click(function(ev) {
            self.appearance.fill(SHOW_FADED);
            self.formbox.find('input').prop('checked', false);
            self.refresh();
        })

        // Invers the selection
        self.infobox.find('.invsel').click(function(ev) {
            for (var i = 0; i < self.appearance.length; i++) {
                self.appearance[i] = self.appearance[i] == SHOW_FADED ? SHOW_CHECK : SHOW_FADED;

                var cb = self.formbox.find('input')[i];
                cb.checked = ! cb.checked;
            }

            self.refresh();
        })
    }

    this.refresh = function() {
        var update = {
            opacity: self.appearance
        }

        Plotly.restyle(self.plotbox.attr('id'), update).then(manageLegend);

        // Sets the opacities of the legend's labels
        legend = Plotly.d3.select('#' + self.plotbox.attr('id') + ' g.legend');
        legend.selectAll('.traces').each(function(d, i) {
            Plotly.d3.select(this).style('opacity', update.opacity[i] + 0.4);
        })
    }

    init();
    plot();
    bindEvents();
}
*/


//
$(document).ready(function () {
    window.scrollTo(0, 0);
    var selected_files = [];

    /* MODIFIED
    function write_box(box_id, label_id, type, message) {
        $('#' + box_id).show();
        $('#' + box_id).removeClass();
        $('#' + box_id).addClass('panel panel-' + type);
        $('#' + label_id).html(message);
    }
    */

    $('#charts').empty();
    var jqxhr = $.getJSON('/efelg/get_list', function (data) {
        json = data;
        contrib_keys = Object.keys(json['Contributors']);
        for (var i = 0; i < contrib_keys.length; i++) {
            c = contrib_keys[i];
            if (!checkIfElementExists('contributors_' + c, 'contributors')) {
                var div1 = document.createElement('div');
                var label1 = document.createElement('label');
                label1.id = 'contributors_' + c;
                label1.title = c;
                label1.innerHTML = c;
                label1.classList.add('withinTable', 'activated', 'mb-2');
                label1.setAttribute('for', 'contributors');
                label1.setAttribute('onClick', 'selectLabel(this)');
                div1.append(label1);
                document.getElementById('contributors').append(div1);
            }

            species_keys = Object.keys(json['Contributors'][c]);
            for (var j = 0; j < species_keys.length; j++) {
                s = species_keys[j];
                if (!checkIfElementExists('species_' + s, 'species')) {
                    var div2 = document.createElement('div');
                    var label2 = document.createElement('label');
                    label2.id = 'species_' + s;
                    label2.title = s;
                    label2.innerHTML = s;
                    label2.classList.add('withinTable', 'activated', 'mb-2');
                    label2.setAttribute('for', 'species');
                    label2.setAttribute('onClick', 'selectLabel(this)');
                    div2.append(label2);
                    document.getElementById('species').append(div2);
                }

                structure_keys = Object.keys(json['Contributors'][c][s]);
                for (var k = 0; k < structure_keys.length; k++) {
                    ss = structure_keys[k];
                    if (!checkIfElementExists('structures_' + ss, 'structures')) {
                        var div3 = document.createElement('div');
                        var label3 = document.createElement('label');
                        label3.id = 'structures_' + ss;
                        label3.title = ss;
                        label3.innerHTML = ss;
                        label3.classList.add('withinTable', 'activated', 'mb-2');
                        label3.setAttribute('for', 'structures');
                        label3.setAttribute('onClick', 'selectLabel(this)');
                        div3.append(label3);
                        document.getElementById('structures').append(div3);
                    }

                    region_keys = Object.keys(json['Contributors'][c][s][ss]);
                    for (var f = 0; f < region_keys.length; f++) {
                        r = region_keys[f];
                        if (!checkIfElementExists('regions_' + r, 'regions')) {
                            var div4 = document.createElement('div');
                            var label4 = document.createElement('label');
                            label4.id = 'regions_' + r;
                            label4.title = r;
                            label4.innerHTML = r;
                            label4.classList.add('withinTable', 'activated', 'mb-2');
                            label4.setAttribute('for', 'regions');
                            label4.setAttribute('onClick', 'selectLabel(this)');
                            div4.append(label4);
                            document.getElementById('regions').append(div4);
                        }

                        type_keys = Object.keys(json['Contributors'][c][s][ss][r]);
                        for (var d = 0; d < type_keys.length; d++) {
                            t = type_keys[d];
                            if (!checkIfElementExists('types_' + t, 'types')) {
                                var div5 = document.createElement('div');
                                var label5 = document.createElement('label');
                                label5.id = 'types_' + t;
                                label5.title = t;
                                label5.innerHTML = t;
                                label5.classList.add('withinTable', 'activated', 'mb-2');
                                label5.setAttribute('for', 'types');
                                label5.setAttribute('onClick', 'selectLabel(this)');
                                div5.append(label5);
                                document.getElementById('types').append(div5);
                            }

                            etype_keys = Object.keys(json['Contributors'][c][s][ss][r][t]);
                            for (var n = 0; n < etype_keys.length; n++) {
                                e = etype_keys[n];
                                if (!checkIfElementExists('etypes_' + e, 'etypes')) {
                                    var div6 = document.createElement('div');
                                    var label6 = document.createElement('label');
                                    label6.id = 'etypes_' + e;
                                    label6.title = e;
                                    label6.innerHTML = e;
                                    label6.classList.add('withinTable', 'activated', 'mb-2');
                                    label6.setAttribute('for', 'etypes');
                                    label6.setAttribute('onClick', 'selectLabel(this)');
                                    div6.append(label6);
                                    document.getElementById('etypes').append(div6);
                                }
                            }
                        }
                    }
                }
            }
        }
    }).done(function () {
        closeMessageDiv("wait-message-div", "main-e-st-div");
    });
});

function checkIfElementExists(elementId, tableId) {
    childList = document.getElementById(tableId).childNodes;
    for (var i = 0; i < childList.length; i++) {
        if (elementId == childList[i].childNodes[0].id) {
            return true;
        }
    }
    return false;
}

/* MODIFIED 
function write_box(box_id, label_id, type, message) {
    if (type == "info") {
        hideDiv("loadfile_box_rejected");
    }
    $('#' + box_id).show();
    $('#' + box_id).removeClass();
    $('#' + box_id).addClass('panel panel-' + type);
    $('#' + label_id).html(message);
}
*/

/* 
$(document).ready(function(){
    window.scrollTo(0,0);
    var selected_files = [];

    function write_box(box_id, label_id, type, message) {
        $('#' + box_id).show();
        $('#' + box_id).removeClass();
        $('#' + box_id).addClass('panel panel-' + type);
        $('#' + label_id).html(message);
    }

    $("#user_files").change(function(e) {
        var string = '<b>Files selected: </b> ';
        var names = Object.values(e.target.files);

        selected_files = names.map(function(item) {
            return item.name;
        })

        string += selected_files.join(', ');
        write_box('loadfile_box', 'loadfile_info', 'info', string);
    })


    $("form#upload_files").submit(function(e) {
        e.preventDefault();
        writeMessage("wmd-first", "Uploading data");
        writeMessage("wmd-second", "Please wait ...");
        openMessageDiv("wait-message-div", "main-e-st-div");
        write_box('loadfile_box', 'loadfile_info', 'info', '<b>Loading files...</b>');

        var formData = new FormData($(this)[0]);
        $.ajax({
            url: $(this).attr("action"),
            data: formData,
            type: 'POST',
            contentType: false,
            processData: false,
            success: function(name_dict) {
                var loaded_filenames = name_dict.all_json_names;
                var refused_filenames = [];
                loaded_filenames = loaded_filenames.map(function(item) {
                    var splitted = item.split('____');
                    return splitted[splitted.length - 1] + '.abf'
                })
                selected_files.forEach(function(elem) {
                    if (loaded_filenames.indexOf(elem) == -1)
                        refused_filenames.push(elem);
                })

                if (loaded_filenames.length == 0)
                    write_box('loadfile_box', 'loadfile_info', 'info', '<b>No file to be uploaded!</b>');
                if (refused_filenames.length) {
                    write_box('loadfile_box_rejected', 'loadfile_info_rejected', 'danger', '<b>Rejected files:</b> ' + refused_filenames.join(', '));
                    showDiv("loadfile_box_rejected"); 
                }
                else
                {
                    write_box('loadfile_box_rejected', 'loadfile_info_rejected', 'danger', '');
                    hideDiv("loadfile_box_rejected"); 
                }
                if (loaded_filenames.length > 0){
                    writeMessage("wmd-first", "Uploading data");
                    writeMessage("wmd-second", "Please wait ...");
                    openMessageDiv("wait-message-div", "main-e-st-div");
                }

                $('#charts_upload').empty();
                all_json_names = name_dict['all_json_names'];
                if (all_json_names.length == 0){
                    closeMessageDiv("wait-message-div", "main-e-st-div");
                }
                index = 'user_div';
                $('#charts_upload').append('<div class="cell panel panel-default" id="' + index  + '"></div>')
                    var counter = 0;
                $.each(all_json_names, function(idx, elem) {
                    $('#' + index).append('<div id="' + elem + '"></div>');
                    $.getJSON('/efelg/get_data/' + elem, function(data) {
                        new TracePlot(elem, JSON.parse(data));
                        counter = counter + 1;
                        if (counter == all_json_names.length){
                            closeMessageDiv("wait-message-div", "main-e-st-div");
                            write_box('loadfile_box', 'loadfile_info', 'info', '<b>Uploaded files:</b>' + loaded_filenames.join(', '));
                        }
                    });
                });
            }
        })
    });

    $('#charts').empty();
    var jqxhr = $.getJSON('/efelg/get_list', function(data) {
        json = data;
        contrib_keys = Object.keys(json['Contributors']);
        for (var i = 0; i < contrib_keys.length; i++) {
            c = contrib_keys[i];
            if (!checkIfElementExists('contributors_' + c, 'contributors')) {
                var div1 = document.createElement('div');
                var label1 = document.createElement('label');
                label1.id = 'contributors_' + c;
                label1.title = c;
                label1.innerHTML = c;
                label1.classList.add('withinTable', 'activated');
                label1.setAttribute('for', 'contributors');
                label1.setAttribute('onClick', 'selectLabel(this)');
                div1.append(label1);
                document.getElementById('contributors').append(div1);
            }

            species_keys = Object.keys(json['Contributors'][c]);
            for (var j = 0; j < species_keys.length; j++) {
                s = species_keys[j];
                if (!checkIfElementExists('species_' + s, 'species')) {
                    var div2 = document.createElement('div');
                    var label2 = document.createElement('label');
                    label2.id = 'species_' + s;
                    label2.title = s;
                    label2.innerHTML = s;
                    label2.classList.add('withinTable', 'activated');
                    label2.setAttribute('for', 'species');
                    label2.setAttribute('onClick', 'selectLabel(this)');
                    div2.append(label2);
                    document.getElementById('species').append(div2);
                }

                structure_keys = Object.keys(json['Contributors'][c][s]);
                for (var k = 0; k < structure_keys.length; k++) {
                    ss = structure_keys[k];
                    if (!checkIfElementExists('structures_' + ss, 'structures')) {
                        var div3 = document.createElement('div');
                        var label3 = document.createElement('label');
                        label3.id = 'structures_' + ss;
                        label3.title = ss;
                        label3.innerHTML = ss;
                        label3.classList.add('withinTable', 'activated');
                        label3.setAttribute('for', 'structures');
                        label3.setAttribute('onClick', 'selectLabel(this)');
                        div3.append(label3);
                        document.getElementById('structures').append(div3);
                    }

                    region_keys = Object.keys(json['Contributors'][c][s][ss]);
                    for (var f = 0; f < region_keys.length; f++) {
                        r = region_keys[f];
                        if (!checkIfElementExists('regions_' + r, 'regions')) {
                            var div4 = document.createElement('div');
                            var label4 = document.createElement('label');
                            label4.id = 'regions_' + r;
                            label4.title = r;
                            label4.innerHTML = r;
                            label4.classList.add('withinTable', 'activated');
                            label4.setAttribute('for', 'regions');
                            label4.setAttribute('onClick', 'selectLabel(this)');
                            div4.append(label4);
                            document.getElementById('regions').append(div4);
                        }

                        type_keys = Object.keys(json['Contributors'][c][s][ss][r]);
                        for (var d = 0; d < type_keys.length; d++) {
                            t = type_keys[d];
                            if (!checkIfElementExists('types_' + t, 'types')) {
                                var div5 = document.createElement('div');
                                var label5 = document.createElement('label');
                                label5.id = 'types_' + t;
                                label5.title = t;
                                label5.innerHTML = t;
                                label5.classList.add('withinTable', 'activated');
                                label5.setAttribute('for', 'types');
                                label5.setAttribute('onClick', 'selectLabel(this)');
                                div5.append(label5);
                                document.getElementById('types').append(div5);
                            }

                            etype_keys = Object.keys(json['Contributors'][c][s][ss][r][t]);
                            for (var n = 0; n < etype_keys.length; n++) {
                                e = etype_keys[n];
                                if (!checkIfElementExists('etypes_' + e, 'etypes')) {
                                    var div6 = document.createElement('div');
                                    var label6 = document.createElement('label');
                                    label6.id = 'etypes_' + e;
                                    label6.title = e;
                                    label6.innerHTML = e;
                                    label6.classList.add('withinTable', 'activated');
                                    label6.setAttribute('for', 'etypes');
                                    label6.setAttribute('onClick', 'selectLabel(this)');
                                    div6.append(label6);
                                    document.getElementById('etypes').append(div6);
                                }
                            }
                        }
                    }
                }
            }
        }
    })
    .done(function() {
        closeMessageDiv("wait-message-div", "main-e-st-div");
    });
});
*/

var json;
var contributor = null;
var specie = null;
var structure = null;
var region = null;
var type = null;
var etype = null;


function applySelection() {
    writeMessage("wmd-first", "Loading traces");
    writeMessage("wmd-second", "Please wait ...");
    openMessageDiv("wait-message-div", "main-e-st-div");
    $('#charts').empty();
    cells = Object.keys(json['Contributors'][contributor][specie][structure][region][type][etype]);
    for (var i = 0; i < cells.length; i++) {

        var cell = cells[i];
        var cell_name = contributor + ' > ' + specie + ' > ' + structure + ' > ' + region + ' > ' + type + ' > ' + etype + ' > ' + cell;
        
        var cellHeader = createCellHeader(cell_name, cell)
        $('#charts').append(cellHeader);
        cellHeader.append('<div id="' + cell + '"></div>');

        file = Object.values(json['Contributors'][contributor][specie][structure][region][type][etype][cell]);
        file.forEach(function (el) {
            var fileName = el.split('.')[0];
            $('#' + cell).append('<div id="' + fileName + '"></div>');
            $.getJSON('/efelg/get_data/' + fileName, function (data) {
                writeMessage("wmd-first", "Cell " + (i + 1).toString() +
                    +" of " + (cells.length + 1).toString() +
                    +". Loading traces for file " + (1 + 1).toString() +
                    +" of " + (file.length + 1).toString());
                new TracePlot(fileName, JSON.parse(data));
            })
        });
    }
    closeMessageDiv("wait-message-div", "main-e-st-div");
    writeMessage("wmd-first", "");
    writeMessage("wmd-second", "");
}

function createCellHeader(cell_name, cell_id) {
    var cell_container = $('<div class="cell text-center" />');
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
        </div>');
    cell_container.find('.cell_selall').click(function () {
        $(this).parents('.cell').find('.selall').click();
    })

    cell_container.find('.cell_dselall').click(function () {
        $(this).parents('.cell').find('.dselall').click();
    })

    cell_container.find('.cell_invsel').click(function () {
        $(this).parents('.cell').find('.invsel').click();
    })
    return cell_container;
}

vcorr_title = "VCORR_TITLE";
vcorr_text = "VCORR_TEXT";

function createSettingsMenu() {
    id = "contents_menu";
    html_string = ' \
        <div class="border border-primary rounded-3 text-start my-2 py-1"> \
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
                        <label for="vcorr_value" class="form-label mb-0">Voltage correction (mV): </label> \
                    </div> \
                    <div class="col-xl-8 col-lg-6 col-md-10 col-sm-10"> \
                        <input id="vcorr_value" class="form-control d-inline" type="number" value=0> \
                        <i class="fas fa-minus ms-5" onclick="updateValue(this, -5)"></i> \
                        <i class="fas fa-plus ms-3" onclick="updateValue(this, 5)"></i> \
                    </div> \
                    <div class="col-xl-1 col-lg-1 col-md-2 col-sm-2 text-end"> \
                        <i class="far fa-question-circle fa-lg" onclick="openInfo(vcorr_title, vcorr_text)"></i> \
                    </div> \
                </div> \
            </div> \
        </div> \
    ';
    return html_string;
}

function toggleMenu(button, id) {
    button.classList.toggle("active");
    var container = $(button).siblings(id);
    var icon = $(button).find('.fas')[0];
    if (container.css('maxHeight') != "0px") {
        container.css({ maxHeight: 0 + "px" });
        icon.classList.remove("fa-angle-up")
        icon.classList.add("fa-angle-down")
    } else {
        container.css({ maxHeight: container[0].scrollHeight + "px" });
        icon.classList.remove("fa-angle-down")
        icon.classList.add("fa-angle-up")
    }
}

var parameters_info = ' \
    <p> \
        <b>Threshold (mV)</b>: \
        <br>Membrane potential threshold for action potential detection. \
    </p> \
    <p> \
        <b>Accept zero std</b>: \
        <br>If set to &quotFalse&quot only mean feature values with std > 0 or mean = 0 \
        will be collected; otherwise all mean values (different than &quotnan&quot) will be collected. \
    </p> \
    <p> \
        <b>Convert zero feature values to</b>: \
        <br>When &quotnan&quot or &quotstim_end&quot are selected in the leftmost \
        drop-down menu, the values of the features selected in the rightmost drop-down menu are converted to &quotnan&quot \
        or to the stimulus end time respectively, if their value is zero after the feature extraction.<br> \
        For no changes in the feature extraction process, select &quot-&quot in the leftmost drop-down menu. \
    </p> \
    <p> \
        <b>Number of printed events per feature</b>: \
        <br>Number of values that will be stored, per feature, in the feature table generated as output file; \
        this parameter is only applied to features that represent spike related properties and for which multiple \
        occurrences might be extracted from a single trace (e.g. AP_amplitude, AP_width, ...).<br> \
        Anyway, the average values reported in the features.json and protocols.json output files are computed on all the occurrences. \
    </p>'

function toggleParametersMenu(button) {
    toggleMenu(button, '#parameters_menu');
    var menu = $('#parameters_menu');
    if (menu.css('overflow') == 'visible') {
        menu.css({overflow: 'hidden'})
    } else {
        menu.css({overflow: 'visible'})
    }
}

function updateDropdownMenu(selection) {
    var dropdown = $("#dropdownMenuButton");
    if ($(selection).val() == "null") {
        dropdown.text("");
        dropdown.attr("disabled", true);
    } else {
        dropdown.text("Choose ");
        dropdown.attr("disabled", false);
    }
}

function selectAllCheckboxes(selectAll) {
    if ($(selectAll).prop("checked")) {
        $('input[type=checkbox][name=mean_features_no_zeros]').each(function () {
            $(this).prop("checked", true);
        });
    }
}

function updateValue(button, value) {
    var input = $(button).siblings('input[type=number]');
    input.val((parseFloat(input.val()) + parseFloat(value)).toFixed(0));
}

function updateEventsValue(button, value) {
    updateValue(button, value);
    checkEventsValue();
}

function checkEventsValue() {
    if ($('#events_value').val() < 5) {
        $('#events_value').val(5);
    }
}

$('#events_value').on("change", function() {
    checkEventsValue();
});

/*

function applySelection() {
    writeMessage("wmd-first", "Loading traces");
    writeMessage("wmd-second", "Please wait ...");
    openMessageDiv("wait-message-div", "main-e-st-div");
    $('#charts').empty();
    cells = Object.keys(json['Contributors'][contributor][specie][structure][region][type][etype]);
    for (var i = 0; i < cells.length; i++) {
        var cell = cells[i];
        // adding cell container per fileId
        var cell_name = contributor + ' > ' + specie + ' > ' + structure + ' > ' + region + ' > ' + type + ' > ' + etype + ' > ' + cell;
        var cell_container = $('<div class="cell panel panel-default" />');
        cell_container.append('<div class="panel-heading cell-heading"> \
                <a href="#">Cell: ' + cell_name + ' <br>Cell id: ' + cell + ' </a> \
                <br> \
                <button class="cell_selall btn-link pull-left cell-button">Select all traces</button> \
                <button class="cell_dselall btn-link pull-left cell-button">Deselect all traces</button> \
                <button class="cell_invsel btn-link pull-left cell-button">Invert selection</button> \
                </div>');
        cell_container.append('<div id="' + cell + '"></div>');
        $('#charts').append(cell_container);

        $('#charts').find('.cell:last-of-type a').click(function() {
            $('#' + i).toggle();
            return false;
        })

        $('#charts').find('.cell:last-of-type .cell_selall').click(function() {
            $(this).parents('.cell').find('.selall').click();
        })

        $('#charts').find('.cell:last-of-type .cell_dselall').click(function() {
            $(this).parents('.cell').find('.dselall').click();
        })

        $('#charts').find('.cell:last-of-type .cell_invsel').click(function() {
            $(this).parents('.cell').find('.invsel').click();
        })

        file = Object.values(json['Contributors'][contributor][specie][structure][region][type][etype][cell]);
        file.forEach(function (el) {
            var fileName = el.split('.')[0];
            $('#' + cell).append('<div id="' + fileName + '"></div>');
            $.getJSON('/efelg/get_data/' + fileName, function(data) {
                writeMessage("wmd-first", "Cell " + (i + 1).toString() +
                        + " of " + (cells.length + 1).toString() +
                        + ". Loading traces for file " + (1 + 1).toString() +
                        + " of " + (file.length + 1).toString());
                new TracePlot(fileName, JSON.parse(data));
            })
        });
    }
    closeMessageDiv("wait-message-div", "main-e-st-div");
    writeMessage("wmd-first", "");
    writeMessage("wmd-second", "");
}
*/

function openInfoPanel() {
    closeMessageDiv('warning-div', 'main-e-st-div');
    openInfo(upload_title, upload_text);
}

function checkUploadedFiles(id) {
    var files = $("input#user_files_" + id)[0].files;
    var extension = $('input[type=radio][name=extension_' + id + ']:checked').val();
    var refused_filenames = [];
    var missing_files = [];

    if (extension == ".abf, .json") {
        var coupled_files = {
            "abf": [],
            "json": []
        };
        for (var i = 0; i < files.length; i++) {
            var file_name = files[i]["name"];
            var file_extension = file_name.split(".")[1];
            if (!(["abf", "json"].includes(file_extension))) {
                refused_filenames.push(file_name);
            } else {
                if (file_extension == "json") {
                    if (file_name.substring(file_name.lastIndexOf("_")) == "_metadata.json") {
                        coupled_files[file_extension].push(file_name);
                    } else {
                        refused_filenames.push(file_name);
                    }
                } else {
                    coupled_files[file_extension].push(file_name);
                }
            }
        }
        if (coupled_files["abf"].length > coupled_files["json"].length) {
            missing_files = coupled_files["abf"]
                .map(file => file.substring(0, file.lastIndexOf(".")) + "_metadata.json")
                .filter(json_file => !coupled_files["json"].includes(json_file));
        } else if (coupled_files["abf"].length < coupled_files["json"].length) {
            missing_files = coupled_files["json"]
                .map(file => file.substring(0, file.lastIndexOf("_")) + ".abf")
                .filter(abf_file => !coupled_files["abf"].includes(abf_file));
        }
    } else {
        refused_filenames = [...files].map(file => file["name"]).filter(name => name.split(".")[1] != "json")
    }

    if (refused_filenames.length > 0) {
        openWarning('Rejected files:<br>' + refused_filenames.join(', ') + 
            '<br><br>Please read the information note at this \
            <span class="text-decoration-underline clickable" onclick="openInfoPanel()">link</span>');
        return false;
    } else if (missing_files.length > 0) {
        openWarning('Missing file:<br>You should submit ' + missing_files.join(', ') + " as well!");
        return false;
    }
    return true;
}

function isCellNameUnique(id) {
    var cell_names = $('input[name=cell_name]').get().map(x => x.value);
    var cell_name = $('#cell_name_' + id).val();
    cell_names.splice(cell_names.indexOf(cell_name), 1);
    if (cell_names.includes(cell_name) || cell_name == "") {
        $('#cell_name_alert_' + id).removeClass("d-none");
        $('#cell_name_' + id).addClass("is-invalid");
        $('#cell_name_' + id).removeClass("is-valid");
        return false;
    } else {
        $('#cell_name_alert_' + id).addClass("d-none");
        $('#cell_name_' + id).removeClass("is-invalid");
        $('#cell_name_' + id).addClass("is-valid");
        return true;
    }
}

function areInputTextAllFilled(id) {
    var allFilled = true;
    $('#upload_files_' + id).find('input[type=text][name!=cell_name]').each(function() {
        if ($(this).val() == "") {
            $(this).addClass("is-invalid");
            $(this).removeClass("is-valid");
            allFilled = false;
        } else {
            $(this).removeClass("is-invalid");
            $(this).addClass("is-valid");
        }
    })
    return allFilled;
}

function areFilesSelected(id) {
    return $("#user_files_" + id).prop("files").length > 0;
}

function checkIfUploadable(id) {
    if (areInputTextAllFilled(id) && isCellNameUnique(id) && areFilesSelected(id)) {
        $('#upload_button_' + id).prop("disabled", false);
        $('#upload_button_tooltip_' + id).prop("title", "Click to upload your files!");
    } else {
        $('#upload_button_' + id).prop("disabled", true);
        $('#upload_button_tooltip_' + id).prop("title", "Please fill all inputs!");
    }
}

var n_box = 0;
createUploadBox();
upload_title = "File upload";
upload_text = "<p> \
                For each cell whose activity you have recorded, you can upload one or more files.<br> \
                This will allow to compute mean feature values grouped by cell in the extraction process.<br> \
                The expected files contain recordings from &quotstep&quot stimulation experiments. \
                </p> \
                <br> \
                <p> \
                    Allowed formats are <b>.abf</b> and <b>.json</b>: \
                    <ul> \
                        <li> \
                            .abf files must be uploaded together with a metadata file containing information on the stimulus adopted during the recordings.<br> \
                            The metadata file must be named as the .abf file with the _metadata suffix (e.g. file1.abf -> file1_metadata.json).<br> \
                            Compulsory key-value pairs in the metadata file are:<br> \
                                &quotstimulus_end&quot, \
                                &quotstimulus_unit&quot, \
                                &quotstimulus_first_amplitude&quot, \
                                &quotstimulus_increment&quot, \
                                &quotsampling_rate_unit&quot, \
                                &quotsampling_rate&quot.<br>  \
                            You can download an example metadata file at this <a href='https://github.com/BlueBrain/BluePyEfe/tree/master/bluepyefe/tests/data_abf/cell01/97509008_metadata.json'> link </a> \
                        </li> \
                        <br> \
                        <li> \
                            .json files contain all the recordings and metadata in a single file.<br> \
                            Traces, stimulus start times and stimulus end times are grouped by keys indicating the stimulus amplitudes.<br> \
                            You can download an example file at this <a href='https://github.com/BlueBrain/BluePyEfe/blob/master/bluepyefe/tests/data_ibf_json/eg_json_data/traces/2021-01-23-test.json'> link </a>  \
                        </li> \
                    </ul> \
                </p>";

function createUploadBox() {
    n_box++;
    html_string = ' \
    <div class="border border-primary rounded-3 mx-auto my-4 p-4" id="upload_box_' + n_box + '"> \
        <form id="upload_files_' + n_box + '" method="POST" enctype="multipart/form-data" action="/efelg/upload_files" class="needs-validation" novalidate> \
            <fieldset id="fieldset_' + n_box + '"> \
                <div class="row"> \
                    <div class="col-lg-2 col-md-4 col-12"> \
                        <label>File type:</label> \
                    </div> \
                    <div class="col-lg-8 col-md-5 col-8"> \
                        <input id="abf_extension_' + n_box + '" type="radio" name="extension_' + n_box + '" value=".abf, .json" checked="checked"> \
                        <label for="abf_extension_' + n_box + '">abf</label> \
                        <input id="json_extension_' + n_box + '" type="radio" name="extension_' + n_box + '" value=".json" class="ms-3"> \
                        <label for="json_extension_' + n_box + '">json</label> \
                    </div> \
                    <div class="col-lg-2 col-md-3 col-4 text-center"> \
                        <i class="far fa-question-circle fa-lg" \
                            onclick="openInfo(upload_title, upload_text)"> \
                        </i> \
                        <i id="delete_button_' + n_box + '" class="far fa-times-circle fa-lg ms-2" \
                            onclick="removeUploadBox(this)"> \
                        </i> \
                    </div> \
                </div> \
                <div class="row mt-1"> \
                    <div class="col-xl-2 col-lg-2 col-md-4 col-sm-6"> \
                        <label for="cell_name_' + n_box + '" class="form-label mb-0">Cell name: </label> \
                    </div> \
                    <div class="col-xl-2 col-lg-3 col-md-8 col-sm-6"> \
                        <input id="cell_name_' + n_box + '" name="cell_name" type="text" value="unknown_' + n_box + '" \
                                class="form-control shadow-none d-inline" aria-describedby="cell_name_alert_' + n_box + '" required /> \
                    </div> \
                    <div class="col-xl-8 col-lg-7 col-md-12 col-sm-12"> \
                        <span id="cell_name_alert_' + n_box + '" class="small-text ms-3 d-none text-danger">Cell name must be unique and not empty!</span> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="contributors_' + n_box + '" class="form-label mb-0">Contributors: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="contributors_' + n_box + '" name="contributors" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="species_' + n_box + '" class="form-label mb-0">Species: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="species_' + n_box + '" name="species" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="structure_' + n_box + '" class="form-label mb-0">Structure: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="structure_' + n_box + '" name="structure" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="region_' + n_box + '" class="form-label mb-0">Region: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="region_' + n_box + '" name="region" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="type_' + n_box + '" class="form-label mb-0">Type: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="type_' + n_box + '" name="type" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="etype_' + n_box + '" class="form-label mb-0">EType: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="etype_' + n_box + '" name="etype" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                </div> \
                <div class="row mt-3"> \
                    <div class="col-lg-4 col-md-5 col-sm-6"> \
                        <label id="browse_label_' + n_box + '" class="btn btn-outline-primary w-100"> \
                            Browse files... \
                            <input type="file" \
                                name="user_files" \
                                id="user_files_' + n_box + '" \
                                accept=".abf, .json" \
                                style="display:none;" \
                                multiple /> \
                            <span class="custom-file-control"></span> \
                        </label> \
                        <span class="invalid-feedback d-none small-text text-danger ms-3">Please select files!</span> \
                    </div> \
                    <div class="col-lg-8 col-md-7 col-sm-6"> \
                        <span id="upload_button_tooltip_' + n_box + '" data-toggle="tooltip" data-placement="bottom" \
                                title="Please fill all inputs!"> \
                            <button type="submit" id="upload_button_' + n_box + '" class="btn btn-outline-primary w-100" disabled> \
                                Upload \
                            </button> \
                        </span> \
                    </div> \
                </div> \
            </fieldset> \
        </form> \
        <div id="charts_upload_' + n_box + '"></div> \
    </div>';
    $("#add_cell_button").parent(".text-end").before(html_string);

    $('input[type=radio][name=extension_' + n_box + ']').change(function () {
        var id = this.id.split("_");
        id = id[id.length - 1];
        $('#user_files_' + id).attr("accept", $(this).val());
    });

    $('#upload_files_' + n_box).find('input[type=text]').click(function () {
        if ($(this).val().toLowerCase().includes("unknown")) {
            $(this).val("");          
        }
    });

    $("#user_files_" + n_box).change(function (e) {
        selected_files = Object.values(e.target.files).map(x => x.name);
        var id = this.id.split("_");
        id = id[id.length - 1];
        checkIfUploadable(id);
    })

    $('#upload_files_' + n_box).find('input[type=text]').on("input click", function () {
        var id = this.id.split("_");
        id = id[id.length - 1];
        checkIfUploadable(id);
    });

    $("form#upload_files_" + n_box).submit(function (e) {
        e.preventDefault();
        var id = this.id.split("_");
        id = id[id.length - 1];
        if (checkUploadedFiles(id)) {
            writeMessage("wmd-first", "Uploading data");
            writeMessage("wmd-second", "Please wait ...");
            openMessageDiv("wait-message-div", "main-e-st-div");
            var formData = new FormData($(this)[0]);
            $.ajax({
                url: $(this).attr("action"),
                data: formData,
                type: 'POST',
                contentType: false,
                processData: false,
                success: function (name_dict) {
                    $('#fieldset_' + id).prop("disabled", true);
                    var loaded_filenames = name_dict.all_json_names;
                    var refused_filenames = [];
                    loaded_filenames = loaded_filenames.map(function (item) {
                        var splitted = item.split('____');
                        return splitted[splitted.length - 1] + '.abf'
                    })
                    selected_files.forEach(function (elem) {
                        if (loaded_filenames.indexOf(elem) == -1)
                            refused_filenames.push(elem);
                    })
                    /* MODIFIED
                    if (loaded_filenames.length == 0)
                        write_box('loadfile_box', 'loadfile_info', 'info', '<b>No file to be uploaded!</b>');
                    */
                    /*
                    if (refused_filenames.length > 0) {
                        openMessageInfo("REFUSED FILES", refused_filenames.join(", "));
                    }
                    */
                    /*
                        else {
                        //write_box('loadfile_box_rejected', 'loadfile_info_rejected', 'danger', '');
                        hideDiv("loadfile_box_rejected"); 
                    }
                    */
                    /*
                    if (loaded_filenames.length > 0){
                        writeMessage("wmd-first", "Uploading data");
                        writeMessage("wmd-second", "Please wait ...");
                        openMessageDiv("wait-message-div", "main-e-st-div");
                    }
                    */

                    //$('#charts_upload').empty();
                    all_json_names = name_dict['all_json_names'];
                    if (all_json_names.length == 0) {
                        closeMessageDiv("wait-message-div", "main-e-st-div");
                    }
                    
                    index = 'user_div_' + id;
                    var cell_info = all_json_names[0].split("____");
                    var cell_header = createCellHeader(cell_info.slice(0, 6).join(" > "), cell_info[5]);
                    cell_header.addClass("mt-4");
                    $('#charts_upload_' + id).append(cell_header);
                    cell_header.append('<div class="cell" id="' + index + '"></div>');

                    var cell_container = $('#' + index);
                    var counter = 0;
                    $.each(all_json_names, function (idx, elem) {
                        cell_container.append('<div id="' + elem + '"></div>');
                        $.getJSON('/efelg/get_data/' + elem, function (data) {
                            new TracePlot(elem, JSON.parse(data));
                            counter = counter + 1;
                            if (counter == all_json_names.length) {
                                closeMessageDiv("wait-message-div", "main-e-st-div");
                                //write_box('loadfile_box', 'loadfile_info', 'info', '<b>Uploaded files:</b>' + loaded_filenames.join(', '));
                            }
                        });
                    });
                }
            })
        }
    });
}

function removeUploadBox(remove_button) {
    $(remove_button).parents("#upload_box_" + remove_button.id.substring(remove_button.id.lastIndexOf("_") + 1)).remove();
}

function openInfo(title, text) {
    $("#info-title").html(title);
    $("#info-text").html(text);
    openMessageDiv("info-div", "main-e-st-div");
}

function openWarning(text) {
    $("#warning-text").html(text);
    openMessageDiv("warning-div", "main-e-st-div");
}

function resetFields() {
    contributor = null;
    specie = null;
    structure = null;
    region = null;
    type = null;
    etype = null;
    labelList = document.getElementsByTagName('label');
    for (var i = 0; i < labelList.length; i++) {
        if (labelList[i].classList.contains('withinTable')) {
            labelList[i].classList.toggle('activated', true);
            labelList[i].classList.remove('selected');
        }
    }
    document.getElementById('apply').disabled = true;
    $('#charts').empty();
}

function deactivateAllLabel() {
    labelList = document.getElementsByTagName('label');
    for (var i = 0; i < labelList.length; i++) {
        labelList[i].classList.remove('activated');
    }
}

function deselectAllLabel() {
    labelList = document.getElementsByTagName('label');
    for (var i = 0; i < labelList.length; i++) {
        labelList[i].classList.remove('activated', 'selected');
    }
}

function enableApplyButton() {
    if (contributor && specie && structure && region && type && etype) {
        document.getElementById('apply').disabled = false;
        if (contributor.includes("Allen")) {
            document.getElementById("citation-text").innerHTML =
                "<p>Use the following general citation format for any Allen Institute resource<br>© [[year of first publication]] Allen Institute for Brain Science. [Name of Allen Institute Resource]. Available from: [Resource URL]<br>or<br>© [[year of first publication]] Allen Institute for Cell Science. [Name of Allen Institute Resource]. Available from: [Resource URL]<br><br>Fetch data info through the <a href='http://celltypes.brain-map.org/data' target='_blank'>data portal</a> via the cell id</p><p>Please read <a href='https://alleninstitute.org/legal/citation-policy/' target='_blank'>Citation Policy</a> and <a href='https://alleninstitute.org/legal/terms-use/' target='_blank'>Terms of use</a></p>"
        } else {
            document.getElementById("citation-text").innerHTML = ""
        }
    } else {
        document.getElementById("citation-text").innerHTML = ""
        document.getElementById('apply').disabled = true;
    }
}

function selectLabel(label) {
    if (!label.classList.contains('activated')) {
        deselectAllLabel();
        contributor = null;
        specie = null;
        structure = null;
        region = null;
        type = null;
        etype = null;
    }
    label.classList.add('selected');
    table = label.parentNode.parentNode;
    deactivateAllLabel();
    switch (table.id) {
        case 'contributors':
            contributor = label.title;
            break;
        case 'species':
            specie = label.title;
            break;
        case 'structures':
            structure = label.title;
            break;
        case 'regions':
            region = label.title;
            break;
        case 'types':
            type = label.title;
            break;
        case 'etypes':
            etype = label.title;
    }
    lookingForContributorPath()
    autoSelectIfOne();
    moveActivatedLabelOnTop();
    scrollTableOnTop();
    enableApplyButton();
}

function autoSelectIfOne(table, elementId) {
    labelList = document.getElementsByClassName('activated');
    var contributorsList = [];
    var speciesList = [];
    var structuresList = [];
    var regionsList = [];
    var typesList = [];
    var etypesList = [];
    for (var i = 0; i < labelList.length; i++) {
        switch (labelList[i].getAttribute('for')) {
            case 'contributors':
                contributorsList.push(labelList[i]);
                break;
            case 'species':
                speciesList.push(labelList[i]);
                break;
            case 'structures':
                structuresList.push(labelList[i]);
                break;
            case 'regions':
                regionsList.push(labelList[i]);
                break;
            case 'types':
                typesList.push(labelList[i]);
                break;
            case 'etypes':
                etypesList.push(labelList[i]);
                break;
        }
    }
    if (contributorsList.length == 1) {
        contributorsList[0].classList.add('selected');
        contributor = contributorsList[0].title;
    }
    if (speciesList.length == 1) {
        speciesList[0].classList.add('selected');
        specie = speciesList[0].title;
    }
    if (structuresList.length == 1) {
        structuresList[0].classList.add('selected');
        structure = structuresList[0].title;
    }
    if (regionsList.length == 1) {
        regionsList[0].classList.add('selected');
        region = regionsList[0].title;
    }
    if (typesList.length == 1) {
        typesList[0].classList.add('selected');
        type = typesList[0].title;
    }
    if (etypesList.length == 1) {
        etypesList[0].classList.add('selected');
        etype = etypesList[0].title;
    }

}

function lookingForContributorPath() {
    if (!contributor) {
        var keys = Object.keys(json['Contributors']);
        for (var i = 0; i < keys.length; i++) {
            currentContributor = keys[i];
            lookingForSpeciePath(currentContributor);
        }
    } else {
        lookingForSpeciePath(contributor);
    }
}

function lookingForSpeciePath(cc) {
    if (!specie) {
        try {
            var keys = Object.keys(json['Contributors'][cc]);
            for (var i = 0; i < keys.length; i++) {
                currentSpecie = keys[i];
                lookingForStructurePath(cc, currentSpecie);
            }
        } catch (err) {
            return;
        }
    } else {
        lookingForStructurePath(cc, specie);
    }
}

function lookingForStructurePath(cc, cs) {
    if (!structure) {
        try {
            var keys = Object.keys(json['Contributors'][cc][cs]);
            for (var i = 0; i < keys.length; i++) {
                currentStructure = keys[i];
                lookingForRegionPath(cc, cs, currentStructure);
            }
        } catch (err) {
            return;
        }
    } else {
        lookingForRegionPath(cc, cs, structure);
    }
}

function lookingForRegionPath(cc, cs, css) {
    if (!region) {
        try {
            var keys = Object.keys(json['Contributors'][cc][cs][css]);
            for (var i = 0; i < keys.length; i++) {
                currentRegion = keys[i];
                lookingForTypePath(cc, cs, css, currentRegion);
            }
        } catch (err) {
            return;
        }
    } else {
        lookingForTypePath(cc, cs, css, region);
    }
}

function lookingForTypePath(cc, cs, css, cr) {
    if (!type) {
        try {
            var keys = Object.keys(json['Contributors'][cc][cs][css][cr]);
            for (var i = 0; i < keys.length; i++) {
                currentType = keys[i];
                lookingForEtypePath(cc, cs, css, cr, currentType);
            }
        } catch (err) {
            return;
        }
    } else {
        lookingForEtypePath(cc, cs, css, cr, type);
    }
}

function lookingForEtypePath(cc, cs, css, cr, ct) {
    try {
        if (!etype) {
            var keys = Object.keys(json['Contributors'][cc][cs][css][cr][ct]);
            for (var i = 0; i < keys.length; i++) {
                currentEtype = keys[i];
                activatePath(cc, cs, css, cr, ct, currentEtype);
            }
        } else {
            Object.keys(json['Contributors'][cc][cs][css][cr][ct][etype]);
            activatePath(cc, cs, css, cr, ct, etype);
        }
    } catch (err) {
        return;
    }
}

function activatePath(cc, cs, css, cr, ct, ce) {
    document.getElementById('contributors_' + cc).classList.toggle('activated', true);
    document.getElementById('species_' + cs).classList.toggle('activated', true);
    document.getElementById('structures_' + css).classList.toggle('activated', true);
    document.getElementById('regions_' + cr).classList.toggle('activated', true);
    document.getElementById('types_' + ct).classList.toggle('activated', true);
    document.getElementById('etypes_' + ce).classList.toggle('activated', true);
}

function moveActivatedLabelOnTop() {
    activatedLabels = document.getElementsByClassName('activated');
    for (var i = 0; i < activatedLabels.length; i++) {
        div = activatedLabels[i].parentNode;
        table = div.parentNode;
        table.insertBefore(div, table.childNodes[0]);
    }
}

function scrollTableOnTop() {
    var time = 1000;
    var offset = 0;
    $('#contributorsD').scroll();
    $('#contributorsD').animate({ scrollTop: offset }, time);
    $('#speciesD').scroll();
    $('#speciesD').animate({ scrollTop: offset }, time);
    $('#structureD').scroll();
    $('#structureD').animate({ scrollTop: offset }, time);
    $('#regionD').scroll();
    $('#regionD').animate({ scrollTop: offset }, time);
    $('#typeD').scroll();
    $('#typeD').animate({ scrollTop: offset }, time);
    $('#etypeD').scroll();
    $('#etypeD').animate({ scrollTop: offset }, time);
}
