
$(document).ready(function(){

    var box_id = 'loadfile_box'
    var label_id = 'loadfile_info'
    
    $('#loadfile_icon').hide()
    $('#' + box_id).hide()
    
    var selected_files = []

    function write_box(type, message) {
        $('#' + box_id).show()
        $('#' + box_id).removeClass()
        $('#' + box_id).addClass('panel panel-' + type)
        $('#' + label_id).html(message)
    }

    $("#user_files").change(function(e) {
        var string = '<b>Files selected:</b> '
        var names = Object.values(e.target.files)
        
        selected_files = names.map(function(item) {
            return item.name
        })
        
        string += selected_files.join(', ')
        write_box('info', string)
    })


    $("form#upload_files").submit(plotTraces, function(e) {
            $('#loadfile_icon').show()
            write_box('info', '<b>Loading files...</b>')
        
            var formData = new FormData($(this)[0]);
            $.ajax({
                url: $(this).attr("action"),
                data: formData,
                type: 'POST',
                contentType: false,
                processData: false,
                success: function(name_dict) {
                    var loaded_filenames = name_dict.all_json_names
                    var refused_filenames = []
                    loaded_filenames = loaded_filenames.map(function(item) {
                        var splitted = item.split('_')
                        return splitted[splitted.length - 1] + '.abf'
                    })
                    selected_files.forEach(function(elem) {
                        if (loaded_filenames.indexOf(elem) == -1)
                            refused_filenames.push(elem)
                    })
                    
                    $('#loadfile_icon').hide()
                    
                    if (refused_filenames.length) 
                        write_box('danger', '<b>Files rejected:</b> ' + refused_filenames.join(', '))
                    else
                        write_box('success', '<b>Loading completed!</b>')
                
                    $('#charts_upload').empty()
                    all_json_names = name_dict['all_json_names'];
                    index = 'user_div' 
                    $('#charts_upload').append('<div class="cell panel panel-default" id="' + index  + '"></div>')
                    $.each(all_json_names, function(idx, elem) {
                        $('#' + index).append('<div id="' + elem + '"></div>')
                        plotTraces(elem , elem)
                    })
                }
            });
            e.preventDefault();
            //return false
    });



    /*		resetAll()

    function resetAll() {
        */  	


        $('#charts').empty()

        $.getJSON('/efelg/get_list', function(data) {
            cells_tree = {}
            $.each(data, function(index, elem) {
                params = elem.split('_')
                branch = cells_tree
                for (var i=0; i<6; i++) {
                    if (!(params[i] in branch) && i == 5)
                    branch[params[i]] = []
                    else if (!(params[i] in branch) && i != 5)
                    branch[params[i]] = {}

                    if (i == 5)
                    branch[params[i]].push(elem)

                    branch = branch[params[i]]
                }
            })

            function enable_dropdown(el, tree) {
                $(el).prop("disabled", false)
                $(el).empty()
                $(el).append('<option>--</option>')

                $.each(Object.keys(tree), function(index, elem) {
                    var n = ' (' + Object.keys(tree[elem]).length + ')'
                    $(el).append('<option value="' + elem + '">' + elem + n + '</option>')
                })

                if ($(el).next('select').length == 0) {
                    $(el).on('change', function(ev) {
                        $(el).prop("disabled", true)

                        $.each(tree[ev.target.value], function(index, elem) {
                            $('#charts').append('<div class="cell panel panel-default" id="' + index + '"></div>')

                            $.each(elem, function(i, e) {
                                $('#' + index).append('<div id="' + e + '"></div>')
                                plotTraces(e, e)
                            })
                        })
                    })                
                    } else {

                    $(el).on('change', function(ev) {
                        $(el).prop("disabled", true)

                        enable_dropdown($(el).next('select').eq(0), tree[ev.target.value])
                    })
                }
            }


            $('.ctrl_box > select').prop("disabled", true)

            enable_dropdown('#drop_species', cells_tree)
        })
        //	}

    function plotTraces(container_id, cellname) {
        var SHOW_FADED = 0.15
        var SHOW_CHECK = 0.65
        var SHOW_HOVER = 1.0

        $('#' + container_id).empty()

        $.getJSON('/efelg/get_data/' + cellname, function(data) {
            data = JSON.parse(data)
    crr_md5 = data['md5']
    if ($('#info_' + crr_md5).length > 0){
        crr_md5 = crr_md5 + 'crr'
    }
            info_container = 'info_' + crr_md5 
            form_container = 'form_' + crr_md5
            plot_container = 'plot_' + crr_md5
            fnTok = cellname.split('_')
            displayStrJoin = fnTok.join(' -> ')
            $('#' + container_id).append('<div id="' + info_container + '" class="panel-heading fn-container"></div')
                $('#' + info_container).append('<span></span>').text('Cell properties: ' + displayStrJoin)
                $('#' + info_container).append('<br><br>')
                $('#' + info_container).append('<button class="selall btn btn-link btn-default">Select all</button>')
                $('#' + info_container).append('<button class="dselall btn btn-link btn-default">Deselect all</button>')
                $('#' + info_container).append('<button class="invsel btn btn-default btn-link">Invert selection</button>')

                $('#' + container_id).append('<form id="' + form_container + '"></form')
                    $('#' + form_container).hide()

                    $('#' + container_id).append('<div id="' + plot_container + '"></div')

                        plotdata = []
                        $.each(data['traces'], function(key, trace) {
                            $('#' + form_container).append('<input type="checkbox" name="' + key + '">')

                            var newTrace = {
                                y: trace,
                                name: key + ' ' + data['amp_unit'],
                                mode: 'lines',
                                hoverinfo: 'none',
                                opacity: SHOW_FADED
                            }
                            plotdata.push(newTrace)
                        });

                        plotdata.sort(function(a, b) {
                            a = parseFloat(a.name)
                            b = parseFloat(b.name)

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
                                y: 1.2,
                            },
                            margin: {l: 40, b: 60, t: 0} 
                        }

                        var n_traces = plotdata.length
                        var opacities = new Array(n_traces).fill(SHOW_FADED)
                        var opacity_before_hover = null

                        function requestUpdate(plt_name) {                 
                            var update = {
                                opacity: opacities
                            }

                            Plotly.restyle(plt_name, update).then(manageLegend)

                            legend = Plotly.d3.select('#' + plt_name + ' g.legend')
                            legend.selectAll('.traces').each(function(d, i) {
                                Plotly.d3.select(this).style('opacity', opacities[i] + 0.4)
                            })
                        }

                        Plotly.newPlot(plot_container, plotdata, layout, {displayModeBar: false}).then(manageLegend)
                        requestUpdate(plot_container)

                        document.getElementById(plot_container).on('plotly_relayout', function(ev) {
                            var plot_id = $('#' + container_id + ' > div[id^="plot_"]')[0].id
                            requestUpdate(plot_id)
                        })

                        document.querySelector('#' + container_id + ' .selall').onclick = function(ev) {
                            var plot_id = $('#' + container_id + ' > div[id^="plot_"]')[0].id
                            console.log(container_id)

                            opacities.fill(SHOW_CHECK)
                            $('#' + container_id + ' form > input').prop('checked', true)

                            requestUpdate(plot_id)
                        }

                        document.querySelector('#' + container_id + ' .dselall').onclick = function(ev) {
                            var plot_id = $('#' + container_id + ' > div[id^="plot_"]')[0].id

                            opacities.fill(SHOW_FADED)
                            $('#' + container_id + ' form > input').prop('checked', false)

                            requestUpdate(plot_id)
                        }

                        document.querySelector('#' + container_id + ' .invsel').onclick = function(ev) {
                            var plot_id = $('#' + container_id + ' > div[id^="plot_"]')[0].id

                            for (var i = 0; i < opacities.length; i++) {
                                opacities[i] = opacities[i] == SHOW_FADED ? SHOW_CHECK : SHOW_FADED

                                var cb = $('#' + container_id + ' form > input')[i]
                                cb.checked = ! cb.checked
                            }

                            requestUpdate(plot_id)
                        }

                        function manageLegend(plt_elem) {
                            legend = Plotly.d3.select('#' + plt_elem.id + ' g.legend')
                            elems = legend.selectAll('.traces rect')

                            function savePrevious(d) {
                                var i = d[0].trace.index

                                opacity_before_hover = opacities[i]

                                opacities[i] = SHOW_HOVER

                                requestUpdate(plt_elem.id)
                            }

                            function restorePrevious(d) {
                                var i = d[0].trace.index

                                opacities[i] = opacity_before_hover

                                requestUpdate(plt_elem.id)
                            }

                            function setOpacity(d) {
                                var form_name = 'form_' + plt_elem.id.slice('plot_'.length)
                                var check_name = 'input[name^="' + d[0].trace.name.slice(0, -3) + '"]'

                                if (opacity_before_hover == SHOW_FADED) {
                                    $('#' + form_name + ' > ' + check_name )[0].checked = true
                                    opacity_before_hover = SHOW_CHECK
                                    } else {
                                    $('#' + form_name + ' > ' + check_name)[0].checked = false
                                    opacity_before_hover = SHOW_FADED
                                }
                            }

                            elems.each(function() {
                                Plotly.d3.select(this).on('click', setOpacity)
                                Plotly.d3.select(this).on('mouseenter', savePrevious)
                                Plotly.d3.select(this).on('mouseleave', restorePrevious)
                            })

                        }
                    })
                }
});


function submitAll() {
    var data = serializeAll()
    var form = $('#gonextform')[0]

    form[0].value = JSON.stringify(data)
    form.submit()
}

function serializeAll() {
    var obj = {}
    var forms = $('form[id^="form_"]')

    for (var i=0; i < forms.length; i++) {
        var cell_name = $(forms[i]).parent()[0].id
        var traces = []
        for (var j=0; j < forms[i].length; j++) {
            if ((forms[i][j].checked))
            traces.push(forms[i][j].name)
        }

        if (traces.length != 0)
        obj[cell_name] = traces
    }

    return obj
}

function splitFilename(cellname){
    var filenameTokens = cellname.split('_');
    return filenameTokens
}
