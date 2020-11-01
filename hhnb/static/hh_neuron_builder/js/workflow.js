var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;

$(window).bind("pageshow", function() {
    console.log("exc: " + exc.toString() + " cxt: " + ctx.toString());
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
                openErrorDiv("Username and/or password are wrong", 'error');
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
                openErrorDiv(response['message'], 'error');
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
                    openErrorDiv(resp["message"], 'error');
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
    document.getElementById("wf-btn-new-wf").onclick = newWorkflow;
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
    document.getElementById("hpc_sys").onchange = manageOptSetInput;

    // manage buttons for insertion of fetch parameters
    document.getElementById("opt-fetch-btn").onclick = displayFetchParamDiv;
    document.getElementById("cancel-param-fetch-btn").onclick = closeFetchParamDiv;
    document.getElementById("hpc_sys_fetch").onchange = manageOptSetInput;

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

    // manage reload message ok button
    document.getElementById("reload-div-btn").onclick = closeReloadDiv;

    //manage button for refreshing job list
    document.getElementById("refresh-job-list-btn").onclick = refreshJobInfoDiv;

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

// open div for optimization run parameter settings
function openParameterDiv() {
    console.log("openParameterDiv() called.");
    fetch('/hh-neuron-builder/get-authentication')
        .then(response => {
                if (response.ok) {
                    document.getElementById("overlaywrapper").style.display = "block";
                    document.getElementById("mainDiv").style.pointerEvents = "none";
                    document.body.style.overflow = "hidden";
                } else {
                    console.log("opening download workspace div");
                    openDownloadWorkspaceDiv();
//                    alert('Please download your workflow before authentication and then upload it to continue with you workspace');
//                    saveWorkflow();
//                    window.location.href = "/oidc/authenticate/";
                }
            }
        )
}

// open side div for optimization run parameter settings
function openErrorDiv(message, messagetag) {
    var contmsgdiv = document.getElementById("overlaywrappererror");
    var msgdiv = document.getElementById("overlayerror");
    var textdiv = document.getElementById("errordynamictext");
    textdiv.innerHTML = "";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.getElementById("overlaywrapper").style.pointerEvents = "none";
    contmsgdiv.style.display = "block";
    textdiv.innerHTML = message;
    if (messagetag == "error"){
        msgdiv.style.borderColor = 'red';
    } else if (messagetag == "info"){
        msgdiv.style.borderColor = 'blue';
    } else if (messagetag == "success") {
        msgdiv.style.borderColor = 'green';
    }
}


// open side div for optimization run parameter settings
function openExpirationDiv(message) {
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.getElementById("overlaywrapper").style.pointerEvents = "none";
    document.getElementById("overlaywrapperexpiration").style.display = "block";
    document.getElementById("expirationdynamictext").innerHTML = message;
}

function openDownloadWorkspaceDiv() {
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.getElementById("overlaywrapper").style.pointerEvents = "none";
    document.getElementById("overlaywrapperdownloadworkspace").style.display = "block";
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


function closeDownloadWorkspaceDiv() {
    document.getElementById("overlaywrapperdownloadworkspace").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

//
function checkConditions(){
    $.getJSON('/hh-neuron-builder/check-cond-exist/' + req_pattern, function(data){
        console.log(data);
        if (data["response"] == "KO"){
            closePleaseWaitDiv();
            openReloadDiv();
        } else {
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

            if (data['opt_res_files']['status']){
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
    var msgtext = document.getElementById("waitdynamictext");
    msgtext.innerHTML = "";
    document.getElementById("overlaywrapperwait").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
    if (message || !(message.length === 0)){
        msgtext.innerHTML = message;
    }
}

// Display reload div
function openReloadDiv(message="") {
    document.getElementById("overlaywrapperreload").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
    if (message || !(message.length === 0)){
        document.getElementById("waitdynamictext").innerHTML = message;
    }
}

// Close reload div
function closeReloadDiv() {
    document.getElementById("overlaywrapperreload").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
    window.location="/hh-neuron-builder/"
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
        if (data['response'] != "OK"){
            openErrorDiv("Submission ended with error: " + data['message'], 'error');
        } else {
            openErrorDiv("Submission ended without errors", 'success');
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
    var msg = 'Upload features files\n("features.json" and "protocols.json")';
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
    var uploadTitleDiv = document.getElementById("uploadTitleDiv");

    uploadForm.setAttribute("action", "/hh-neuron-builder/upload-files/" + type + "/" + exc + "/" + ctx + "/");
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

function refreshJobInfoDiv(){
    closeJobInfoDiv();
    displayJobInfo();
}

// Manage job info div
function displayJobInfo() {
    displayPleaseWaitDiv();
    changeMsgPleaseWaitDiv("Fetching job list");
    var tableBody = document.getElementById("job-list-body");
    $("#job-list-div").empty();
    $.getJSON("/hh-neuron-builder/get-job-list/" + req_pattern, function(joblist){
        if ($.isEmptyObject(joblist)){
            closePleaseWaitDiv();
            openErrorDiv("You have no job on the hpc system", 'info');
            checkConditions();
            return false; 
        }
        var job_list_len = Object.keys(joblist).length;
        var job_key_list = Object.keys(joblist);
        $("#job-list-body").empty();
        for (var i = 0; i < job_list_len; i++){
            (function(cnrt) {
                crr_idx = 0;
                $.getJSON("/hh-neuron-builder/get-job-details/" + encodeURIComponent(job_key_list[cnrt]) + "/" + req_pattern + "/", function(job_details){
                    if (cnrt+1 > crr_idx) {
                        print_idx = cnrt+1;
                        crr_idx = print_idx;
                    }
                    changeMsgPleaseWaitDiv("Fetching details for job " + (print_idx) + " of " + job_list_len);
                    var crr_job_json = job_details;

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


                    if (crr_job_json['job_stage'] == "COMPLETED" || 
                            crr_job_json['job_stage'] == "SUCCESSFUL" || 
                            crr_job_json['job_stage'] == "FAILED") {
                        cell3.style.color = "#00802b";
                        cell3.style.fontWeight = "bolder";
                        cell3.style.fontSize = "14px";
                        job_download_button2.disabled = false;
                        if (crr_job_json['job_stage'] == "FAILED"){
                            cell3.style.color = "#DD9900";
                        }
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
                                    jobth.click();
                                    var dtth = document.getElementById("dt-th");
                                    dtth.click();
                                    dtth.click();
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
    changeMsgPleaseWaitDiv("Downloading job results and analyzing data.<br>This operation may take several minutes.");
    $.getJSON('/hh-neuron-builder/download-job/' + jobid + '/' + req_pattern + '/', function(data){
        if (data["response"] == "KO"){
            closePleaseWaitDiv();
            openErrorDiv(data["message"], 'error');
            return false;
        }
        var p = $.getJSON('/hh-neuron-builder/run-analysis/' + req_pattern, function(modifydata){
            var resp_flag = false
                if (modifydata["response"] == "KO") {
                    closePleaseWaitDiv();
                    openErrorDiv(modifydata["message"], 'error');
                    return false;
                } else {
                    var resp_flag = true
                        $.getJSON('/hh-neuron-builder/zip-sim/' + jobid + '/'  + req_pattern, function(zip_data){
                            if (zip_data["response"] == "KO") {
                                closePleaseWaitDiv();
                                openErrorDiv(zip_data["message"], 'error');
                                return false;
                            } else {
                                closePleaseWaitDiv();
                            }
                            checkConditions();
                        });
                };
        });
        setTimeout(function(){ 
            if (resp_flag) {
            } else { 
                p.abort();
                closePleaseWaitDiv();
                openErrorDiv("Your request has expired.<br>Please verify that you are not behind a firewall and/or your data are not too big to be processed in less than 10 minutes", 'error')
            }
        }, 600000);
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

//
function newWorkflow() {
    displayPleaseWaitDiv();
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            closePleaseWaitDiv();
            openReloadDiv();
        } else {
            closePleaseWaitDiv();
            window.location.href = "/hh-neuron-builder/workflow/";
        }
    });
}

function cloneWorkflow() {
//    displayPleaseWaitDiv();
    $.getJSON("/hh-neuron-builder/clone-workflow/" + req_pattern + "/", function(data) {
        console.log(data);
        let win = window.open("/hh-neuron-builder/workflow/" + data.exc + "/" + data.ctx + "/", "_blank");
        win.focus();
    });
    // $.getJSON('/hh-neuron-builder/create-wf-folders/cloned/' + req_pattern, function(zip_data){
    //     checkConditions();
    //     closePleaseWaitDiv();
    //     let win = window.open('/hh-neuron-builder/workflow', "_blank");
    //     win.focus();
    // });
}

//
/*function saveWorkflow() {
    displayPleaseWaitDiv(message="Saving workflow to storage");
    $.getJSON('/hh-neuron-builder/save-wf-to-storage/' + req_pattern, function(zip_data){
        checkConditions();
        closePleaseWaitDiv();
    });
}*/


function downloadURI(uri, name) {
  var link = document.createElement("a");
  link.download = name;
  link.href = uri;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  delete link;
}


function saveWorkflow() {
    fetch("/hh-neuron-builder/workflow-download/" + req_pattern, {
        method: "GET"
    }).then(
        data => downloadURI(data.url, 'workflow')
    ).catch(
        error => console.log(error)
    );
}


function saveWorkflowOnDiv() {
    fetch("/hh-neuron-builder/workflow-download/" + req_pattern, {
        method: "GET"
    }).then(data => {
            downloadURI(data.url, 'workflow');
            window.location.href = "/oidc/authenticate/";
        }
    ).catch(
        error => console.log(error)
    );
}

//
function goHome() {
    displayPleaseWaitDiv(message="Loading ...");
    window.location.href='/hh-neuron-builder?ctx=' + ctx;
    closePleaseWaitDiv();
}

//
function manageOptSetInput(){

    var select_el = $(this).closest('select').attr('id');
    var dd = document.getElementById(select_el);
    var form_el = $(dd).closest('form').attr('id');
    var sys = dd.options[dd.selectedIndex].getAttribute("name");

    var corenum = document.getElementById("core-num");
    var nodenum = document.getElementById("node-num");
    var runtime = document.getElementById("runtime");
    if (form_el == "submitRunParam") {
        var pwd = document.getElementById("password_submit");
        var un = document.getElementById("username_submit");
        var pwd_div = document.getElementById("pwd-div");
        var un_div = document.getElementById("un-div");
        var hpc_param_container = document.getElementById("hpc-param");
        var apply_param_button = document.getElementById("apply-param");
    } else if (form_el == "submitFetchParam"){
        var pwd = document.getElementById("password_fetch");
        var un = document.getElementById("username_fetch");
        var pwd_div = document.getElementById("pwd-fetch-div");
        var un_div = document.getElementById("un-fetch-div");
        var hpc_param_container = document.getElementById("hpc-param-fetch");
        var apply_param_button = document.getElementById("apply-param-fetch");
    }

    if (sys == "--"){
        pwd_div.setAttribute("style", "display:none");
        un_div.setAttribute("style", "display:none");
        hpc_param_container.classList = "collapse";
        apply_param_button.disabled = true;
        pwd.required = false;
        un.required = false;
        if (form_el == "submitRunParam") {
            corenum.value = "";
            nodenum.value = "";
            runtime.value = "";
            corenum.required = false;
            nodenum.required = false;
            runtime.required = false;
        }
    }
    else if (sys == "DAINT-CSCS" || sys == "SA-CSCS"){
        rt_sys = {"DAINT-CSCS":"120m", "SA-CSCS":2}
        pwd_div.setAttribute("style", "display:none");
        un_div.setAttribute("style", "display:none");
        pwd.setAttribute("value", "NONE");
        hpc_param_container.setAttribute("style", "display:none");
        apply_param_button.disabled = false;
        pwd.required = false;
        un.required = false;
        if (form_el == "submitRunParam") {
            corenum.value = 24;
            nodenum.value = 6;
            runtime.type = "string";
            //runtime.value = "120m";
            runtime.value = rt_sys[sys];
            corenum.required = true;
            nodenum.required = true;
            runtime.required = true;
        }
    } else if (sys == "NSG"){
        pwd_div.setAttribute("style", "display:block;");
        un_div.setAttribute("style", "display:block;");
        pwd.setAttribute("value", "");
        pwd.required = true;
        un.required = true;
        hpc_param_container.setAttribute("style", "display:block");
        apply_param_button.disabled = false;
        if (form_el == "submitRunParam") {
            corenum.value = 2;
            nodenum.value = 1;
            runtime.type = "number";
            runtime.value = 2;
            corenum.required = true;
            nodenum.required = true;
            runtime.required = true;
        }
    }
}
