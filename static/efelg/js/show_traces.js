// show "check permissions" message
//writeMessage("wmd-first", "Checking data permissions. This may take 30s to 50s");
writeMessage("wmd-first", "Loading");
writeMessage("wmd-second", "Please wait...");
openMessageDiv("wait-message-div", "main-e-st-div");

var contributor = null;
var specie = null;
var structure = null;
var region = null;
var type = null;
var etype = null;

var menus = []
var i_box = 0;
var selected_files = [];
var json;

addParametersMenuListener();
createUploadBox();
onChangeEventsValue();


//
function addParametersMenuListener() {
    menus.push($('#parameters_menu'));
    $(window).resize(() => menus.forEach(menu => {
        if (menu.css('maxHeight') != "0px") {
            menu.css({ maxHeight: menu[0].scrollHeight + "px" });
        }
    }));
}


//
function submitAll() {

    function serializeAll() {
        var obj = {};
        $('div.input_box').each((i, inputBox) => {
            var inputBox = $(inputBox);
            var cell_name = inputBox.parent()[0].id;
            var traces = [];
            inputBox.find('[type="checkbox"]').each((i, checkbox) => {
                if (checkbox.checked) {
                    var name = checkbox.name
                    traces.push(name.substring(0, name.indexOf(" ")));
                }
            });
            if (traces.length != 0) {
                var sampleObj = {};
                sampleObj['stim'] = traces;
                sampleObj['v_corr'] = inputBox.find('.vcorr-value').val();
                obj[cell_name] = sampleObj;
            }
        });
        return obj
    }

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
                var crr_div = document.createElement("div");
                if (i % 2 == 0) {
                    crr_div.style.backgroundColor = 'rgb(220, 220, 220)';
                } else {
                    crr_div.style.background = 'rgb(240, 240, 240)';
                }
                var cellname_span = document.createElement("span");
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
                crr_div.appendChild(document.createElement("br"));
                var stim_span = document.createElement("span");
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
$(document).ready(function () {

    function checkIfElementExists(elementId, tableId) {
        childList = document.getElementById(tableId).childNodes;
        for (var i = 0; i < childList.length; i++) {
            if (elementId == childList[i].childNodes[0].id) {
                return true;
            }
        }
        return false;
    }

    window.scrollTo(0, 0);

    $('#charts').empty();
    $.getJSON('/efelg/get_list', function (data) {
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


//
function applySelection() {
    $('#charts').empty();
    plotCells(Object.keys(json['Contributors'][contributor][specie][structure][region][type][etype]), false, null);
}


//
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


//
function toggleParametersMenu(button) {
    toggleMenu(button, '#parameters_menu');
    var menu = $('#parameters_menu');
    if (menu.css('overflow') == 'visible') {
        menu.css({ overflow: 'hidden' })
    } else {
        menu.css({ overflow: 'visible' })
    }
}


//
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


//
function selectAllCheckboxes(selectAll) {
    if ($(selectAll).prop("checked")) {
        $('input[type=checkbox][name=mean_features_no_zeros]').each(function () {
            $(this).prop("checked", true);
        });
    }
}


//
function updateVoltageCorrection(button, correction) {
    updateValue(button, correction);
    plotVoltageCorrection($(button).parents(".input_box").next()[0].id, correction);
}


//
function updateValue(button, value) {
    var input = $(button).siblings('input[type=number]');
    input.val((parseFloat(input.val()) + parseFloat(value)).toFixed(0));
}


//
function updateEventsValue(button, value) {
    updateValue(button, value);
    checkEventsValue();
}


//
function checkEventsValue() {
    if ($('#events_value').val() < 5) {
        $('#events_value').val(5);
    }
}


//
function onChangeEventsValue() {
    $('#events_value').on("change", function () {
        if ($(this).val() > 5) {
            updateValue(this, value);
        }
        checkEventsValue();
    });
}


//
function openInfoPanel(title, text) {
    closeMessageDiv('warning-div', 'main-e-st-div');
    $("#info-title").html(title);
    $("#info-text").html(text);
    openMessageDiv("info-div", "main-e-st-div");
}


//
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
            <span class="text-decoration-underline clickable" onclick="openInfoPanel(uploadTitle, uploadText)">link</span>');
        return false;
    } else if (missing_files.length > 0) {
        openWarning('Missing file:<br>You should submit ' + missing_files.join(', ') + " as well!");
        return false;
    }
    return true;
}



//
function checkIfUploadable(id) {

    //
    function areInputTextAllFilled(id) {
        var areAllFilled = true;
        $('#upload_files_' + id).find('input[type=text][name!=cell_name]').each(function () {
            if ($(this).val() == "") {
                $(this).addClass("is-invalid");
                $(this).removeClass("is-valid");
                areAllFilled = false;
                return;
            } else {
                $(this).removeClass("is-invalid");
                $(this).addClass("is-valid");
            }
        })
        return areAllFilled;
    }


    //
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


    //
    function areFilesSelected(id) {
        return $("#user_files_" + id).prop("files").length > 0;
    }


    if (areInputTextAllFilled(id) && isCellNameUnique(id) && areFilesSelected(id)) {
        $('#upload_button_' + id).prop("disabled", false);
        $('#upload_button_tooltip_' + id).prop("title", "Click to upload your files!");
    } else {
        $('#upload_button_' + id).prop("disabled", true);
        $('#upload_button_tooltip_' + id).prop("title", "Please fill all inputs!");
    }
}


//
function createUploadBox() {
    i_box++;
    html_string = ' \
    <div class="border border-primary rounded-3 mx-auto my-4 p-4" id="upload_box_' + i_box + '"> \
        <form id="upload_files_' + i_box + '" method="POST" enctype="multipart/form-data" action="/efelg/upload_files" class="needs-validation" novalidate> \
            <fieldset id="fieldset_' + i_box + '"> \
                <div class="row"> \
                    <div class="col-lg-2 col-md-4 col-12"> \
                        <label>File type:</label> \
                    </div> \
                    <div class="col-lg-8 col-md-5 col-8"> \
                        <input id="abf_extension_' + i_box + '" type="radio" name="extension_' + i_box + '" value=".abf, .json" checked="checked"> \
                        <label for="abf_extension_' + i_box + '">abf</label> \
                        <input id="json_extension_' + i_box + '" type="radio" name="extension_' + i_box + '" value=".json" class="ms-3"> \
                        <label for="json_extension_' + i_box + '">json</label> \
                    </div> \
                    <div class="col-lg-2 col-md-3 col-4 text-end"> \
                        <i class="far fa-question-circle fa-lg" \
                            onclick="openInfoPanel(uploadTitle, uploadText)"> \
                        </i> \
                        <i id="delete_button_' + i_box + '" class="far fa-times-circle fa-lg ms-2" \
                            onclick="removeUploadBox(this)"> \
                        </i> \
                    </div> \
                </div> \
                <div class="row mt-1"> \
                    <div class="col-xl-2 col-lg-2 col-md-4 col-sm-6"> \
                        <label for="cell_name_' + i_box + '" class="form-label mb-0">Cell name: </label> \
                    </div> \
                    <div class="col-xl-2 col-lg-3 col-md-8 col-sm-6"> \
                        <input id="cell_name_' + i_box + '" name="cell_name" type="text" value="unknown_' + i_box + '" \
                                class="form-control shadow-none d-inline" aria-describedby="cell_name_alert_' + i_box + '" required /> \
                    </div> \
                    <div class="col-xl-8 col-lg-7 col-md-12 col-sm-12"> \
                        <span id="cell_name_alert_' + i_box + '" class="small-text ms-3 d-none text-danger">Cell name must be unique and not empty!</span> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="contributors_' + i_box + '" class="form-label mb-0">Contributors: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="contributors_' + i_box + '" name="contributors" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="species_' + i_box + '" class="form-label mb-0">Species: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="species_' + i_box + '" name="species" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="structure_' + i_box + '" class="form-label mb-0">Structure: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="structure_' + i_box + '" name="structure" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="region_' + i_box + '" class="form-label mb-0">Region: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="region_' + i_box + '" name="region" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="type_' + i_box + '" class="form-label mb-0">Type: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="type_' + i_box + '" name="type" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                    <div class="col-lg-2 col-md-4 col-sm-6"> \
                        <label for="etype_' + i_box + '" class="form-label mb-0">EType: </label> \
                    </div> \
                    <div class="col-lg-4 col-md-8 col-sm-6"> \
                        <input id="etype_' + i_box + '" name="etype" type="text" value="unknown" class="form-control shadow-none d-inline" required /> \
                    </div> \
                </div> \
                <div class="row mt-3"> \
                    <div class="col-lg-4 col-md-5 col-sm-6"> \
                        <label id="browse_label_' + i_box + '" class="btn btn-outline-primary w-100"> \
                            Browse files... \
                            <input type="file" \
                                name="user_files" \
                                id="user_files_' + i_box + '" \
                                accept=".abf, .json" \
                                style="display:none;" \
                                multiple /> \
                            <span class="custom-file-control"></span> \
                        </label> \
                        <span class="invalid-feedback d-none small-text text-danger ms-3">Please select files!</span> \
                    </div> \
                    <div class="col-lg-8 col-md-7 col-sm-6"> \
                        <span id="upload_button_tooltip_' + i_box + '" data-toggle="tooltip" data-placement="bottom" \
                                title="Please fill all inputs!"> \
                            <button type="submit" id="upload_button_' + i_box + '" class="btn btn-outline-primary w-100" disabled> \
                                Upload \
                            </button> \
                        </span> \
                    </div> \
                </div> \
            </fieldset> \
        </form> \
        <div id="charts_upload_' + i_box + '"></div> \
    </div>';
    $("#add_cell_button").parent(".text-end").before(html_string);

    $('input[type=radio][name=extension_' + i_box + ']').change(function () {
        var id = this.id.split("_");
        id = id[id.length - 1];
        $('#user_files_' + id).attr("accept", $(this).val());
    });

    $('#upload_files_' + i_box).find('input[type=text]').click(function () {
        if ($(this).val().toLowerCase().includes("unknown")) {
            $(this).val("");
        }
    });

    $("#user_files_" + i_box).change(function (e) {
        selected_files = Object.values(e.target.files).map(x => x.name);
        var id = this.id.split("_");
        id = id[id.length - 1];
        checkIfUploadable(id);
        var files = $("#user_files_" + id).prop("files")
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            var splitted_name = file["name"].split(".");
            var ext = splitted_name[splitted_name.length - 1];
            if (ext == "json") {
                var read = new FileReader();
                read.readAsBinaryString(file);
                read.onloadend = function () {
                    var data = JSON.parse(read.result);
                    var cell_name = $("#cell_name_" + id);
                    var structure = $("#structure_" + id);
                    var species = $("#species_" + id);
                    var region = $("#region_" + id);
                    var contributors = $("#contributors_" + id)
                    var type = $("#type_" + id);
                    var etype = $("#etype_" + id);
                    if (cell_name.val().includes("unknown")) {
                        if ("name" in data) {
                            cell_name.val(data["name"].toLowerCase());
                        } else if ("cell_id" in data) {
                            cell_name.val(data["cell_id"].toLowerCase());
                        }
                    }
                    if (structure.val().includes("unknown")) {
                        if ("area" in data) {
                            structure.val(data["area"].toLowerCase());
                        } else if ("brain_structure" in data) {
                            structure.val(data["brain_structure"].toLowerCase());
                        }
                    }
                    if (species.val().includes("unknown")) {
                        if ("species" in data) {
                            species.val(data["species"].toLowerCase());
                        } else if ("animal_species" in data) {
                            species.val(data["animal_species"].toLowerCase());
                        }
                    }
                    if (region.val().includes("unknown")) {
                        if ("region" in data) {
                            region.val(data["region"].toLowerCase());
                        } else if ("cell_soma_location" in data) {
                            region.val(data["cell_soma_location"].toLowerCase());
                        }
                    }
                    if (contributors.val().includes("unknown")) {
                        if ("contributors_affiliations" in data) {
                            contributors.val(data["contributors_affiliations"].toLowerCase());
                        } else if ("contributors" in data) {
                            contributors.val(data["contributors"]["name"].toLowerCase());
                        }
                    }
                    if (type.val().includes("unknown")) {
                        if ("type" in data) {
                            type.val(data["type"].toLowerCase());
                        }
                    }
                    if (etype.val().includes("unknown")) {
                        if ("etype" in data) {
                            etype.val(data["etype"].toLowerCase());
                        }
                    }
                }
            }
        }
    });

    $('#upload_files_' + i_box).find('input[type=text]').on("input click", function () {
        var id = this.id.split("_");
        id = id[id.length - 1];
        checkIfUploadable(id);
    });

    $("form#upload_files_" + i_box).submit(function (e) {
        e.preventDefault();
        var id = this.id.split("_");
        id = id[id.length - 1];
        if (checkUploadedFiles(id)) {
            writeMessage("wmd-first", "Loading traces");
            writeMessage("wmd-second", "Please wait...");
            openMessageDiv("wait-message-div", "main-e-st-div");
            var inputs = $(this).find('input[type=text]');
            for (var i = 0; i < inputs.length; i++) {
                $(inputs[i]).val($(inputs[i]).val().replaceAll(" ", "_"));
            }
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

                    all_json_names = name_dict['all_json_names'];
                    if (all_json_names.length == 0) {
                        closeMessageDiv("wait-message-div", "main-e-st-div");
                    }

                    plotCells(all_json_names, true, id);
                }
            })
        }
    });
}


//
function removeUploadBox(remove_button) {
    $(remove_button).parents("#upload_box_" + remove_button.id.substring(remove_button.id.lastIndexOf("_") + 1)).remove();
}


//
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


var parametersInfo = ' \
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
    </p> \
';

uploadTitle = "File upload";

uploadText = " \
    <p> \
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
    </p> \
";
