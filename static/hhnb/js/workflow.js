var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;

$(window).bind("pageshow", function() {
    console.log("exc: " + exc.toString() + " cxt: " + ctx.toString());
    checkConditions();
    closeHpcParameterDiv();
    // closeFetchParamDiv();
    closeUploadDiv(true);
    // hideLoadingAnimation();
    closeJobFetchDiv();
});

$(document).ready(function(){
    showLoadingAnimation("Loading...");
    checkConditions();
    hideLoadingAnimation();
    // check conditions on function activation
    //checkConditions();

    // manage form for submitting run parameters
 /*    var $formrunparam = $('#submitRunParam');
    $formrunparam.submit(function(e){
        e.preventDefault();
        $.post('/hh-neuron-builder/submit-run-param/' + req_pattern + '/', $(this).serialize(), function(response){
            if (response['response'] == "KO"){
                openErrorDiv("Username and/or password are wrong", 'error');
                checkConditions();
            } else {
                checkConditions();
                closeHpcParameterDiv();
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
                // closeFetchParamDiv();
                displayJobInfoDiv();
                checkConditions();
            } 
        },'json');
        return false;
    });
 */
    var $submitJobParamForm = $("#submitJobParamForm");
    console.log($submitJobParamForm);
    $submitJobParamForm.submit(function(e) {
        e.preventDefault();
        let hpc_sys = $(".accordion-button.active").attr("name");
        var paramFormData = new FormData();
        paramFormData.append("csrfmiddlewaretoken", $("input[name=csrfmiddlewaretoken]").val()) 
        paramFormData.append("hpc_sys", hpc_sys);
        if (hpc_sys == "DAINT-CSCS") {
            paramFormData.append("gen-max", $("#daint-gen-max").val());
            paramFormData.append("offspring", $("#daint-offspring").val());
            paramFormData.append("node-num", $("#daint-node-num").val());
            paramFormData.append("core-num", $("#daint-gen-max").val());
            paramFormData.append("runtime", $("#daint-runtime").val());
            paramFormData.append("project", $("#daint_project_id").val());
        }
        if (hpc_sys == "SA-CSCS") {
            paramFormData.append("gen-max", $("#sa-daint-gen-max").val());
            paramFormData.append("offspring", $("#sa-daint-offspring").val());
            paramFormData.append("node-num", $("#sa-daint-node-num").val());
            paramFormData.append("core-num", $("#sa-daint-gen-max").val());
            paramFormData.append("runtime", $("#sa-daint-gen-max").val());
        }
        if (hpc_sys == "NSG") {
            paramFormData.append("gen-max", $("#nsg-gen-max").val());
            paramFormData.append("offspring", $("#nsg-offspring").val());
            paramFormData.append("node-num", $("#nsg-node-num").val());
            paramFormData.append("core-num", $("#nsg-gen-max").val());
            paramFormData.append("runtime", $("#nsg-gen-max").val());
            paramFormData.append("username_submit", $("#username_submit").val());
            paramFormData.append("password_submit", $("#password_submit").val());    
        }
        for (let key of paramFormData.entries()) {
            console.log(key);
        }
        $.ajax({
            url: "/hh-neuron-builder/submit-run-param/" + req_pattern + "/",
            data: paramFormData,
            type: "POST",
            contentType: false,
            processData: false,
            async: false,
            success: function(response) {
                if (response['response'] == "KO"){
                    openErrorDiv("Username and/or password are wrong", 'error');
                    checkConditions();
                } else {
                    checkConditions();
                    closeHpcParameterDiv();
                } 
            }
        })
    })

    // manage form to upload simulation zip file 
    var $uploadFileForm = $("#uploadForm");
    $uploadFileForm.submit(function(e){
        files = $("#formFile").prop("files");
        closeUploadDiv(false);
        showLoadingAnimation("Loading");
        // changeMsgPleaseWaitDiv("Uploading file to the server");
        var uploadFormData = new FormData($("#uploadForm")[0]);
        for (let key of uploadFormData.entries()) {
            console.log(key);
        }
        $.ajax({
            url: $(this).attr("action"),
            data: uploadFormData,
            type: 'POST',
            contentType: false,
            processData: false,
            async: false,
            success: function(resp){
                console.log(resp);
                if (resp["response"]=="KO"){
                    openErrorDiv(resp["message"], 'error');
                } else {
                    checkConditions();
                }
                $("#formFile").val("");
            },  
        });
        e.preventDefault();
        hideLoadingAnimation();
    });
});

// serve embedded-efel-gui page
function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/";
}

function inSilicoPage() {
    showLoadingAnimation("Uploading to blue-naas...")
    console.log("inSilicoPage() called");
    $("#run-sim-btn").prop("disabled", true);
    $.getJSON("/hh-neuron-builder/upload-to-naas/" + req_pattern, function(uploaddata){
        console.log(uploaddata);
        $.getJSON("/hh-neuron-builder/model-loaded-flag/" + req_pattern, function(data){
            console.log(data);
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
function openHpcParameterDiv() {
    console.log("openParameterDiv() called.");
    manageOptSetInput();
    fetch("/hh-neuron-builder/get-authentication")
        .then(response => {
                console.log(response);
                if (response.ok) {
                    $("#overlaywrapper").css("display", "block");
                    $("#overlayparam").css("display", "block");
                } else {
                    console.log("opening download workspace div");
                    openDownloadWorkspaceDiv();
                }
            }
        )
}

$(".accordion-button.hpc").on("click", function() {
    $("#apply-param").prop("disabled", false);
    $(".accordion-button").removeClass("active");
    $(this).addClass("active");
})

// close side div for optimization run parameter settings
function closeHpcParameterDiv() {
    $("#overlaywrapper").css("display", "none");
    $("#overlayparam").css("display", "none");
    $("#apply-param").prop("disabled", true);
} 

function applyJobParam() {
    var submitJobParamForm = $("#submitJobParamForm");
    submitJobParamForm.submit();
}

function manageErrorDiv(open=false, close=false, message="", tag="") {
    let overlayWrapper = $("#overlaywrapper");
    let overlayWrapperError = $("#overlaywrappererror");
    let errorDynamicText = $("#errordynamictext");
    let button = $("#ok-error-div-btn");
    button.removeClass("blue", "red", "green");
    if (open) {
        overlayWrapper.css("display", "block");
        overlayWrapperError.css("display", "block");
        errorDynamicText.html(message);
        if (tag == "error") {
            overlayWrapperError.css("box-shadow", "0 0 1rem 0 rgba(255, 0, 0, .8)");
            overlayWrapperError.css("border-color", "red");
            button.addClass("red");
        } else if (tag == "info") {
            overlayWrapperError.css("box-shadow", "0 0 1rem 0 rgba(0, 0, 255, .8)");
            overlayWrapperError.css("border-color", "blue");
            button.addClass("blue");
        } else if (tag == "success") {
            overlayWrapperError.css("box-shadow", "0 0 1rem 0 rgba(0, 255, 0, .8)");
            overlayWrapperError.css("border-color", "green");
            button.addClass("green");
        }
    } else if (close) {
        overlayWrapper.css("display", "none");
        overlayWrapperError.css("display", "none");
    }
}

function openErrorDiv(message, tag) {
    manageErrorDiv(open=true, close=false, message, tag);
}

function closeErrorDiv() {
    manageErrorDiv(open=false, close=true);
    checkConditions();
}

function manageExpirationDiv(open=false, close=false, message="") {
    let overlayWrapper = $("#overlaywrapper");
    let overlayWrapperExpiration = $("#overlaywrapperexpiration");
    let expirationDynamicText = $("#expirationdynamictext");
    if (open) {
        overlayWrapper.css("display", "block");
        overlayWrapperExpiration.css("display", "block");
        expirationDynamicText.html(message);
    } else if (close) {
        overlayWrapper.css("display", "none");
        overlayWrapperExpiration.css("display", "none");
    }
}

function openExpirationDiv(message) {
    manageExpirationDiv(open=true, close=false, message);
}

function closeExpirationDiv() {
    manageExpirationDiv(open=false, close=true);
}

function manageReloadDiv(open=false, close=false, message="") {
    let overlayWrapper = $("#overlaywrapper");
    let overlayWrapperReload = $("#overlayWrapperReload");
    let reloadDynamicText = $("#reloaddynamictext");
    if (open) {
        overlayWrapper.css("display", "block");
        overlayWrapperReload.css("display", "block");
        reloadDynamicText.html(message);
    } else if (close) {
        overlayWrapper.css("display", "none");
        overlayWrapperReload.css("display", "none");
    }
}

// Open reload div
function openReloadDiv(message="") {
    manageReloadDiv(open=true, close=false, message);
}

// Close reload div
function closeReloadDiv() {
    manageReloadDiv(open=false, close=true);
    window.location="/hh-neuron-builder/"
}

function openDownloadWorkspaceDiv() {
    $("#overlaywrapper").css("display", "block");
    $("#overlaydownloadworkspace").css("display", "block");
}

function closeDownloadWorkspaceDiv() {
    $("#overlaywrapper").css("display", "none");
    $("#overlaydownloadworkspace").css("display", "none");
}

//
function checkConditions(){
    $.getJSON('/hh-neuron-builder/check-cond-exist/' + req_pattern, function(data){
        console.log(data);
        if (data["response"] == "KO"){
            // closePleaseWaitDiv();
            hideLoadingAnimation();
            openReloadDiv(data["message"]);
        } else {
            var textnode = document.createTextNode("Workflow id: " + data["wf_id"]); 
            document.getElementById("wf-title").innerHTML = "";
            document.getElementById("wf-title").appendChild(textnode);
            if (data['expiration']){
                openExpirationDiv("The workflow directory tree is expired on the server.<br>Please go to the Home page and start a new workflow.<br>");
                return false
            }
            if (data['feat']['status']){
                let featBar = $("#feat-bar");
                featBar.removeClass("red");
                featBar.addClass("green");
                featBar.html("");
                $("#del-feat-btn").prop("disabled", false);
                $("#down-feat-btn").prop("disabled", false);
            } else {
                let featBar = $("#feat-bar");
                featBar.removeClass("green");
                featBar.addClass("red");
                featBar.html(data['feat']['message']);
                $("#del-feat-btn").prop("disabled", true);
                $("#down-feat-btn").prop("disabled", true);
            };

            if (data['opt_files']['status']){
                let optFilesBar = $("#opt-files-bar");
                optFilesBar.removeClass("red");
                optFilesBar.addClass("green");
                optFilesBar.html("");
                $("#down-opt-set-btn").prop("disabled", false);
                $("#del-opt").prop("disabled", false)
            } else {
                let optFilesBar = $("#opt-files-bar");
                optFilesBar.removeClass("green");
                optFilesBar.addClass("red");
                optFilesBar.html("Optimization files NOT present");
                $("#down-opt-set-btn").prop("disabled", true);
                $("#del-opt").prop("disabled", true)
            };

            if (data['opt_set']['status']){
                let optParamBar = $("#opt-param-bar");
                optParamBar.removeClass("red");
                optParamBar.addClass("green");
                optParamBar.html("");
            } else {
                let optParamBar = $("#opt-param-bar");
                optParamBar.removeClass("green");
                optParamBar.addClass("red");
                optParamBar.html(data['opt_set']['message'])
            };
            $("input[name=node-num").val(data["opt_set"]["opt_sub_param_dict"]["number_of_nodes"]); 
            $("input[name=core-num").val(data["opt_set"]["opt_sub_param_dict"]["number_of_cores"]); 
            $("input[name=offspring").val(data["opt_set"]["opt_sub_param_dict"]["offspring_size"]); 
            $("input[name=runtime").val(data["opt_set"]["opt_sub_param_dict"]["runtime"]); 
            $("input[name=gen-max").val(data["opt_set"]["opt_sub_param_dict"]["number_of_generations"]); 

            if (data['opt_res_files']['status']){
                $("#down-opt-btn").prop("disabled", false);
            } else {
                $("#down-opt-btn").prop("disabled", true);
            }

            // if optimization has been submitted
            if (data['opt_flag']['status']){
                $("#launch-opt-btn").prop("disabled", true);
                // disable feature extraction buttons
                $("#feat-efel-btn").prop("disabled", true);
                $("#feat-up-btn").prop("disabled", true);
                $("#del-feat-btn").prop("disabled", true);

                //disable optimization buttons
                $("#opt-db-hpc-btn").prop("disabled", true);
                $("#opt-up-btn").prop("disabled", true);
                $("#del-opt").prop("disabled", true);

                // disable optimization settings buttons
                $("#opt-set-btn").prop("disabled", true);
                // if no optimization has been submitted
            } else {
                // enable feature extraction buttons
                $("#feat-efel-btn").prop("disabled", false);
                $("#feat-up-btn").prop("disabled", false);
                
                //enable optimization buttons
                $("#opt-db-hpc-btn").prop("disabled", false);
                $("#opt-up-btn").prop("disabled", false);
                // disable optimization settings buttons
                $("#opt-set-btn").prop("disabled", false);

                // if ready for submission, enable launch optimization button
                if (data['feat']['status'] & data['opt_files']['status'] & data['opt_set']['status']){
                    $("#launch-opt-btn").prop("disabled", false);  
                } else {
                    $("#launch-opt-btn").prop("disabled", true);  
                }
            }

            // Simulation panel
            if (data['run_sim']['status']){
                let optResBar = $("#opt-res-bar");
                optResBar.removeClass("red");
                optResBar.addClass("green");
                optResBar.html(data['run_sim']['message'])
                $("#down-sim-btn").prop("disabled", false);
                $("#run-sim-btn").prop("disabled", false);
                $("#opt-fetch-btn").prop("disabled", true);
                $("#opt-res-up-btn").prop("disabled", true)

                if (data['sim_flag']['status']) {
                    $("#del-sim-btn").prop("disabled", true);  
                    $("#opt-fetch-btn").prop("disabled", true);  
                    $("#opt-res-up-btn").prop("disabled", true);  
                } else {
                    $("#del-sim-btn").prop("disabled", false);  
                    $("#opt-fetch-btn").prop("disabled", false);  
                    $("#opt-res-up-btn").prop("disabled", false);  
                } 
            } else {
                let optResBar = $("#opt-res-bar");
                optResBar.removeClass("green");
                optResBar.addClass("red");
                optResBar.html(data['run_sim']['message']);  
                // document.getElementById("run-sim-div").style.backgroundColor='rgba(255, 255, 255, 0.06)';
                $("#down-sim-btn").prop("disabled", true);  
                $("#del-sim-btn").prop("disabled", true);  
                $("#run-sim-btn").prop("disabled", true);  
                $("#opt-fetch-btn").prop("disabled", false);  
                $("#opt-res-up-btn").prop("disabled", false);  
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

// Run optimization on hpc system 
function runOptimization() {
    $("#launch-opt-btn").prop("disabled", true);
    showLoadingAnimation("Launching optimization on the hpc system");
    $.getJSON("/hh-neuron-builder/run-optimization/" + req_pattern, function(data){
        checkConditions();
        hideLoadingAnimation();
        if (data['response'] != "OK"){
            openErrorDiv("Submission ended with error: " + data['message'], 'error');
        } else {
            openErrorDiv("Submission ended without errors", 'success');
        }
    });
}

// handle on upload file event
$(document).on("change", "#formFile", function(){
    $("#uploadFormButton").prop("disabled", false);
})

function displayFeatUploadDiv() {
    openUploadDiv("feat", "Upload features files (\"features.json\" and \"protocols.json\")");
}

function displayOptSetUploadDiv() {
    openUploadDiv("optset", "Upload optimization settings (\".zip\")");
}

function displayOptResUploadDiv() {
    openUploadDiv("modsim", "Upload model (\".zip\")");
}

function openUploadDiv(type, msg) {
    $("#overlaywrapper").css("display", "block");
    $("#overlayupload").css("display", "block");
    $("#uploadForm").attr("action", "/hh-neuron-builder/upload-files/" + type + "/" + req_pattern + "/");
    $("#uploadFormLabel").html("<strong>" + msg + "</strong>");
    $("#uploadFornButton").prop("disabled", true);
    if (type == "feat") {
        $("#formFile").prop("multiple", true).attr("accept", ".json");
        console.log("feat formFile");
        console.log(document.getElementById("formFile"));
    } else {
        $("#formFile").prop("multiple", false).attr("accept", ".zip");
        console.log(document.getElementById("formFile"));
    }
    if (type == "modsim") {
        $("#uploadImg").css("display", "block");
    } else {
        $("#uploadImg").css("display", "none");
    }
}

function closeUploadDiv(empty=true) {
    $("#overlaywrapper").css("display", "none");
    $("#overlayupload").css("display", "none");
    if (empty) {
        $("#formFile").val("");
    }
}

function displayJobFetchDiv() {
    $("#overlaywrapper").css("display", "block");
    $("#overlayjobs").css("display", "block");
    $(".list-group-item.fetch-jobs").attr("aria-disabled", "false").removeClass("disabled active");
}

function resetJobFetchDiv() {
    $("#nsgLoginRow").css("display", "none");
    $("#spinnerRow").css("display", "none");
    $("#progressRow").css("display", "none");
    $("#tableRow").css("display", "none");
    $("#job-list-body").empty();
    $("#jobsAuthAlert").removeClass("show");
    $("#cancel-job-list-btn").prop("disabled", false);
    $("#refresh-job-list-btn").prop("disabled", true);
    $(".list-group-item.fetch-jobs").removeClass("disabled active").attr("aria-disabled", "false");
    $("#checkNsgSpinnerButton").css("opacity", "0");
    $("#usernameNsg").removeClass("is-invalid");
    $("#passwordNsg").removeClass("is-invalid");
    resetProgressBar();
}

function closeJobFetchDiv() {
    $("#overlaywrapper").css("display", "none");
    $("#overlayjobs").css("display", "none");
    resetJobFetchDiv();
}

function checkNsgLogin() {
    $("#checkNsgSpinnerButton").css("opacity", "1");

    username = $("#usernameNsg").val()
    password = $("#passwordNsg").val()

    $.ajax({
        url: "/hh-neuron-builder/check-nsg-login/" + req_pattern + "/",
        method: "POST",
        data: {
            "username": username,
            "password": password,
        },
        success: function(data) {
            $("#checkNsgSpinnerButton").css("opacity", "0");
            $("#usernameNsg").removeClass("is-invalid");
            $("#passwordNsg").removeClass("is-invalid");
            $("#nsgLoginRow").css("display", "none");
            displayJobList($("#jobsNSG"));
        },
        error: function(error) {
            $("#checkNsgSpinnerButton").css("opacity", "0");
            $("#usernameNsg").addClass("is-invalid").attr("aria-describedby", "User not valid");
            $("#passwordNsg").addClass("is-invalid").attr("aria-describedby", "Password not valid");
        }
    })
}

// Manage job list div
function displayCSCSJobList(button) {
    resetJobFetchDiv();
    fetch("/hh-neuron-builder/get-authentication")
            .then(response => {
                console.log(response);
                if (response.ok) {
                    displayJobList(button)                    
                } else {
                    $("#jobsAuthAlert").addClass("show");
                }
            })
}

function displayNsgJobList() {
    resetJobFetchDiv();
    $("#jobsNSG").addClass("active");
    $("#tableRow").css("display", "none");
    $("#nsgLoginRow").css("display", "flex");
}

function refreshJobListDiv() {
    $("#job-list-body").empty();
    $("#tableRow").css("display", "none");
    $("#refresh-job-list-btn").prop("disabled", true);
    resetProgressBar();
    displayJobList($(".list-group-item.fetch-jobs.active"));
}

function displayJobList(button) {
    $("#cancel-job-list-btn").prop("disabled", true);
    $("#spinnerRow").css("display", "flex");
    $(".list-group-item.fetch-jobs").addClass("disabled").attr("aria-disabled", "true");
    button.attr("aria-disabled", "false").removeClass("disabled").addClass("active");

    var tableBody = document.getElementById("job-list-body");
    var hpc = button.attr("name");

    $.getJSON("/hh-neuron-builder/get-job-list/" + hpc + "/" + req_pattern, async function(jobList) {
        $("#spinnerRow").css("display", "none");
        $("#progressRow").css("display", "flex");
        
        jobList = JSON.parse(jobList);
        console.log(jobList);
        if ($.isEmptyObject(jobList)) {
            closeJobFetchDiv();
            openErrorDiv("You have no job on the hpc system", "info");
            checkConditions();
            return false;
        }
        
        await sleep(500);
        
        step = 100 / (Object.keys(jobList).length + 1);
        animateProgressBar(step);

        $.each(jobList, function(id, job){
            $.getJSON("/hh-neuron-builder/get-job-details2/" + id + "/" + req_pattern + "/", function(jobDetails){
                jobDetails = JSON.parse(jobDetails);
                console.log(jobDetails);
                let downloadButton = document.createElement("button");
                downloadButton.id = jobDetails.job_id;
                downloadButton.innerHTML = "Download";
                downloadButton.className = "btn workflow-btn job-download-button";
                downloadButton.disabled = true;
                downloadButton.setAttribute("onclick", "downloadJob(this)");

                let tr = document.createElement("tr");
                let tdWf = document.createElement("td");
                let tdId = document.createElement("td");
                let tdStatus = document.createElement("td");
                let tdDate = document.createElement("td");
                let tdButton = document.createElement("td");

                tdWf.innerHTML = jobDetails.job_name;
                tdId.innerHTML = jobDetails.job_id;
                tdStatus.innerHTML = jobDetails.job_stage;
                tdDate.innerHTML = moment.utc(jobDetails.job_date_submitted).format();
                tdButton.appendChild(downloadButton);

                tr.appendChild(tdWf);
                tr.appendChild(tdId);
                tr.appendChild(tdStatus);
                tr.appendChild(tdDate);
                tr.appendChild(tdButton);
                tableBody.appendChild(tr);

                if (jobDetails.job_stage == "COMPLETED" || 
                            jobDetails.job_stage == "SUCCESSFUL" || 
                            jobDetails.job_stage == "FAILED") {
                        tdStatus.style.color = "#00802b";
                        tdStatus.style.fontWeight = "bolder";
                        downloadButton.disabled = false;
                        if (jobDetails.job_stage == "FAILED"){
                            tdStatus.style.color = "#DD9900";
                        }
                    } else {
                        tdStatus.style.color = "#DD9900";
                        tdStatus.style.fontWeight = "bolder";
                        downloadButton.disabled = true;
                    }

                animateProgressBar(step);
            })
        });
        while (true) {
            await sleep(1000);
            if (parseFloat($("#progressBar").attr("aria-valuenow")) >= 99.0) {
                $("#progressRow").css("display", "none");
                $("#tableRow").css("display", "flex");
                $("#refresh-job-list-btn").prop("disabled", false).blur();
                $("#cancel-job-list-btn").prop("disabled", false);
                $(".list-group-item.fetch-jobs").attr("aria-disabled", "false").removeClass("disabled");
                return true;
            }
        }
    });
}

function closeDownloadJob() {
    resetProgressBar();
    $("#overlaywrapper").css("display", "none");
    $("#overlayjobprocessing").css("display", "none");
}

async function downloadJob(button) {
    console.log("downloadJob() called");
    // disable all buttons
    jobId = button.id;
    closeJobFetchDiv();
    $("#overlaywrapper").css("display", "block");
    $("#overlayjobprocessing").css("display", "block");
    $("#jobProcessingTitle").html("Downloading job: " + jobId);
    await sleep(2000);
    animateProgressBar(20);
    $.getJSON("/hh-neuron-builder/download-job/" + jobId + "/" + req_pattern + "/", function(data) {
        if (data["response"] == "KO") {
            closeDownloadJob();
            openErrorDiv(data["message"], "error");
            return false;
        }
        animateProgressBar(50);
        $("#jobProcessingTitle").html("Running Analysis");
        var p = $.getJSON("/hh-neuron-builder/run-analysis/" + req_pattern, function(modifydata) {
            var resp_flag = false;
            if (modifydata["response"] == "KO") {
                closeDownloadJob();
                openErrorDiv(data["message", "error"]);
                return false;
            } else {
                var resp_flag = true;
                animateProgressBar(80);
                $("#jobProcessingTitle").html("Creating ZIP file")
                $.getJSON("/hh-neuron-builder/zip-sim/" + jobId + "/" + req_pattern, async function(zip_data) {
                    if (zip_data["response"] == "KO") {
                        closeDownloadJob();
                        openErrorDiv(zip_data["message"], "error");
                        return false;
                    } else {
                        $("#jobProcessingTitle").html("Completing...");
                        animateProgressBar(100);
                        await sleep(2000);
                    }
                    checkConditions();
                    $("#overlayjobprocessing").css("display", "none");
                    $("#overlaywrapper").css("display", "none");
                }).fail(function (error) { 
                    console.log("failing on zip-sim");
                    console.log(error);
                })
            }
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

function downloadLocalFeat(){
    downloadLocal("feat");
}

function downloadLocal(filetype) {
    showLoadingAnimation();
    window.location.href = "/hh-neuron-builder/download-zip/" + filetype + "/" +
        exc + "/" + ctx + "/";
    checkConditions();
    hideLoadingAnimation();
}

function newWorkflow() {
    showLoadingAnimation();
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            hideLoadingAnimation();
            openReloadDiv();
        } else {
            hideLoadingAnimation();
            window.location.href = "/hh-neuron-builder/workflow/";
        }
    });
}

function cloneWorkflow() {
    $.getJSON("/hh-neuron-builder/clone-workflow/" + req_pattern + "/", function(data) {
        console.log(data);
        let win = window.open("/hh-neuron-builder/workflow/" + data.exc + "/" + data.ctx + "/", "_blank");
        win.focus();
    });
    $("#wf-btn-clone-wf").blur();
}

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

function goHome() {
    showLoadingAnimation("Loading...");
    window.location.href='/hh-neuron-builder?ctx=' + ctx;
    closePleaseWaitDiv();
}

function manageOptSetInput() {
    if ($("#daint-node-num").val() == "") {
        $("#daint-node-num").val(6);
    }
    if ($("#daint-core-num").val() == "") {
        $("#daint-core-num").val(24);
    }
    if ($("#daint-runtime").val() == "") {
        $("#daint-runtime").val("120m");
    }
    if ($("#sa-daint-node-num").val() == "") {
        $("#sa-daint-node-num").val(6);
    }
    if ($("#sa-daint-core-num").val() == "") {
        $("#sa-daint-core-num").val(24);
    }
    if ($("#sa-daint-runtime").val() == "") {
        $("#sa-daint-runtime").val(2);
    }
    if ($("#nsg-node-num").val() == "") {
        $("#nsg-node-num").val(1);
    }
    if ($("#nsg-core-num").val() == "") {
        $("#nsg-core-num").val(2);
    }
    if ($("#nsg-runtime").val() == "") {
        $("#nsg-runtime").val(2);
    }
}

$("#daintCollapse")[0].addEventListener('show.bs.collapse', function () {
    console.log("upper daint");
    $("#overlayparam").addClass("upper-daint");
    // $("#overlayparam").css("top", "calc(10%)");
})

$("#serviceAccountCollapse")[0].addEventListener('show.bs.collapse', function () {
    $("#overlayparam").addClass("upper-sa-daint");
    // $("#overlayparam").css("top", "calc(20%)");
    console.log("upper SA");
})
$("#nsgCollapse")[0].addEventListener('show.bs.collapse', function () {
    $("#overlayparam").addClass("upper-nsg");
    // $("#overlayparam").css("top", "calc(40%)");
    console.log("upper nsg");
})

$("#daintCollapse")[0].addEventListener('hide.bs.collapse', function () {
    $("#overlayparam").removeClass("upper-daint");
    console.log("lower daint");
})

$("#serviceAccountCollapse")[0].addEventListener('hide.bs.collapse', function () {
    $("#overlayparam").removeClass("upper-sa-daint");
    console.log("lower SA");
})
$("#nsgCollapse")[0].addEventListener('hide.bs.collapse', function () {
    $("#overlayparam").removeClass("upper-nsg");
    console.log("lower nsg")

})

function animateProgressBar(progress) {
    current_progress = parseInt($(".progress-bar").attr("aria-valuenow"));
    next_progress = current_progress + progress;
    $(".progress-bar").css("width", next_progress + "%").attr("aria-valuenow", next_progress);
}

function resetProgressBar() {
    $(".progress-bar").css("width", "0%").attr("aria-valuenow", "0");
}

function dismissAlert() {
    $("#jobsAuthAlert").removeClass("show");
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
 }