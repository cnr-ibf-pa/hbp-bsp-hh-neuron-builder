// show "check permissions" message
writeMessage("wmd-first", "Checking data permissions");
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
            console.log(trace_len);
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
        cells_tree = {}
        if (data.length == 0) {

        }
        $.each(data, function(index, elem) {
            params = elem.split('____');
            branch = cells_tree;
            for (var i=0; i<6; i++) {
                if (!(params[i] in branch) && i == 5)
                    branch[params[i]] = [];
                else if (!(params[i] in branch) && i != 5)
                    branch[params[i]] = {};

                if (i == 5)
                    branch[params[i]].push(elem);
                branch = branch[params[i]];
            }
        })

        function enable_dropdown(el, tree) {
            $(el).prop("disabled", false)
                $(el).empty()
                $(el).append('<option>--</option>')

                $.each(Object.keys(tree), function(index, elem) {
                    var n = ' (' + Object.keys(tree[elem]).length + ')';
                            $(el).append('<option value="' + elem + '">' + elem + n + '</option>');
                            });

                    if ($(el).next('select').length == 0) {
                        $(el).on('change', function(ev) {
                            openMessageDiv("wait-message-div", "main-e-st-div");
                            writeMessage("wmd-first", "Loading traces");
                            writeMessage("wmd-second", "Please wait ...");
                            $(el).prop("disabled", true);
                            var keys_len = Object.keys(tree[ev.target.value]).length;
                            var keys_counter = keys_len;
                            $.each(tree[ev.target.value], function(index, elem) {
                                var name_split = splitFilename(elem[0]);
                                var cell_name = name_split[0] + ' > ' + name_split[1] + ' > ' + name_split[2] + ' >     ' + name_split[3] + ' > ' + name_split[4] + ' > ' + name_split[5];
                                var cell_container = $('<div class="cell panel panel-default" />');
                                cell_container.append('<div class="panel-heading cell-heading"> \
                                        <a href="#">Cell: ' + cell_name + '</a>	\
                                        <br><br> \
                                        <button class="cell_selall btn-link pull-left cell-button">Select all traces</button> \
                                        <button class="cell_dselall btn-link pull-left cell-button">Deselect all traces</button> \
                                        <button class="cell_invsel btn-link pull-left cell-button">Invert selection</button> \
                                        </div>');
                                cell_container.append('<div id="' + index + '"></div>');
                                $('#charts').append(cell_container);

                                $('#charts').find('.cell:last-of-type a').click(function(){
                                    $('#' + index).toggle();
                                    return false
                                })

                                $('#charts').find('.cell:last-of-type .cell_selall').click(function(){
                                    $(this).parents('.cell').find('.selall').click();
                                })

                                $('#charts').find('.cell:last-of-type .cell_invsel').click(function(){
                                    $(this).parents('.cell').find('.invsel').click();
                                })

                                $('#charts').find('.cell:last-of-type .cell_dselall').click(function(){
                                    $(this).parents('.cell').find('.dselall').click();
                                })

                                var elem_counter = 0;
                                var elem_len = elem.length;
                                $.each(elem, function(i, e) {
                                    $('#' + index).append('<div id="' + e + '"></div>');
                                    $.getJSON('/efelg/get_data/' + e, function(data) {
                                        elem_counter++;
                                        writeMessage("wmd-first", "Cell " + (keys_len - keys_counter + 1).toString()
                                                + " of " + keys_len.toString() + 
                                                ". Loading traces for file " + 
                                                elem_counter.toString() + 
                                                " of " + elem_len.toString());
                                        new TracePlot(e, JSON.parse(data));
                                        if (elem_counter == elem_len){
                                            keys_counter--;
                                            if (keys_counter == 0) {
                                                closeMessageDiv("wait-message-div", "main-e-st-div");
                                                writeMessage("wmd-first", "");
                                                writeMessage("wmd-second", "");
                                            }
                                        }
                                    })
                                })
                            })
                        })                
                    } else {

                        $(el).on('change', function(ev) {
                            $(el).prop("disabled", true);
                            enable_dropdown($(el).next('select').eq(0), tree[ev.target.value]);
                        })
                    }
        }


        $('.ctrl_box > select').prop("disabled", true);
        enable_dropdown('#drop_species', cells_tree);
    })
    .done(function() {
        closeMessageDiv("wait-message-div", "main-e-st-div");
    });
});
