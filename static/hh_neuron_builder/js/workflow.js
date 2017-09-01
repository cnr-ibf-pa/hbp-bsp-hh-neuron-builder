$(document).ready(function(){
    // check conditions on function activation
    checkConditions();

    // manage form for submitting run parameters
    var $form = $('#submitRunParam');
    $form.submit(function(){
        $.post($(this).attr('action'), $(this).serialize(), function(response){
            closeParameterDiv();
            checkConditions();
        },'json');
        return false;
    });

    // manage form for submitting fetch parameters
    var $form = $('#submitFetchParam');
    $form.submit(function(){
        $.post($(this).attr('action'), $(this).serialize(), function(response){
            closeFetchParamDiv();
            checkConditions();
        },'json');
        return false;
    });

    // manage form to upload simulation zip file 
    var $uploadForm = $('#uploadOptResForm');
    $uploadForm.submit(function(e){
        displayPleaseWaitDiv();
        var uploadFormData = new FormData($(this)[0]);
        $.ajax({
            url: $(this).attr("action"),
            data:uploadFormData,
            type: 'POST',
            contentType: false,
            processData: false,
            success: function(resp){
                checkConditions();
            },  
        });
        e.preventDefault();
        closeOptResUploadDiv();
        closePleaseWaitDiv();
    });


    // manage form to upload feature files (i.e. features.json, protocols.json)
    var $uploadFeatForm = $('#uploadFeatForm');
    $uploadFeatForm.submit(function(e){
        var uploadFeatFormData = new FormData($(this)[0]);
        $.ajax({
            url: $(this).attr("action"),
            data:uploadFeatFormData,
            type: 'POST',
            contentType: false,
            processData: false,
            success: function(resp){
                checkConditions();
            },  
        });
        e.preventDefault();
        closeFeatureUploadDiv() 
    });

    // assign functions to buttons' click
    document.getElementById("test-button").onclick = displayFetchParamDiv;
    document.getElementById("test-back-button").onclick = displayJobInfoDiv;
    document.getElementById("opt-set-btn").onclick = openParameterDiv;
    document.getElementById("cancel-param-btn").onclick = closeParameterDiv;
    document.getElementById("run-sim-btn").onclick = inSilicoPage;
    document.getElementById("feat-efel-btn").onclick = efelPage;
    document.getElementById("feat-up-btn").onclick = displayFeatUploadDiv;
    document.getElementById("cancel-feature-btn").onclick = closeFeatureUploadDiv;
    document.getElementById("opt-db-hpc-btn").onclick = chooseOptModel;
    document.getElementById("opt-up-btn").onclick = reloadCurrentPage;
    document.getElementById("opt-fetch-btn").onclick = displayFetchParamDiv;
    document.getElementById("cancel-param-fetch-btn").onclick = closeFetchParamDiv;
    document.getElementById("opt-res-up-btn").onclick = displayOptResUploadDiv;
    document.getElementById("del-feat").onclick = deleteFeatureFiles;
    document.getElementById("del-opt").onclick = deleteOptFiles;
    document.getElementById("launch-opt-btn").onclick = runOptimization;
});


// serve embedded-efel-gui page
function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/";
}

// serve embedded-naas page
function inSilicoPage() {
    document.getElementById("res-upload-info-div").innerHTML = "Uploading to <strong> Neuron As A Service </strong>. Please wait ...";
    $.getJSON("/hh-neuron-builder/upload-to-naas", function(uploaddata){
        $.getJSON("/hh-neuron-builder/model-loaded-flag", function(data){
            var o = data["response"];
            if (o == "nothing"){
                window.location.href = "";
            } else {
                document.getElementById("res-upload-info-div").innerHTML = ""
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
        if (data['feat']){
            document.getElementById('feat-bar').style.background = "green";
            document.getElementById('feat-bar').innerHTML = "";
            document.getElementById('del-feat').disabled = false;
        } else {
            document.getElementById('feat-bar').style.background = "red";
            document.getElementById('feat-bar').innerHTML = '"features.json" and/or "protocols.json" NOT present';
            document.getElementById('del-feat').disabled = true;
        };

        if (data['opt_files']){
            document.getElementById('opt-files-bar').style.background = "green";
            document.getElementById('del-opt').disabled = false;
            document.getElementById('opt-files-bar').innerHTML = "";
        } else {
            document.getElementById('opt-files-bar').style.background = "red";
            document.getElementById('del-opt').disabled = true;
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
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(0, 110, 0, 0.08)';
        } else {
            document.getElementById("optlaunchimg").src = "/static/images/ko_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "No job submitted";
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(255, 255, 255,0.0)';
        }

        if (data['feat'] & data['opt_files'] & data['opt_set']){
            document.getElementById("launch-opt-btn").disabled = false;  
        } else {
            document.getElementById("launch-opt-btn").disabled = true;  
        };

        // Simulation panel
        if (data['run_sim']){
            document.getElementById("opt-res-bar").style.background = "green";  
            document.getElementById("run-sim-btn").disabled = false;  
            document.getElementById("run-sim-div").style.backgroundColor='rgba(0, 110, 0, 0.08)';
        } else {
            document.getElementById("opt-res-bar").style.background = "red";  
            document.getElementById("run-sim-btn").disabled = true;  
            document.getElementById("run-sim-div").style.backgroundColor='rgba(255, 255, 255, 0.06)';
        };

    });
}

// Delete features.json and protocol.json files from containing folder
function deleteFeatureFiles() {
    var resp = confirm("Are you sure you want to delete current feature files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-feature-files", function(data){
            checkConditions();
        });
    }
}

// Delete source optimization files from folder
function deleteOptFiles() {
    var resp = confirm("Are you sure you want to delete current optimization files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-opt-files", function(data){
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
function displayFeatUploadDiv() {
    document.getElementById("overlaywrapperfeature").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// Manage feature files upload button
function closeFeatureUploadDiv() {
    document.getElementById("overlaywrapperfeature").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

// Manage optimization result upload button
function displayOptResUploadDiv() {
    document.getElementById("overlaywrapperoptres").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// Manage feature files upload button
function closeOptResUploadDiv() {
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
                    var job_id_span = document.createElement("SPAN");
                    job_id_span.className = "simple-span";
                    var textnode = document.createTextNode(crr_job_json['job_id']); 
                    job_id_span.appendChild(textnode)
                    crr_div.appendChild(job_id_span);
                    //
                    var job_date_span = document.createElement("SPAN");
                    job_date_span.className = "simple-span";
                    var job_date = document.createTextNode(crr_job_json['job_date_submitted']);
                    job_date_span.appendChild(job_date);
                    crr_div.appendChild(job_date_span);
                    //
                    var job_status_span = document.createElement("SPAN");
                    job_status_span.className = "simple-span";
                    var job_status = document.createTextNode(crr_job_json['job_stage']); 
                    job_status_span.appendChild(job_status);
                    crr_div.appendChild(job_status_span)
                    // 
                    if (crr_job_json['job_stage'] == "COMPLETED") {
                        job_status_span.style.backgroundColor = 'green';
                        var job_download_button = document.createElement("BUTTON");
                        job_download_button.setAttribute('content', 'Download');
                        job_download_button.setAttribute('class', 'btn btn-link');
                        crr_div.appendChild(job_download_button);
                    }

                    document.getElementById("job-list-div").appendChild(crr_div)
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
