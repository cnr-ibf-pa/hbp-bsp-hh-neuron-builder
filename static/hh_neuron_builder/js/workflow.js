var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;

$(window).bind("pageshow", function() { 
    checkConditions();
    closeParameterDiv();
    closeFetchParamDiv();
    closeUploadDiv();
    closePleaseWaitDiv();
    closeJobInfoDiv();
});

$( "#mainDiv" ).focus(function() {
    //checkConditions();
});

$(document).ready(function(){
    // check conditions on function activation
    //checkConditions();

    $('#job-list-div').on('click', '.down-job-btn', function(){
        downloadJob(this.id);
    });

    $('#job-list-body').on('click', '.down-job-btn', function(){
        downloadJob(this.id);
    });

    $('#opt-res-file').on('change', function(){
        $('#upload-opt-res-btn').prop('disabled', !$('#opt-res-file').val());
    });

    // manage form for submitting run parameters
    var $formrunparam = $('#submitRunParam');
    $formrunparam.submit(function(e){
        e.preventDefault();
        $.post('/hh-neuron-builder/submit-run-param/' + req_pattern + '/', $(this).serialize(), function(response){
            if (response['response'] == "KO"){
                openErrorDiv("Username and/or password are wrong");
                checkConditions();
            } else {
                checkConditions();
                closeParameterDiv();
            } 
        },'json');
        return false;
    });

    // manage form for submitting fetch parameters
    var $formfetchparam = $('#submitFetchParam');
    $formfetchparam.submit(function(e){
        e.preventDefault();
        $.post('/hh-neuron-builder/submit-fetch-param/' + req_pattern + '/', $(this).serialize(), function(response){
            if (response['response'] == "KO"){
                openErrorDiv(response['message']);
                checkConditions();
            } else {
                closeFetchParamDiv();
                displayJobInfoDiv();
                checkConditions();
            } 
        },'json');
        return false;
    });


    // manage form to upload simulation zip file 
    var $uploadFileForm = $('#uploadFileForm');
    $uploadFileForm.submit(function(e){
        closeUploadDiv();
        displayPleaseWaitDiv();
        changeMsgPleaseWaitDiv("Uploading file to the server");
        var uploadFormData = new FormData($(this)[0]);
        $.ajax({
            url: $(this).attr("action"),
            data:uploadFormData,
            type: 'POST',
            contentType: false,
            processData: false,
            async: false,
            success: function(resp){
                if (resp["response"]=="KO"){
                    openErrorDiv(resp["message"]);
                } else {
                    checkConditions();
                }
            },  
        });
        e.preventDefault();
        closePleaseWaitDiv();
    });

    // assign functions to buttons' click
    
    // manage top bar buttons
    document.getElementById("wf-btn-home").onclick = goHome;
    document.getElementById("wf-btn-clone-wf").onclick = cloneWorkflow;
    document.getElementById("wf-btn-save").onclick = saveWorkflow;

    // manage optimization settings buttons action
    document.getElementById("opt-set-btn").onclick = openParameterDiv;
    document.getElementById("cancel-param-btn").onclick = closeParameterDiv;
    document.getElementById("down-opt-set-btn").onclick = downloadLocalOptSet;

    // manage simulation run buttons
    document.getElementById("run-sim-btn").onclick = inSilicoPage;
    document.getElementById("down-sim-btn").onclick = downloadLocalSim;
    document.getElementById("down-opt-btn").onclick = downloadLocalOpt;

    // manage extract features button
    document.getElementById("feat-efel-btn").onclick = efelPage;

    // manage feature upload buttons
    document.getElementById("feat-up-btn").onclick = featUploadButton;

    // manage choose optimization settings button
    document.getElementById("opt-db-hpc-btn").onclick = chooseOptModel;

    // manage upload optimization settings button
    document.getElementById("opt-up-btn").onclick = displayOptSetUploadDiv;
    document.getElementById("cancel-upload-file-btn").onclick = closeUploadDiv;

    // manage buttons for insertion of fetch parameters
    document.getElementById("opt-fetch-btn").onclick = displayFetchParamDiv;
    document.getElementById("cancel-param-fetch-btn").onclick = closeFetchParamDiv;

    // manage optimization results upload button
    document.getElementById("opt-res-up-btn").onclick = displayOptResUploadDiv;

    // manage button for deleting features
    document.getElementById("del-feat-btn").onclick = deleteFeatureFiles;
    document.getElementById("down-feat-btn").onclick = downloadLocalFeat;

    // manage button for deleting optimization setting files
    document.getElementById("del-opt").onclick = deleteOptFiles;

    // manage button for deleting optimization setting files
    document.getElementById("del-sim-btn").onclick = deleteSimFiles;

    // manage button for running optimization
    document.getElementById("launch-opt-btn").onclick = runOptimization;

    // manage buttons for downloading jobs
    document.getElementById("cancel-job-list-btn").onclick = closeJobInfoDiv;

    // manage error message ok button
    document.getElementById("ok-error-div-btn").onclick = closeErrorDiv;
    //
});


// serve embedded-efel-gui page
function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/";

}

// serve embedded-naas page
function inSilicoPage() {
    $.getJSON("/hh-neuron-builder/upload-to-naas/" + req_pattern, function(uploaddata){
        $.getJSON("/hh-neuron-builder/model-loaded-flag/" + req_pattern, function(data){
            var o = data["response"];
            if (o == "KO"){
                window.location.href = "";
            } else {
                window.location.href = "/hh-neuron-builder/embedded-naas/" + req_pattern + "/";
            } 
        });

    });
}

// serve choose-opt-model page
function chooseOptModel() {
    window.location.href = "/hh-neuron-builder/choose-opt-model"; 
}

// reload current page
function reloadCurrentPage() {
    window.location.href = "";
}

// open side div for optimization run parameter settings
function openParameterDiv() {
    document.getElementById("overlaywrapper").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}


// open side div for optimization run parameter settings
function openErrorDiv(message) {
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.getElementById("overlaywrapper").style.pointerEvents = "none";
    document.getElementById("overlaywrappererror").style.display = "block";
    document.getElementById("errordynamictext").innerHTML = message;
}


// open side div for optimization run parameter settings
function openExpirationDiv(message) {
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.getElementById("overlaywrapper").style.pointerEvents = "none";
    document.getElementById("overlaywrapperexpiration").style.display = "block";
    document.getElementById("expirationdynamictext").innerHTML = message;
}

// open side div for optimization run parameter settings
function closeErrorDiv() {
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.getElementById("overlaywrapper").style.pointerEvents = "auto";
    document.getElementById("overlaywrappererror").style.display = "none";
    document.getElementById("errordynamictext").innerHTML = "";
    checkConditions();
}

// close side div for optimization run parameter settings
function closeParameterDiv() {
    document.getElementById("overlaywrapper").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
} 

// close expiration div 
function closeExpirationDiv() {
    document.getElementById("overlaywrapperexpiration").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
} 

//
function checkConditions(){
    
    $.getJSON('/hh-neuron-builder/check-cond-exist/' + req_pattern, function(data){
        console.log(data)
        var textnode = document.createTextNode("Workflow id: " + data["wf_id"]); 
        document.getElementById("wf-title").innerHTML = "";
        document.getElementById("wf-title").appendChild(textnode);
        if (data['expiration']){
            openExpirationDiv("The workflow directory tree is expired on the server.<br>Please go to the Home page and start a new workflow.<br>");
            return false
        }
        if (data['feat']['status']){
            document.getElementById('feat-bar').style.background = "green";
            document.getElementById('feat-bar').innerHTML = "";
            document.getElementById("del-feat-btn").disabled = false;
            document.getElementById('down-feat-btn').disabled = false;
        } else {
            document.getElementById('feat-bar').style.background = "red";
            document.getElementById("feat-bar").innerHTML = data['feat']['message'];  
            document.getElementById("del-feat-btn").disabled = true;
            document.getElementById('down-feat-btn').disabled = true;
        };

        if (data['opt_files']['status']){
            document.getElementById('opt-files-bar').style.background = "green";
            document.getElementById('del-opt').disabled = false;
            document.getElementById('down-opt-set-btn').disabled = false;
            document.getElementById('opt-files-bar').innerHTML = "";
        } else {
            document.getElementById('opt-files-bar').style.background = "red";
            document.getElementById('del-opt').disabled = true;
            document.getElementById('down-opt-set-btn').disabled = true;
            document.getElementById('opt-files-bar').innerHTML = data['opt_files']['message'];  
            document.getElementById('opt-files-bar').innerHTML = "Optimization files NOT present";
        };

        if (data['opt_set']['status']){
            document.getElementById('opt-param-bar').style.background = "green";
            document.getElementById('opt-param-bar').innerHTML = "";
        } else {
            document.getElementById('opt-param-bar').style.background = "red";
            document.getElementById('opt-param-bar').innerHTML = data['opt_set']['message'];
        };
        document.getElementById("node-num").value = data["opt_set"]["opt_sub_param_dict"]["number_of_nodes"]; 
        document.getElementById("core-num").value = data["opt_set"]["opt_sub_param_dict"]["number_of_cores"]; 
        document.getElementById("offspring").value = data["opt_set"]["opt_sub_param_dict"]["offspring_size"]; 
        document.getElementById("runtime").value = data["opt_set"]["opt_sub_param_dict"]["runtime"]; 
        document.getElementById("gen-max").value = data["opt_set"]["opt_sub_param_dict"]["number_of_generations"]; 

        if (data['opt_res']['status']){
            document.getElementById('down-opt-btn').disabled = false;
        } else {
            document.getElementById('down-opt-btn').disabled = true;
        }

        // if optimization has been submitted
        if (data['opt_flag']['status']){
            document.getElementById("optlaunchimg").src = "/static/img/ok_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "Optimization job submitted";
            document.getElementById("launch-opt-btn").disabled = true;  

            // disable feature extraction buttons
            document.getElementById("feat-efel-btn").disabled = true;
            document.getElementById("feat-up-btn").disabled = true;
            document.getElementById("del-feat-btn").disabled = true;

            //disable optimization buttons
            document.getElementById("opt-db-hpc-btn").disabled = true;
            document.getElementById("opt-up-btn").disabled = true;
            document.getElementById("del-opt").disabled = true;

            // disable optimization settings buttons
            document.getElementById("opt-set-btn").disabled = true;
            
            // if no optimization has been submitted
        } else {
            // enable feature extraction buttons
            document.getElementById("feat-efel-btn").disabled = false;
            document.getElementById("feat-up-btn").disabled = false;

            //enable optimization buttons
            document.getElementById("opt-db-hpc-btn").disabled = false;
            document.getElementById("opt-up-btn").disabled = false;

            // disable optimization settings buttons
            document.getElementById("opt-set-btn").disabled = false;

            document.getElementById("optlaunchimg").src = "/static/img/ko_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "No job submitted";
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(255, 255, 255,0.0)';

            // if ready for submission, enable launch optimization button
            if (data['feat']['status'] & data['opt_files']['status'] & data['opt_set']['status']){
                document.getElementById("launch-opt-btn").disabled = false;  
            } else {
                document.getElementById("launch-opt-btn").disabled = true;  
            }
        }

        // Simulation panel
        if (data['run_sim']['status']){
            $('#inner-sim-div').show();
            document.getElementById("opt-res-bar").style.background = "green";  
            document.getElementById("opt-res-bar").innerHTML = data['run_sim']['message'];  
            document.getElementById("down-sim-btn").disabled = false;  
            document.getElementById("run-sim-btn").disabled = false;  

            if (data['sim_flag']['status']){
                document.getElementById("del-sim-btn").disabled = true;  
                document.getElementById("opt-fetch-btn").disabled = true;  
                document.getElementById("opt-res-up-btn").disabled = true;  
            } else {
                document.getElementById("del-sim-btn").disabled = false;  
                document.getElementById("opt-fetch-btn").disabled = false;  
                document.getElementById("opt-res-up-btn").disabled = false;  
            } 
        } else {
            document.getElementById("opt-res-bar").style.background = "red";  
            document.getElementById("opt-res-bar").innerHTML = data['run_sim']['message'];  
            document.getElementById("run-sim-div").style.backgroundColor='rgba(255, 255, 255, 0.06)';
            document.getElementById("down-sim-btn").disabled = true;  
            document.getElementById("del-sim-btn").disabled = true;  
            document.getElementById("run-sim-btn").disabled = true;  
            document.getElementById("opt-fetch-btn").disabled = false;  
            document.getElementById("opt-res-up-btn").disabled = false;  
        };
    })
}

// Delete features.json and protocol.json files from containing folder
function deleteFeatureFiles() {

    var resp = confirm("Are you sure you want to delete current feature files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-files/feat/" + req_pattern + "/", function(data){
            checkConditions();
        });
    }
}

// Delete source optimization files from folder
function deleteOptFiles() {
    var resp = confirm("Are you sure you want to delete current optimization files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-files/optset/" + exc + "/" + ctx + "/", function(data){
            checkConditions();
        });
    }
}

// Delete source optimization files from folder
function deleteSimFiles() {
    var resp = confirm("Are you sure you want to delete current optimization files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-files/modsim/" + exc + "/" + ctx + "/", function(data){
            checkConditions();
        });
    }
}

// Display please wait div
function displayPleaseWaitDiv(message="") {
    document.getElementById("overlaywrapperwait").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
    if (message || !(message.length === 0)){
        document.getElementById("waitdynamictext").innerHTML = message;
    }
}

// Hide please wait message div
function closePleaseWaitDiv() {
    document.getElementById("overlaywrapperwait").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

function changeMsgPleaseWaitDiv(msg) {
    document.getElementById("waitdynamictext").innerHTML = msg;
}

// Run optimization on hpc system 
function runOptimization() {
    document.getElementById("run-sim-btn").disabled = true;
    displayPleaseWaitDiv();
    changeMsgPleaseWaitDiv("Launching optimization on the hpc system");
    $.getJSON("/hh-neuron-builder/run-optimization/" + req_pattern, function(data){
        checkConditions();
        closePleaseWaitDiv();
        if (data['status_code'] != 200){
            openErrorDiv("Submission ended with error: " + data['status_code']);
        } else {
            openErrorDiv("Submission ended without errors");
        }
    });
}


// Display operation ended message div
function displayOpEndDiv() {
    document.getElementById("overlaywrapperop").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// Hide please wait message div
function hideOpEndDiv() {
    document.getElementById("overlaywrapperop").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

// Manage feature files upload button
function featUploadButton() {
    document.getElementById("opt-res-file").value = "";
    document.getElementById("opt-res-file").multiple = true;
    document.getElementById("opt-res-file").accept = ".json";
    var type = "feat";
    var msg = 'Upload features files ("features.json" and "protocols.json")';
    openUploadDiv(type, msg);
}

// Manage optimization result upload button
function displayOptResUploadDiv() {
    document.getElementById("opt-res-file").value = "";
    document.getElementById("opt-res-file").multiple = false;
    document.getElementById("opt-res-file").accept = ".zip";
    var type = "modsim";
    var msg = 'Upload model (".zip")';
    openUploadDiv(type, msg);
}


// Manage optimization result upload button
function displayOptSetUploadDiv() {
    document.getElementById("opt-res-file").value = "";
    document.getElementById("opt-res-file").multiple = false;
    document.getElementById("opt-res-file").accept = ".zip";
    var type = "optset";
    var msg = 'Upload optimization settings (".zip")';
    openUploadDiv(type, msg);
}


//
function openUploadDiv(type, msg) {
    var uploadForm = document.getElementById("uploadFileForm");

    uploadForm.setAttribute("action", "/hh-neuron-builder/upload-files/" + type + "/" + exc + "/" + ctx + "/");

    var uploadTitleDiv = document.getElementById("uploadTitleDiv");
    uploadTitleDiv.innerHTML = "<strong>" + msg + "</strong>";

    // display image if uploading simulztion .zip file
    if (type == "modsim"){
        document.getElementById("upload_sim_img_div").style.display = "block";
    } else {
        document.getElementById("upload_sim_img_div").style.display = "none";
    }
    $('#opt-res-file').val("");
    $('#upload-opt-res-btn').prop('disabled', true);
    document.getElementById("overlaywrapperoptres").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// Manage feature files upload button
function closeUploadDiv() {
    document.getElementById("overlaywrapperoptres").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}


// Display fetch parameter div
function displayFetchParamDiv() {
    document.getElementById("overlaywrapperfetch").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// Manage feature files upload button
function closeFetchParamDiv() {
    document.getElementById("overlaywrapperfetch").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

function displayJobInfoDiv(){
    displayJobInfo();
}

// Manage job info div
function displayJobInfo() {
    displayPleaseWaitDiv();
    changeMsgPleaseWaitDiv("Fetching job list");
    $("#job-list-div").empty();
    $.getJSON("/hh-neuron-builder/get-nsg-job-list/" + req_pattern, function(joblist){
        if ($.isEmptyObject(joblist)){
            closePleaseWaitDiv();
            openErrorDiv("You have no job on the hpc system");
            checkConditions();
            return false; 
        }
        var job_list_len = Object.keys(joblist).length;
        var job_key_list = Object.keys(joblist);
        var tableId = document.getElementById("job-list-table");
        var tableBody = document.getElementById("job-list-body");
        $("#job-list-body").empty();
        for (var i = 0; i < job_list_len; i++){
            (function(cnrt) {
                crr_idx = 0;
                $.getJSON("/hh-neuron-builder/get-nsg-job-details/" + job_key_list[cnrt] + "/" + req_pattern + "/", function(job_details){
                    if (cnrt+1 > crr_idx) {
                        print_idx = cnrt+1;
                        crr_idx = print_idx;
                    }
                    changeMsgPleaseWaitDiv("Fetching details for job " + (print_idx) + " of " + job_list_len);

                    var crr_job_json = job_details;
                    //
                    //var crr_div = document.createElement("DIV");
                    //crr_div.className = "center-container row-center-container";
                    //
                    //var job_id_span = document.createElement("SPAN");
                    //job_id_span.className = "simple-span w-30pc center-container row-center-container";
                    //var textnode = document.createTextNode(crr_job_json['job_id']); 
                    //job_id_span.appendChild(textnode);
                    //crr_div.appendChild(job_id_span);
                    //
                    //var job_date_span = document.createElement("SPAN");
                    //job_date_span.className = "simple-span w-20pc center-container row-center-container";
                    //var job_date = document.createTextNode(crr_job_json['job_date_submitted']);
                    //job_date_span.appendChild(job_date);
                    //crr_div.appendChild(job_date_span);
                    //
                    //var job_status_span = document.createElement("SPAN");
                    //job_status_span.className = "simple-span w-15pc center-container row-center-container";

                    //var job_status = document.createTextNode(crr_job_json['job_stage']); 
                    //job_status_span.appendChild(job_status);

                    //crr_div.appendChild(job_status_span);

                    //var job_download_button = document.createElement("button");
                    //job_download_button.id = crr_job_json['job_id'] + "2";
                    //job_download_button.innerHTML = "Download";
                    //job_download_button.className = "btn btn-default down-job-btn";
                    //job_download_button.disabled = true;
                    //crr_div.appendChild(job_download_button);


                    var job_download_button2 = document.createElement("button");
                    job_download_button2.id = crr_job_json['job_id'];
                    job_download_button2.innerHTML = "Download";
                    job_download_button2.className = "btn btn-default down-job-btn";
                    job_download_button2.disabled = true;

                    // 

                    var crr_row = tableBody.insertRow(-1);
                    var cell1 = crr_row.insertCell(0);
                    var cell2 = crr_row.insertCell(1);
                    var cell3 = crr_row.insertCell(2);
                    var cell4 = crr_row.insertCell(3);
                    var cell5 = crr_row.insertCell(4);
                    cell1.className += "ttd";
                    cell2.className += "ttd";
                    cell3.className += "ttd";
                    cell3.setAttribute("align", "center");
                    cell4.className += "ttd";
                    cell5.className += "ttd";
                    cell1.innerHTML = "  " + joblist[crr_job_json["job_id"]]["wf"]["wf_id"] + "  ";
                    cell2.innerHTML = "  " + crr_job_json["job_id"] + "  ";
                    cell3.innerHTML = "  " + crr_job_json["job_stage"] + "  " ;

                    var datetime = crr_job_json["job_date_submitted"];
                    var gmt_datetime = moment.utc(datetime).format();
                    cell4.innerHTML = "  " + gmt_datetime + "  ";
                    cell5.appendChild(job_download_button2);


                    if (crr_job_json['job_stage'] == "COMPLETED") {
                        cell3.style.color = "#00802b";
                        cell3.style.fontWeight = "bolder";
                        cell3.style.fontSize = "14px";
                        job_download_button2.disabled = false;
                    } else {
                        cell3.style.color = "#DD9900";
                        cell3.style.fontWeight = "bolder";
                        cell3.style.fontSize = "14px";
                        job_download_button2.disabled = true;
                    }



                    //document.getElementById("job-list-div").prepend(crr_div);
                    if (cnrt == job_list_len - 1) {
                        setTimeout(function()
                        {
                            closePleaseWaitDiv();
                            document.getElementById("overlaywrapperjobs").style.display = "block";
                            document.getElementById("mainDiv").style.pointerEvents = "none";
                            document.body.style.overflow = "hidden";
                            var jobth = document.getElementById("job-th");
                            jobth.click();
                            var wfth = document.getElementById("wf-th");
                            wfth.click();
                        }, 2000);
                    }
                });
            })(i);
        }
    });
    return true;
}


//
function closeJobInfoDiv() {
    document.getElementById("overlaywrapperjobs").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}


//
function downloadJob(jobid) {
    displayPleaseWaitDiv();
    closeJobInfoDiv();
    changeMsgPleaseWaitDiv("Downloading job and analysing data.<br>This operation may take several minutes.");
    $.getJSON('/hh-neuron-builder/download-job/' + jobid + '/' + req_pattern + '/', function(data){
        if (data["response"] == "KO"){
            closePleaseWaitDiv();
            openErrorDiv(data["message"]);
            return false;
        }
        $.getJSON('/hh-neuron-builder/modify-analysis-py/' + req_pattern, function(modifydata){
            if (modifydata["response"] == "KO") {
                closePleaseWaitDiv();
                openErrorDiv(modifydata["message"]);
                return false;
            } else {
                $.getJSON('/hh-neuron-builder/zip-sim/' + req_pattern, function(zip_data){
                    closePleaseWaitDiv();
                    checkConditions();
                });
            };
        });
    });
}


//
function downloadLocalSim(){
    downloadLocal("modsim");
}


//
function downloadLocalOpt(){
    downloadLocal("optres");
}

//
function downloadLocalOptSet(){
    downloadLocal("optset");
}

//
function downloadLocalFeat(){
    downloadLocal("feat");
}
//
function downloadLocal(filetype) {

    displayPleaseWaitDiv();
    window.location.href = "/hh-neuron-builder/download-zip/" + filetype + "/" +
        exc + "/" + ctx + "/";
    checkConditions();
    closePleaseWaitDiv();
}

function cloneWorkflow() {
    displayPleaseWaitDiv();
    $.getJSON('/hh-neuron-builder/create-wf-folders/cloned/' + req_pattern, function(zip_data){
        checkConditions();
        closePleaseWaitDiv();
    });
}

function saveWorkflow() {
    displayPleaseWaitDiv(message="Saving workflow to storage");
    $.getJSON('/hh-neuron-builder/save-wf-to-storage/' + req_pattern, function(zip_data){
        checkConditions();
        closePleaseWaitDiv();
    });
}

function goHome() {
    displayPleaseWaitDiv(message="Loading ...");
    window.location.href='/hh-neuron-builder?ctx=' + ctx;
    closePleaseWaitDiv();
}
