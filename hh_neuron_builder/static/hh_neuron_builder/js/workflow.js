$(window).bind("pageshow", function() { 
    checkConditions();
});
$(document).ready(function(){
    // check conditions on function activation
    checkConditions();

    $('#job-list-div').on('click', '.down-job-btn', function(){
        downloadJob(this.id);
    });

    //
    // manage form for submitting run parameters
    var $formrunparam = $('#submitRunParam');
    $formrunparam.submit(function(){
        $.post($(this).attr('action'), $(this).serialize(), function(response){
            closeParameterDiv();
            checkConditions();
        },'json');
        return false;
    });

    // manage form for submitting fetch parameters
    var $formfetchparam = $('#submitFetchParam');
    $formfetchparam.submit(function(){
        $.post($(this).attr('action'), $(this).serialize(), function(response){
            closeFetchParamDiv();
            displayJobInfoDiv();
            checkConditions();
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
                checkConditions();
            },  
        });
        e.preventDefault();
        closePleaseWaitDiv();
    });

    // assign functions to buttons' click
    //document.getElementById("test-button").onclick = displayFetchParamDiv;
    //document.getElementById("test-back-button").onclick = displayJobInfoDiv;

    // manage optimization settings buttons action
    document.getElementById("opt-set-btn").onclick = openParameterDiv;
    document.getElementById("cancel-param-btn").onclick = closeParameterDiv;
    document.getElementById("down-opt-set-btn").onclick = downloadLocalOptSet;


    // manage simulation run buttons
    document.getElementById("run-sim-btn").onclick = inSilicoPage;
    document.getElementById("down-sim-btn").onclick = downloadLocalSim;

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
    document.getElementById("del-feat").onclick = deleteFeatureFiles;
    document.getElementById("down-feat-btn").onclick = downloadLocalFeat;

    // manage button for deleting optimization setting files
    document.getElementById("del-opt").onclick = deleteOptFiles;

    // manage button for deleting optimization setting files
    document.getElementById("del-sim-btn").onclick = deleteSimFiles;

    // manage button for running optimization
    document.getElementById("launch-opt-btn").onclick = runOptimization;

    // manage buttons for downloading jobs
    document.getElementById("cancel-job-list-btn").onclick = closeJobInfoDiv;
    //
});


// serve embedded-efel-gui page
function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/";

}

// serve embedded-naas page
function inSilicoPage() {
    $.getJSON("/hh-neuron-builder/upload-to-naas", function(uploaddata){
        $.getJSON("/hh-neuron-builder/model-loaded-flag", function(data){
            var o = data["response"];
            if (o == "ERROR"){
                window.location.href = "";
            } else {
                window.location.href = "/hh-neuron-builder/embedded-naas/";
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

// close side div for optimization run parameter settings
function closeParameterDiv() {
    document.getElementById("overlaywrapper").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
} 

//
function checkConditions(){
    $.getJSON('/hh-neuron-builder/check-cond-exist', function(data){
        var textnode = document.createTextNode("Workflow id: " + data["wf_id"]); 
        document.getElementById("wf-title").innerHTML = "";
        document.getElementById("wf-title").appendChild(textnode);

        if (data['feat']){
            document.getElementById('feat-bar').style.background = "green";
            document.getElementById('feat-bar').innerHTML = "";
            document.getElementById('del-feat').disabled = false;
            document.getElementById('down-feat-btn').disabled = false;
        } else {
            document.getElementById('feat-bar').style.background = "red";
            document.getElementById('feat-bar').innerHTML = '"features.json" and/or "protocols.json" NOT present';
            document.getElementById('del-feat').disabled = true;
            document.getElementById('down-feat-btn').disabled = true;
        };

        if (data['opt_files']){
            document.getElementById('opt-files-bar').style.background = "green";
            document.getElementById('del-opt').disabled = false;
            document.getElementById('down-opt-set-btn').disabled = false;
            document.getElementById('opt-files-bar').innerHTML = "";
        } else {
            document.getElementById('opt-files-bar').style.background = "red";
            document.getElementById('del-opt').disabled = true;
            document.getElementById('down-opt-set-btn').disabled = true;
            document.getElementById('opt-files-bar').innerHTML = "Optimization files NOT present";
        };

        if (data['opt_set']){
            document.getElementById('opt-param-bar').style.background = "green";
            document.getElementById('opt-param-bar').innerHTML = "";
        } else {
            document.getElementById('opt-param-bar').style.background = "red";
            document.getElementById('opt-param-bar').innerHTML = "Optimization parameters NOT set";
        };

        if (data['opt_flag']){
            document.getElementById("optlaunchimg").src = "/static/images/ok_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "Optimization job submitted";
        } else {
            document.getElementById("optlaunchimg").src = "/static/images/ko_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "No job submitted";
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(255, 255, 255,0.0)';
        }

        if (data['feat'] & data['opt_files'] & data['opt_set'] & !data['opt_flag']){
            document.getElementById("launch-opt-btn").disabled = false;  
        } else {
            document.getElementById("launch-opt-btn").disabled = true;  
        };

        // Simulation panel
        if (data['run_sim']){
            document.getElementById("opt-res-bar").style.background = "green";  
            document.getElementById("down-sim-btn").disabled = false;  
            document.getElementById("run-sim-btn").disabled = false;  
            if (data['sim_flag']){
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
            document.getElementById("run-sim-div").style.backgroundColor='rgba(255, 255, 255, 0.06)';
            document.getElementById("down-sim-btn").disabled = true;  
            document.getElementById("del-sim-btn").disabled = true;  
        };
    })
}

// Delete features.json and protocol.json files from containing folder
function deleteFeatureFiles() {
    var resp = confirm("Are you sure you want to delete current feature files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-files/feat/", function(data){
            checkConditions();
        });
    }
}

// Delete source optimization files from folder
function deleteOptFiles() {
    var resp = confirm("Are you sure you want to delete current optimization files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-files/optset/", function(data){
            checkConditions();
        });
    }
}

// Delete source optimization files from folder
function deleteSimFiles() {
    var resp = confirm("Are you sure you want to delete current optimization files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-files/modsim/", function(data){
            checkConditions();
        });
    }
}

// Display please wait div
function displayPleaseWaitDiv() {
    document.getElementById("overlaywrapperwait").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
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
    $.getJSON("/hh-neuron-builder/run-optimization", function(data){
        checkConditions();
        closePleaseWaitDiv();
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
    var msg = 'Upload optimization results (".zip")';
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
    uploadForm.setAttribute("action","/hh-neuron-builder/upload-files/" + type + "/");

    var uploadTitleDiv = document.getElementById("uploadTitleDiv");
    uploadTitleDiv.innerHTML = "<strong>" + msg + "</strong>";

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
    $.getJSON("/hh-neuron-builder/get-nsg-job-list", function(joblist){
        var job_list_len = Object.keys(joblist).length;
        var job_key_list = Object.keys(joblist);
        for (var i = 0; i < job_list_len; i++){
            (function(cnrt) {
                $.getJSON("/hh-neuron-builder/get-nsg-job-details/" + job_key_list[cnrt] + "/", function(job_details){
                    changeMsgPleaseWaitDiv("Fetching details for job " + (cnrt+1) + " of " + job_list_len);

                    var crr_job_json = job_details;
                    //
                    var crr_div = document.createElement("DIV");
                    crr_div.className = "center-container row-center-container";
                    //
                    var job_id_span = document.createElement("SPAN");
                    job_id_span.className = "simple-span w-30pc center-container row-center-container";
                    var textnode = document.createTextNode(crr_job_json['job_id']); 
                    job_id_span.appendChild(textnode)
                        crr_div.appendChild(job_id_span);
                    //
                    var job_date_span = document.createElement("SPAN");
                    job_date_span.className = "simple-span w-20pc center-container row-center-container";
                    var job_date = document.createTextNode(crr_job_json['job_date_submitted']);
                    job_date_span.appendChild(job_date);
                    crr_div.appendChild(job_date_span);
                    //
                    var job_status_span = document.createElement("SPAN");
                    job_status_span.className = "simple-span w-15pc center-container row-center-container";

                    var job_status = document.createTextNode(crr_job_json['job_stage']); 
                    job_status_span.appendChild(job_status);

                    crr_div.appendChild(job_status_span);

                    var job_download_button = document.createElement("button");
                    job_download_button.id = crr_job_json['job_id'];
                    job_download_button.innerHTML = "Download";
                    job_download_button.className = "btn btn-default down-job-btn";
                    job_download_button.disabled = true;
                    crr_div.appendChild(job_download_button);

                    // 
                    if (crr_job_json['job_stage'] == "COMPLETED") {
                        job_status_span.style.backgroundColor = 'green';
                        job_download_button.disabled = false;
                    } else {
                        job_status_span.style.backgroundColor = 'rgb(255, 153, 102)';
                    }

                    document.getElementById("job-list-div").prepend(crr_div);
                    document.getElementById("job-list-div").prepend(document.getElementById("fetch-job-title"));
                    if (cnrt == job_list_len - 1) {
                        closePleaseWaitDiv();
                        document.getElementById("overlaywrapperjobs").style.display = "block";
                        document.getElementById("mainDiv").style.pointerEvents = "none";
                        document.body.style.overflow = "hidden";
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
    changeMsgPleaseWaitDiv("Downloading job and analysing data. This operation may take several minutes.");
    $.getJSON('/hh-neuron-builder/download-job/' + jobid + '/', function(data){
        $.getJSON('/hh-neuron-builder/modify-analysis-py', function(modifydata){
            $.getJSON('/hh-neuron-builder/zip-sim', function(zip_data){
                closePleaseWaitDiv();
                checkConditions();
            });
        });
    });
}


//
function downloadLocalSim(){
    downloadLocal("modsim");
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
    window.location.href = "/hh-neuron-builder/download-zip/" + filetype + "/";
    //window.location.assign("/hh-neuron-builder/download-zip/" + filetype + "/");
    closePleaseWaitDiv();
    checkConditions();
}
