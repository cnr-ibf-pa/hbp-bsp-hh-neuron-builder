var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;

var is_user_authenticated = false;
var modal_view = true;
var from_hhf = false;

$(window).bind("pageshow", function() {
    console.log("exc: " + exc.toString() + " cxt: " + ctx.toString());
    checkConditions();


    if (window.location.href.includes("/hh-neuron-builder/hhf-comm?hhf_dict=") && modal_view) {
        $("#modalButton").trigger("click");
        modal_view = false;
    }
    console.log(window.location.href);
});


$(document).ready(function(){
    // checkConditions();
    
    
    showLoadingAnimation("Loading...");
    fetch("/hh-neuron-builder/get-authentication")
            .then(response => {
                console.log(response);
                hideLoadingAnimation();
                if (response.ok) {
                    is_user_authenticated = true;                    
                }
            })

    var $submitJobParamForm = $("#submitJobParamForm");
    console.log($submitJobParamForm);
    $submitJobParamForm.submit(function(e) {
        e.preventDefault();
        let hpc_sys = $(".accordion-button.active").attr("name");
        var paramFormData = new FormData();
        paramFormData.append("csrfmiddlewaretoken", $("input[name=csrfmiddlewaretoken]").val()) 
        paramFormData.append("hpc_sys", hpc_sys);
        if (hpc_sys == "DAINT-CSCS" || hpc_sys == "SA-CSCS") {
            if (!is_user_authenticated) {
                $("#hpcAuthAlert").addClass("show");
                return false;
            }
        }
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
        console.log("uploadingFileForm() called.");
        showLoadingAnimation("Loading...");
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
                hideLoadingAnimation();
            },  
        });
        e.preventDefault();
    });

    // hideLoadingAnimation();
});

// serve embedded-efel-gui page
function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/";
}

function inSilicoPage() {
    console.log("inSilicoPage() called.");
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
    $("#overlaywrapper").css("display", "block");
    $("#overlayparam").css("display", "block");
    if($(".accordion-button.hpc").hasClass("active")) {
        $("#apply-param").prop("disabled", false);
    }
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
    $("#hpcAuthAlert").removeClass("show");
} 

function applyJobParam() {
    $("#apply-param").blur();
    var submitJobParamForm = $("#submitJobParamForm");
    submitJobParamForm.submit();
}

function manageErrorDiv(isOpen=false, isClose=false, message="", tag="") {
    let overlayWrapper = $("#overlaywrapper");
    let overlayWrapperError = $("#overlaywrappererror");
    let errorDynamicText = $("#errordynamictext");
    let button = $("#ok-error-div-btn");
    button.removeClass("blue", "red", "green");
    if (isOpen) {
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
    } else if (isClose) {
        overlayWrapper.css("display", "none");
        overlayWrapperError.css("display", "none");
    }
}

function openErrorDiv(message, tag) {
    manageErrorDiv(isOpen=true, isClose=false, message, tag);
}

function closeErrorDiv() {
    manageErrorDiv(isOpen=false, isClose=true);
    checkConditions();
}

function manageExpirationDiv(isOpen=false, isClose=false, message="") {
    let overlayWrapper = $("#overlaywrapper");
    let overlayWrapperExpiration = $("#overlaywrapperexpiration");
    let expirationDynamicText = $("#expirationdynamictext");
    if (isOpen) {
        overlayWrapper.css("display", "block");
        overlayWrapperExpiration.css("display", "block");
        expirationDynamicText.html(message);
    } else if (isClose) {
        overlayWrapper.css("display", "none");
        overlayWrapperExpiration.css("display", "none");
    }
}

function openExpirationDiv(message) {
    manageExpirationDiv(isOpen=true, isClose=false, message);
}

function closeExpirationDiv() {
    manageExpirationDiv(isOpen=false, isClose=true);
}

function manageReloadDiv(isOpen=false, isClose=false, message="") {
    let overlayWrapper = $("#overlaywrapper");
    let overlayWrapperReload = $("#overlaywrapperreload");
    let reloadDynamicText = $("#reloaddynamictext");
    if (isOpen) {
        overlayWrapper.css("display", "block");
        overlayWrapperReload.css("display", "block");
        reloadDynamicText.html(message);
    } else if (isClose) {
        overlayWrapper.css("display", "none");
        overlayWrapperReload.css("display", "none");
    }
}

// Open reload div
function openReloadDiv(message="") {
    manageReloadDiv(isOpen=true, isClose=false, message);
}

// Close reload div
function closeReloadDiv() {
    manageReloadDiv(isOpen=false, isClose=true);
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
    console.log("checkConditions() called.");
    showLoadingAnimation("Loading...");
    $.getJSON('/hh-neuron-builder/check-cond-exist/' + req_pattern, function(data){
        console.log(data);
        if (data["response"] == "KO"){
            openReloadDiv(data["message"]);
        } else {
            $("#wf-title").html("Workflow id: <bold>" + data["wf_id"] + "</bold>");
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
                console.log("restoring classes");
                let optFilesBar = $("#opt-files-bar");
                optFilesBar.removeClass("green");
                optFilesBar.addClass("red");
                optFilesBar.html(data['opt_files']['message']);
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
                $("#del-sim-btn").prop("disabled", false);

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
                $("#down-sim-btn").prop("disabled", true);  
                $("#del-sim-btn").prop("disabled", true);  
                $("#run-sim-btn").prop("disabled", true);  
                $("#opt-fetch-btn").prop("disabled", false);  
                $("#opt-res-up-btn").prop("disabled", false);  
            };

            // HHF Integration
            if (data['from_hhf']['status']) {
                $("#opt-db-hpc-btn").prop("disabled", true);
                $("#opt-up-btn").prop("disabled", true);
                $("#down-opt-set-btn").prop("disabled", false);
                $("#del-opt").prop("disabled", false);
                $(".hhf-integration-component").css("display", "block");
                from_hhf = true;
            } else {
                from_hhf = false;
                $(".hhf-integration-component").css("display", "none");
            }
        };
        hideLoadingAnimation();
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
    if (from_hhf) {
        fetch("/hh-neuron-builder/hhf-delete-all/" + req_pattern)
            .then(results => { console.log(results); checkConditions(); });
    } else {
        var resp = confirm("Are you sure you want to delete current optimization files?");
        if (resp) {
            $.getJSON("/hh-neuron-builder/delete-files/optset/" + exc + "/" + ctx + "/", function(data){
                checkConditions();
            });
        }
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
    $("#overlayupload").addClass("upper-daint");
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
    $("#overlayupload").removeClass("upper-daint");
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
            if (parseFloat($("#progressBarFetchJob").attr("aria-valuenow")) >= 99.0) {
                var tableRows = []
                for (let i = 0; i < tableBody.children.length; i++) {
                    tableRows[i] = tableBody.children[i];
                }
                tableRows.sort(function(a, b) {
                    return moment.utc(a.children[3].innerHTML) - moment.utc(b.children[3].innerHTML);
                });
                tableRows.reverse();
                $("#job-list-body").empty();
                for (let i = 0; i < tableRows.length; i++) {
                    tableBody.appendChild(tableRows[i]);
                }

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
    setProgressBarValue(20);
    $.getJSON("/hh-neuron-builder/download-job/" + jobId + "/" + req_pattern + "/", function(data) {
        if (data["response"] == "KO") {
            closeDownloadJob();
            openErrorDiv(data["message"], "error");
            return false;
        }
        setProgressBarValue(50);
        $("#jobProcessingTitle").html("Running Analysis");
        var p = $.getJSON("/hh-neuron-builder/run-analysis/" + req_pattern, function(modifydata) {
            var resp_flag = false;
            if (modifydata["response"] == "KO") {
                closeDownloadJob();
                openErrorDiv(data["message", "error"]);
                return false;
            } else {
                var resp_flag = true;
                setProgressBarValue(80);
                $("#jobProcessingTitle").html("Creating ZIP file")
                $.getJSON("/hh-neuron-builder/zip-sim/" + jobId + "/" + req_pattern, async function(zip_data) {
                    if (zip_data["response"] == "KO") {
                        closeDownloadJob();
                        openErrorDiv(zip_data["message"], "error");
                        return false;
                    } else {
                        $("#jobProcessingTitle").html("Completing...");
                        setProgressBarValue(100);
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
    if (from_hhf) {
        showLoadingAnimation("Downloading HHF folder...");
        fetch("/hh-neuron-builder/hhf-download-all/" + req_pattern, {
            method: "GET"
        }).then(
            data => downloadURI(data.url, 'hhf_folder')
        ).then(
            hideLoadingAnimation()
        ).catch(
            error => console.log(error)
        );
    } else {
        downloadLocal("optset");
    }
}

function downloadLocalFeat(){
    downloadLocal("feat");
}

function downloadLocal(filetype) {
    showLoadingAnimation("Downloading files...");
    window.location.href = "/hh-neuron-builder/download-zip/" + filetype + "/" + exc + "/" + ctx + "/";
    checkConditions();
    hideLoadingAnimation();
}

function newWorkflow() {
    $("#wf-btn-new-wf").blur();
    showLoadingAnimation("Starting new workflow...");
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            openReloadDiv();
        } else {
            window.location.href = "/hh-neuron-builder/workflow/";
        }
        hideLoadingAnimation();
    });
}

function cloneWorkflow() {
    $("#wf-btn-clone-wf").blur();
    showLoadingAnimation("Cloning workflow...");
    $.ajax({
        url: "/hh-neuron-builder/clone-workflow/" + req_pattern + "/",
        method: "GET",
        async: false,
        success: function(data) {
            hideLoadingAnimation();
            window.open("/hh-neuron-builder/workflow/" + data.exc + "/" + data.ctx + "/", "_blank");
            win.focus();
        }
    });
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
    console.log("saveWorkflow() called.");
    $("#wf-btn-save").blur();
    showLoadingAnimation("Loading...")
    fetch("/hh-neuron-builder/workflow-download/" + req_pattern, {
        method: "GET"
    }).then(
        data => downloadURI(data.url, 'workflow')
    ).then(
        hideLoadingAnimation()
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
    console.log("goHome() called.");
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
    current_progress = parseFloat($(".progress-bar").attr("aria-valuenow"));
    next_progress = current_progress + progress;
    $(".progress-bar").css("width", next_progress + "%").attr("aria-valuenow", next_progress);
}

function setProgressBarValue(value) {
    $(".progress-bar").css("width", parseInt(value) + "%").attr("aria-valuenow", parseInt(value));
}

function resetProgressBar() {
    $(".progress-bar").css("width", "0%").attr("aria-valuenow", "0");
}

function dismissAlert(el) {
    console.log($(el).parent().removeClass("show"));
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

$("#loginButton").click(function() {
    console.log("loginButton() pressed.");
    showLoadingAnimation("Loading...");
    $.ajax({
        url: "/hh-neuron-builder/store-workflow-in-session/" + req_pattern + "/",
        method: "GET",
        success: function(data) {
            window.location.href = "/oidc/authenticate";
        }
    });
    return false;
});


$("#openFileManagerIcon").hover(
    function() {
        $(this).addClass("fa-folder-open").removeClass("fa-folder");
    },
    function() {
        $(this).removeClass("fa-folder-open").addClass("fa-folder");
    }
);


function openFileManager() {
    fetchHHFFileList();
    console.log("fetchHHFFileList() on openFileManager()");
    $("#overlaywrapper").css("display", "block");
    $("#overlayfilemanager").css("display", "block");
    $.ajax({
        url: "/hh-neuron-builder/hhf-get-model-key/" + req_pattern + "/",
        method: "GET",
        success: function(response) {
            console.log(response);
            $("#modelKeyInput").val(JSON.parse(response).model_key);
        }
    });
}


function fetchHHFFileList() {
    $.getJSON("/hh-neuron-builder/hhf-get-files/" + req_pattern + "/", function(data) {
        
        if (data.morphology && data.morphology.length > 0) {
            for (let i = 0; i < data.morphology.length; i++) {
                let name = data.morphology[i]
                $("#morphologyFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>");
                $("#morphologyFileList").removeClass("empty-list");
            }
        } else {
            console.log("append Empty on morpFileList");
            $("#morphologyFileList").addClass("empty-list");
            $("#morphologyFileList").append("<div class='file-item empty'>Empty</div>");
        }

        if (data.mechanisms && data.mechanisms.length > 0) {
            for (let i = 0; i < data.mechanisms.length; i++) {
                let name = data.mechanisms[i]
                $("#mechanismsFileList").append("<li id='" + name + "' class='list-group-item file-item' onclick='selectFileItem(this)'>" + name + "</li>");
            }
        } else {
            console.log("append Empty on modFileList");
            $("#mechanismsFileList").append("<div class='file-item empty'>Empty</div>");
        }
        
        if (data.config && data.config.length > 0) {
            for (let i = 0; i < data.config.length; i++) {
                let name = data.config[i];
                $("#configFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>");
            } 
        } else {
            $("#configFileList").append("<div class='file-item empty'>Empty</div>");
        }

        if (data.model && data.model.length > 0) {
            for (let i = 0; i < data.model.length; i++) {
                let name = data.model[i];
                $("#modelFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>")
            }
        } else {
            $("#modelFileList").append("<div class='file-item empty'>Empty</div>");
        }

        if (data["parameters.json"]) {
            $("#parametersTextArea").val(data["parameters.json"]);
        }

        if (data["opt_neuron.py"]) {
            $("#optNeuronCode").html(data["opt_neuron.py"]);
        }
        hljs.highlightAll();
   
        $("#fileItemSpinner").css("display", "none");
        showFileList($(".folder-item.active"));
    });
}


function refreshHHFFileList() {
    $(".file-group").css("display", "none");
    $(".file-group").empty();
    $(".file-textarea").css("display", "none");
    $(".file-code").css("display", "none");
    $("code").html();
    $("#fileItemSpinner").css("display", "flex");
    fetchHHFFileList();
    console.log("fetchHHFFileList() on refreshHHFFileList()");
}


function closeFileManager() {
    $("#overlaywrapper").css("display", "none");
    $("#overlayfilemanager").css("display", "none");
    $(".file-item").removeClass("active");
    $(".file-group").empty();
    $("code").html();
    saveParametersJson();
    setModelKey(onClose=true);
    checkConditions();
};


function saveParametersJson() {
    var jj = {"parameters.json": ($("#parametersTextArea").val())};
    $.ajax({
        url: "/hh-neuron-builder/hhf-save-parameters-json/" + req_pattern,
        method: "POST",
        data: jj,
        error: function(response) {
            console.log(JSON.parse(response.responseText));
            openErrorDiv(JSON.parse(response.responseText).message, "error");
        }
    });
}


$("#deleteFileButton").click(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }

    if ($(".folder-item.active").attr("id") == "morphologyFolder") {
        if ($("#morphologyFileList").hasClass("empty-list")) {
            $("#uploadFileButton").removeClass("disabled");
        }
    }

    if ($(".file-item.active").length == 0) {
        return false;
    }

    var jj_ids = {"id": []};
    var files = $(".file-item.active");

    console.log(files);
    files.each(function(i) {
        jj_ids.id.push($(this).attr("id"));
    });

    console.log(JSON.stringify(jj_ids));

    fetch("/hh-neuron-builder/hhf-delete-files/" + $(".folder-item.active").attr("id") + "/" + req_pattern + "?file_list=" + encodeURIComponent(JSON.stringify(jj_ids)), {
        method: "GET"
    }).then(function(data) {
        console.log(data);
        refreshHHFFileList();
        console.log("refreshHHFFileList() on #deleteFileButton callback.")
    })
});


$("#downloadFileButton").click(function() {
    if ($(".folder-item.active").attr("id") == "parametersFolder" ) {
        fetch("/hh-neuron-builder/hhf-download-files/parameters/" + req_pattern)
            .then(data => downloadURI(data.url, 'parameters.json'));
        return false;
    } 

    if ($(".folder-item.active").attr("id") == "optNeuronFolder") {
        fetch("/hh-neuron-builder/hhf-download-files/optneuron/" + req_pattern)
            .then(data => downloadURI(data.url, 'opt_neuron.py'));
        return false;
    } 
    
    if ($(".file-item.active").length == 0) {
        return false;
    }

    showLoadingAnimation("Downloading files...");

    var jj_ids = {"id": []};
    var files = $(".file-item.active");

    files.each(function(i) {
        jj_ids.id.push($(this).attr("id"));
    });

    fetch("/hh-neuron-builder/hhf-download-files/" + $(".folder-item.active").attr("id") + "/" + req_pattern + "?file_list=" + encodeURIComponent(JSON.stringify(jj_ids)), {
        method: "GET"
    }).then(function(data) {
        downloadURI(data.url, 'files');
        $(".file-item.active").removeClass("active");
        hideLoadingAnimation();
    }).catch(
        error => console.log(error)
    );
});


$("#uploadFileButton").click(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    
    const input = document.createElement("input");
    input.setAttribute("multiple", "true");
    input.setAttribute("type", "file");
    input.click();
    
    var counter = 0;
    var files = 0

    const upload = (file) => {
        $.ajax({
            url: "/hh-neuron-builder/hhf-upload-files/" + $(".folder-item.active").attr("id") + "/" + req_pattern + "/",
            method: "POST",
            headers: {
                "Content-Type": "application/octet-stream",
                "Content-Disposition": "attachment; filename=\"" + file.name + "\""
            },
            body: file,
            success: function(response) {
                console.log("file " + file.name + " uploaded successfully");
                counter += 1;
                if (counter == files) {
                    hideLoadingAnimation();
                    refreshHHFFileList();
                    console.log("refreshHHFFileList() on #uploadFileButton callback.")
                }
            },
            error: function(error) {
                console.log(error);
                closeFileManager();
                openErrorDiv(JSON.parse(error.responseText).message, "error");
            }
        });
    }

    const onSelectFile = async function(x) {
        files = input.files.length;
        console.log("files: " + files.toString());
        $(".file-group").css("display", "none");
        $("#fileItemSpinner").css("display", "flex");
        showLoadingAnimation('Uploading files...');
        for (let i = 0; i < input.files.length; i++) {
            upload(input.files[i]);
        }
        input.files = null;
    }

    input.addEventListener('change', onSelectFile, false);
});


$("#selectAllButton").click(function() {
    if ($(this).hasClass("active")) {
        $(".file-item").removeClass("active");
    } else {
        $(this).addClass("active");
        $(".file-group.active").children().addClass("active");
        //$(".file-item").addClass("active");
    }
})


function uploadParameters() {
    console.log("upload parameters.json");
}


$(".folder-item").click(function() {
    showFileList($(this));
})


function showFileList(folder) {
    var currFolder = folder.attr("id");
    var currList = null;

    $("#selectAllButton").removeClass("active");
    $(".file-item").removeClass("active");
    $(".folder-item").removeClass("active").attr("aria-current", false);
    $(".file-group").css("display", "none").removeClass("active");
    $(".file-textarea").css("display", "none");
    $(".file-code").css("display", "none");
    $(".ui-button").removeClass("disabled");

    folder.addClass("active").attr("aria-current", true);

    if (currFolder == "morphologyFolder") {
        currList = $("#morphologyFileList"); 
        if (!currList.hasClass("empty-list")) {
            $("#uploadFileButton").addClass("disabled");
        }
    } else if (currFolder == "mechanismsFolder") {
        currList = $("#mechanismsFileList");
    } else if (currFolder == "configFolder") {
        currList = $("#configFileList"); 
        $("#uploadFileButton").addClass("disabled");
        $("#deleteFileButton").addClass("disabled");

    } else if (currFolder == "modelFolder") {
        currList = $("#modelFileList"); 
        $("#uploadFileButton").addClass("disabled");
        $("#deleteFileButton").addClass("disabled");
    } else if (currFolder == "parametersFolder") {
        currList = $("#parametersTextArea"); 
        $("#deleteFileButton").addClass("disabled");
        $("#selectAllButton").addClass("disabled");

    } else if (currFolder == "optNeuronFolder") {
        currList = $("#optNeuronTextArea"); 
        $("#deleteFileButton").addClass("disabled");
        $("#selectAllButton").addClass("disabled");
        $("#uploadFileButton").addClass("disabled");
    }
    currList.css("display", "block");
    currList.addClass("active");
    if (currList.hasClass("empty-list")) {
        $("#downloadFileButton").addClass("disabled");
        $("#selectAllButton").addClass("disabled");
        $("#deleteFileButton").addClass("disabled");
    }
}


function selectFileItem(item) {
    $(item).toggleClass("active");
}


$("#refreshFileListButton").click(function() {
    refreshHHFFileList();
    console.log("refreshHHFFileList() on #refreshFileListButton callback.")
})


function setModelKey(onClose=false) {
    var k = $("#modelKeyInput").val();
    fetch("/hh-neuron-builder/hhf-apply-model-key/" + req_pattern + "/" + k.toString(), {
        method: "GET"
    }).then( data => { 
        console.log(data)
        if (data.status == 200 && !onClose) {
            refreshHHFFileList();
            console.log("refreshHHFFileList() on #uploadFileButton callback.")
        }    
    });
}


$("#infoFileManagerButton").click(function() {
    $("#modalButton").trigger("click");
});
