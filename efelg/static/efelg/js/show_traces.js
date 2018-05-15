// show "check permissions" message
writeMessage("wmd-first", "Checking data permissions. This may take 30s to 50s");
writeMessage("wmd-second", "Please wait ...");
openMessageDiv("wait-message-div", "main-e-st-div");

//
function submitAll() {
    var $submitForm = $('#gonextform');
    $submitForm.submit(function(e){
        var data = serializeAll();
        var form = $('#gonextform')[0];
        form[1].value = JSON.stringify(data);
        list_len = Object.keys(data).length;
        e.preventDefault(); 
        if (list_len == 0) {
            openMessageDiv("e-st-warning-div", "main-e-st-div");
        } else {
            openMessageDiv("e-st-user-choice-div", "main-e-st-div");
            var list_div = document.getElementById("e-st-user-choice");
            while(list_div.firstChild){
                list_div.removeChild(list_div.firstChild);
            }
            for (var i = 0; i < list_len; i++){
                var crr_key = Object.keys(data)[i];
                var crr_stim = data[Object.keys(data)[i]]['stim'];
                var crr_div = document.createElement("DIV");
                if (i % 2 == 0) {
                    crr_div.style.backgroundColor = 'rgb(220, 220, 220)'; 
                } else {
                    crr_div.style.background = 'rgb(240, 240, 240)'; 
                }
                //
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
                sorted_stim_fin = sorted_stim.sort(function(a, b){return a-b});
                for (var j = 0; j < sorted_stim_fin.length; j++){
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

    for (var i=0; i < forms.length; i++) {
        var cell_name = $(forms[i]).parent()[0].id;
        var cboxes = $(forms[i]).find('[type="checkbox"]');
        var traces = [];
        for (var j=0; j < cboxes.length; j++) {
            if (cboxes[j].checked)
                traces.push(cboxes[j].name);
        }
        if (traces.length != 0) {
            var sampleObj = {};

            sampleObj['stim'] = traces;
            //sampleObj['vcorr'] = $(infos[i]).find('.vcorr').val()

            obj[cell_name] = sampleObj;
        }
    }
    return obj
}

//
function splitFilename(cellname){
    var filenameTokens = cellname.split('____');
    return filenameTokens
}

//
function acceptUserChoiceList() {
    var crr_div = document.getElementById("e-st-user-choice");
    while(crr_div.firstChild){
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
    while(crr_div.firstChild){
        crr_div.removeChild(crr_div.firstChild);
    }
}

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


//
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

var json;

var contributor = null;
var specie = null;
var structure = null;
var region = null;
var type = null;
var etype = null;

function checkIfElementExists(elementId, tableId) {
    childList = document.getElementById(tableId).childNodes;
    for (var i = 0; i < childList.length; i++) {
        if (elementId == childList[i].childNodes[0].id) {
            return true;
        }
    }
    return false;
}

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
    $('#charts').empty()
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
        if (contributor.includes("Allen")){
            document.getElementById("citation-text").innerHTML = 
                "<p>Use the following general citation format for any Allen Institute resource<br>© [[year of first publication]] Allen Institute for Brain Science. [Name of Allen Institute Resource]. Available from: [Resource URL]<br>or<br>© [[year of first publication]] Allen Institute for Cell Science. [Name of Allen Institute Resource]. Available from: [Resource URL]<br><br>Fetch data info through the <a href='http://celltypes.brain-map.org/data' target='_blank'>data portal</a> via the cell id</p>Please read <a href='https://alleninstitute.org/legal/citation-policy/' target='_blank'>Citation Policy</a> and <a href='https://alleninstitute.org/legal/terms-use/' target='_blank'>Terms of use</a>"
        }else{
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
        } catch(err) {
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
        } catch(err) {
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
        } catch(err) {
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
        } catch(err) {
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
    } catch(err) {
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
    $('#contributorsD').animate({scrollTop: offset}, time);
    $('#speciesD').scroll();
    $('#speciesD').animate({scrollTop: offset}, time);
    $('#structureD').scroll();
    $('#structureD').animate({scrollTop: offset}, time);
    $('#regionD').scroll();
    $('#regionD').animate({scrollTop: offset}, time);
    $('#typeD').scroll();
    $('#typeD').animate({scrollTop: offset}, time);
    $('#etypeD').scroll();
    $('#etypeD').animate({scrollTop: offset}, time);
}
