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
        // $("#modalButton").trigger("click");
        $("#modalHHF").modal("show");
        modal_view = false;
    }
});


$(document).ready(function(){
    // checkConditions();
    
    fetch("/hh-neuron-builder/get-authentication")
            .then(response => {
                if (response.ok) {
                    is_user_authenticated = true;                    
                }
            })

    var $submitJobParamForm = $("#submitJobParamForm");
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
        showLoadingAnimation("Setting configurations...");
        if (hpc_sys == "DAINT-CSCS") {
            paramFormData.append("gen-max", $("#daint-gen-max").val());
            paramFormData.append("offspring", $("#daint-offspring").val());
            paramFormData.append("node-num", $("#daint-node-num").val());
            paramFormData.append("core-num", $("#daint-core-num").val());
            paramFormData.append("runtime", $("#daint-runtime").val());
            paramFormData.append("project", $("#daint_project_id").val());
        }
        if (hpc_sys == "SA-CSCS") {
            paramFormData.append("gen-max", $("#sa-daint-gen-max").val());
            paramFormData.append("offspring", $("#sa-daint-offspring").val());
            paramFormData.append("node-num", $("#sa-daint-node-num").val());
            paramFormData.append("core-num", $("#sa-daint-core-num").val());
            paramFormData.append("runtime", $("#sa-daint-gen-max").val());
        }
        if (hpc_sys == "NSG") {
            paramFormData.append("gen-max", $("#nsg-gen-max").val());
            paramFormData.append("offspring", $("#nsg-offspring").val());
            paramFormData.append("node-num", $("#nsg-node-num").val());
            paramFormData.append("core-num", $("#nsg-core-num").val());
            paramFormData.append("runtime", $("#nsg-gen-max").val());
            paramFormData.append("username_submit", $("#username_submit").val());
            paramFormData.append("password_submit", $("#password_submit").val());    
        }
        $.ajax({
            url: "/hh-neuron-builder/submit-run-param/" + req_pattern + "/",
            data: paramFormData,
            type: "POST",
            contentType: false,
            processData: false,
            async: false,
            success: function(response) {
                hideLoadingAnimation();
                closeHpcParameterDiv();
                if (response['response'] == "KO"){
                    openErrorDiv(response.message, 'error');
                    $("#username_submit").addClass("is-invalid").attr("aria-describedby", "User not valid");
                    $("#password_submit").addClass("is-invalid").attr("aria-describedby", "Password not valid");
                    //checkConditions();
                } else {
                    $("#username_submit").removeClass("is-invalid");
                    $("#password_submit").removeClass("is-invalid");
                    checkConditions();
                } 
            },
            error: function(error) {
                hideLoadingAnimation();
                console.error(error);
                if (error.status == 403) {
                    openReloadDiv("Something goes wrong.<br>Try to reload the page");
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
            error: function(error) {
                hideLoadingAnimation();
                console.error(error);
                if (error.status == 403) {
                    openReloadDiv("Something goes wrong.<br>Try to reload the page");
                }
            }
        });
        e.preventDefault();
    });

    // hideLoadingAnimation();
});

// serve embedded-efel-gui page
function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/" + req_pattern + "/";
}

function inSilicoPage() {
    console.log("inSilicoPage() called");
    showLoadingAnimation("Uploading to blue-naas...")
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
    if (isOpen) {
        overlayWrapper.css("display", "block");
        overlayWrapperError.css("display", "block");
        errorDynamicText.html(message);
        if (tag == "error") {
            overlayWrapperError.css("box-shadow", "0 0 1rem 0 rgba(255, 0, 0, .8)");
            overlayWrapperError.css("border-color", "red");
            button.addClass("red").removeClass("blue green");
        } else if (tag == "info") {
            overlayWrapperError.css("box-shadow", "0 0 1rem 0 rgba(0, 0, 255, .8)");
            overlayWrapperError.css("border-color", "blue");
            button.addClass("blue").removeClass("red green");
        } else if (tag == "success") {
            overlayWrapperError.css("box-shadow", "0 0 1rem 0 rgba(0, 255, 0, .8)");
            overlayWrapperError.css("border-color", "green");
            button.addClass("green").removeClass("red blue");
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
    //window.location="/hh-neuron-builder/workflow"
    window.location.reload();
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
    showLoadingAnimation("Loading workflow...");
    $.getJSON('/hh-neuron-builder/check-cond-exist/' + req_pattern, function(data){
        console.log(data);
        if (data["response"] == "KO"){
            openExpirationDiv(data["message"]);
        } else {
            $("#wf-title").html("Workflow id: <bold>" + data["wf_id"] + "</bold>");
            if (data['expiration']){
                openExpirationDiv("The workflow directory tree is expired on the server.<br>Please go to the Home page and start a new workflow.<br>");
                return false
            }
            if (data['feat']['status'] == 'hhf_etraces') {
                let featBar = $("#feat-bar");
                featBar.removeClass("red green");
                featBar.addClass("orange");
                featBar.html(data['feat']['message'])
                $("#del-feat-btn").prop("disabled", true);
                $("#down-feat-btn").prop("disabled", true);
            } else {
                if (data['feat']['status']){
                    let featBar = $("#feat-bar");
                    featBar.removeClass("red orange");
                    featBar.addClass("green");
                    featBar.html("");
                    $("#del-feat-btn").prop("disabled", false);
                    $("#down-feat-btn").prop("disabled", false);
                } else {
                    let featBar = $("#feat-bar");
                    featBar.removeClass("green orange");
                    featBar.addClass("red");
                    featBar.html(data['feat']['message']);
                    $("#del-feat-btn").prop("disabled", true);
                    $("#down-feat-btn").prop("disabled", true);
                };
            }
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
                $("#openFileManagerButton").prop("disabled", true);

                // disable optimization settings buttons
                $("#opt-set-btn").prop("disabled", true);
            } else {
                // if no optimization has been submitted enable feature extraction buttons
                $("#feat-efel-btn").prop("disabled", false);
                $("#feat-up-btn").prop("disabled", false);
                
                //enable optimization buttons
                $("#opt-db-hpc-btn").prop("disabled", false);
                $("#opt-up-btn").prop("disabled", false);
                // disable optimization settings buttons
                $("#opt-set-btn").prop("disabled", false);

                $("#openFileManagerButton").prop("disabled", false);

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
                if (data['opt_flag']['status']) {
                    $("#del-opt").prop("disabled", true);
                } else {
                    $("#del-opt").prop("disabled", false);
                }
                $("#openFileManagerButton").css("display", "block");
                $("#opt-up-btn").css("display", "none");
                from_hhf = true;
            } else {
                from_hhf = false;
                $("#opt-up-btn").css("display", "block");
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
            openErrorDiv("Submission ended with error:<br>" + data['message'], 'error');
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
    } else {
        $("#formFile").prop("multiple", false).attr("accept", ".zip");
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
    $(".list-group-item.fetch-jobs").removeClass("disabled active clicked").attr("aria-disabled", "false");
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
    if (button.hasClass("clicked")) {
        return false;
    }
    resetJobFetchDiv();
    if (is_user_authenticated) {
        displayJobList(button);
    }  else {
        $("#jobsAuthAlert").addClass("show");
    }
    button.addClass("clicked");
}

function displayNsgJobList(button) {
    if (button.hasClass("clicked")) {
        return false;
    }
    resetJobFetchDiv();
    $("#jobsNSG").addClass("active");
    $("#tableRow").css("display", "none");
    $("#nsgLoginRow").css("display", "flex");
    button.addClass("clicked");
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
            $.getJSON("/hh-neuron-builder/get-job-details2/" + id + "/" + req_pattern + "/", function(jobDetails) {

                jobDetails = JSON.parse(jobDetails);
                console.log(jobDetails);

                keys = Object.keys(jobDetails);
                for (let k = 0; k < keys.length; k++) {
                    if (k == "resp" && jobDetails[k] == "KO") {
                        console.error(jobDetails.message);
                        openReloadDiv("Something goes wrong while fetching jobs.<br>Please realod the page.");
                        return false;
                    }
                }

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
                if (tdWf.innerHTML == "") {
                    tdWf.innerHTML = "Unknown";
                }
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
                            //downloadButton.disabled = true;
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
                $(".list-group-item.fetch-jobs").attr("aria-disabled", "false").removeClass("disabled clicked");
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
    $("#jobProcessingTitle").html("Downloading job:<br>" + jobId + "<br>");
    await sleep(2000);
    setProgressBarValue(20);
    $.getJSON("/hh-neuron-builder/download-job/" + jobId + "/" + req_pattern + "/", function(data) {
        if (data["response"] == "KO") {
            closeDownloadJob();
            openErrorDiv(data["message"], "error");
            return false;
        }
        setProgressBarValue(50);
        $("#jobProcessingTitle").html("Running Analysis<br>");
        var p = $.getJSON("/hh-neuron-builder/run-analysis/" + req_pattern, function(modifydata) {
            var resp_flag = false;
            if (modifydata["response"] == "KO") {
                closeDownloadJob();
                openErrorDiv(data["message", "error"]);
                return false;
            } else {
                var resp_flag = true;
                setProgressBarValue(80);
                $("#jobProcessingTitle").html("Creating ZIP file<br>")
                $.getJSON("/hh-neuron-builder/zip-sim/" + jobId + "/" + req_pattern, async function(zip_data) {
                    if (zip_data["response"] == "KO") {
                        closeDownloadJob();
                        openErrorDiv(zip_data["message"], "error");
                        return false;
                    } else {
                        $("#jobProcessingTitle").html("Completing...<br>");
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
            hideLoadingAnimation();
            openReloadDiv();
        } else {
            hideLoadingAnimation();
            window.location.href = "/hh-neuron-builder/workflow/";
        }
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
            let win = window.open("/hh-neuron-builder/workflow/" + data.exc + "/" + data.ctx + "/", "_blank");
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
    showLoadingAnimation("Loading...");
    console.log("saveWorkflow() called.");
    $("#wf-btn-save").blur();
    fetch("/hh-neuron-builder/workflow-download/" + req_pattern, {
        method: "GET"
    }).then(
        data => {
            downloadURI(data.url, 'workflow'); 
            hideLoadingAnimation();
        }
    ).then(
       // hideLoadingAnimation()
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
    $("#overlayparam").addClass("upper-daint");
})

$("#serviceAccountCollapse")[0].addEventListener('show.bs.collapse', function () {
    $("#overlayparam").addClass("upper-sa-daint");
})
$("#nsgCollapse")[0].addEventListener('show.bs.collapse', function () {
    $("#overlayparam").addClass("upper-nsg");
})

$("#daintCollapse")[0].addEventListener('hide.bs.collapse', function () {
    $("#overlayparam").removeClass("upper-daint");
})

$("#serviceAccountCollapse")[0].addEventListener('hide.bs.collapse', function () {
    $("#overlayparam").removeClass("upper-sa-daint");
})
$("#nsgCollapse")[0].addEventListener('hide.bs.collapse', function () {
    $("#overlayparam").removeClass("upper-nsg");
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


function openFileManager(showConfig=false) {
    refreshHHFFileList();
    console.log("openFileManager() called with showConfi=" + showConfig.toString())
    if (showConfig) {
        showFileList($("#configFolder"));
    }

    console.log("fetchHHFFileList() on openFileManager()");
    $("#overlaywrapper").css("display", "block");
    $("#overlayfilemanager").css("display", "block");
    $("#overlayfilemanager").addClass("open");
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
                $("#mechanismsFileList").removeClass("empty-list");
            }
        } else {
            console.log("append Empty on modFileList");
            $("#mechanismsFileList").append("<div class='file-item empty'>Empty</div>");
            $("#mechanismsFileList").addClass("empty-list");
        }
        
        if (data.config && data.config.length > 0) {
            for (let i = 0; i < data.config.length; i++) {
                let name = data.config[i];
                $("#configFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>");
                $("#configFileList").removeClass("empty-list");
            }
        } else {
            $("#configFileList").append("<div class='file-item empty'>Empty</div>");
            $("#configFileList").addClass("empty-list");
        }

        if (data.model && data.model.length > 0) {
            for (let i = 0; i < data.model.length; i++) {
                let name = data.model[i];
                $("#modelFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>")
                $("#modelFileList").removeClass("empty-list");
            }
        } else {
            $("#modelFileList").append("<div class='file-item empty'>Empty</div>");
            $("#modelFileList").addClass("empty-list");
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
    // $(".file-textarea").css("display", "none");
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

    resetEditorMode();

    setModelKey(onClose=true);
    checkConditions();
};


$("#deleteFileButton").click(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    if ($(".file-item.active").length == 0 && $("editor-item.active").length == 0) {
        return false;
    }

    if ($(".file-item.active").length > 1) {
        $("#confirmationDialogModalTitle").html("Are you sure to delete these files ?");
    } else {
        $("#confirmationDialogModalTitle").html("Are you sure to delete this file ?");
    }
    $("#confirmationDialogModalCancelButton").html("Cancel");
    $("#confirmationDialogModalOkButton").html("Yes").attr("onclick", "deleteHHFFiles()");
    $("#confirmationDialogModal").modal("show");
});


function deleteHHFFiles() {

    if ($(".folder-item.active").attr("id") == "morphologyFolder") {
        if ($("#morphologyFileList").hasClass("empty-list")) {
            $("#uploadFileButton").removeClass("disabled");
        }
    }

    var jj_ids = {"id": []};

    if (editorMode) {
        if ($(".editor-item.active").length == 0) {
            return false;
        }
        jj_ids.id.push($(".editor-item.active").attr("name"));
    } else {
        if ($(".file-item.active").length == 0) {
            return false;
        }
        $(".file-item.active").each(function(i) {
            jj_ids.id.push($(this).attr("id"));
        });
    }

    fetch("/hh-neuron-builder/hhf-delete-files/" + $(".folder-item.active").attr("id") + "/" + req_pattern + "?file_list=" + encodeURIComponent(JSON.stringify(jj_ids)), {
        method: "GET"
    }).then(function(data) {
        console.log(data);
        refreshHHFFileList();
        loadEditor();
        console.log("refreshHHFFileList() on #deleteFileButton callback.")
    })
}


$("#downloadFileButton").click(function() {

    var jj_ids = {"id" : []};

    if (!editorMode) {
        if ($(".folder-item.active").attr("id") == "optNeuronFolder") {
            fetch("/hh-neuron-builder/hhf-download-files/optneuron/" + req_pattern)
                .then(data => downloadURI(data.url, 'opt_neuron.py'));
            return false;
        } 
        
        if ($(".file-item.active").length == 0) {
            return false;
        } else {
            $(".file-item.active").each(function(i) {
                jj_ids.id.push($(this).attr("id"));
            });
        }
    } else {
        if ($(".editor-item.active").length == 0) {
            return false;
        }
        jj_ids.id.push($(".editor-item.active").attr("name"));
    }
    
    showLoadingAnimation("Downloading files...");

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
    if ($(".folder-item.active").attr("id") == "mechanismsFolder") {
        input.setAttribute("multiple", "true");
    }
    input.setAttribute("multiple", "true");
    input.setAttribute("type", "file");
    input.click();
    
    var counter = 0;
    var files = 0

    const upload = (file) => {
        fetch("/hh-neuron-builder/hhf-upload-files/" + $(".folder-item.active").attr("id") + "/" + req_pattern + "/", {
            method: "POST",
            headers: {
                "Content-Type": "application/octet-stream",
                "Content-Disposition": "attachment; filename=\"" + file.name + "\""
            },
            body: file
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.response == "OK") {
                counter += 1;
                if (counter == files) {
                    hideLoadingAnimation();
                    refreshHHFFileList();
                    updateEditor();
                }
            } else {
                closeFileManager();
                openErrorDiv(data.message, "error");
            }
        });
    }

    const onSelectFile = async function(x) {        
        files = input.files.length;
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
        $(this).removeClass("active");
        $(".file-item").removeClass("active");
    } else {
        $(this).addClass("active");
        $(".file-group.active").children().addClass("active");
    }
})


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
    $(".file-code").css("display", "none");
    $(".ui-button").removeClass("disabled");
    
    hideFloatingOpenFileButton();


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
        showFloatingOpenFileButton();
    } else if (currFolder == "modelFolder") {
        currList = $("#modelFileList"); 
        $("#uploadFileButton").addClass("disabled");
        $("#deleteFileButton").addClass("disabled");
        showFloatingOpenFileButton();
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
    updateEditor();
})


let alpha = []
$("#modelKeyInput").on("input", function(){
    let k = $("#modelKeyInput").val()[0];
    if (k in [""]){
    }
})


function setModelKey(onClose=false) {
    var k = $("#modelKeyInput").val();
    fetch("/hh-neuron-builder/hhf-apply-model-key/" + req_pattern + "/" + k.toString(), {
        method: "GET"
    }).then( data => { 
        console.log(data)
        if (data.status == 200 && !onClose) {
            refreshHHFFileList();
        }    
    });
}


$("#infoFileManagerButton").click(function() {
    $("#modalHHF").modal("show");
});


function showFloatingOpenFileButton() {
    $("#editFileButton").addClass("show");
}

function hideFloatingOpenFileButton() {
    $("#editFileButton").removeClass("show");
    $("#saveFileButton").removeClass("show");
}

var editorMode = false;



$("#editFileButton").mousedown(function() {
    $(this).addClass("clicked")
})

$("#editFileButton").mouseup(function() {
    $(this).removeClass("clicked")
    if (editorMode && $("#saveFileButton").hasClass("show")) {
        $("#confirmationDialogModalTitle").html("Discards changes ?");
        $("#confirmationDialogModalCancelButton").html("No");
        $("#confirmationDialogModalOkButton").html("Yes").attr("onclick", "discardTextAreaChanges(true)");
        $("#confirmationDialogModal").modal("show");
    } else {
        switchMode();
    }
});

$("#editFileButton").mouseout(function() {
    $(this).removeClass("clicked")
})


function resetEditorMode() {
    editorMode = false;
    $("#folderselector").css("display", "block").removeClass("fade-out fade-in");
    $("#editorselector").css("display", "none").removeClass("fade-out fade-in");
    $("#fileselector").css("display", "block").removeClass("fade-out fade-in");
    $("#fileeditor").css("display", "none").removeClass("fade-out fade-in");
    $("#editFileButtonImage").removeClass("show zoomout").css("top", "8px").css("left", "2px").attr("src", "/static/assets/img/open-file-white.svg");
    $("#editFileButton").attr("title", "Open/Edit files");
    $("#editorfilelist").empty();
    $("#saveFileButton").removeClass("show disabled");
    $("#saveFileButtonSpinner").css("display", "none");
    $("#saveFileButtonImage").css("display", "inline");        
}


function switchMode() {
    let folderSelector = $("#folderselector");
    let editorSelector = $("#editorselector");
    let fileSelector = $("#fileselector");
    let fileEditor = $("#fileeditor")
    let editFileButtonImage = $("#editFileButtonImage");


    editorMode = !editorMode;
    
    folderSelector[0].addEventListener("animationend", function(){
        if (editorMode) {
            folderSelector.css("display", "none");
            editorSelector.css("display", "block");
            editorSelector.removeClass("fade-out").addClass("fade-in");
        }
    })
    editorSelector[0].addEventListener("animationend", function() {
        if (!editorMode) {
            editorSelector.css("display", "none");
            folderSelector.css("display", "block");
            folderSelector.removeClass("fade-out").addClass("fade-in")
        }
    })

    fileSelector[0].addEventListener("animationend", function() {
        if (editorMode) {
            fileSelector.css("display", "none");
            fileEditor.css("display", "block");
            fileEditor.removeClass("fade-out").addClass("fade-in");
        }
    })
    fileEditor[0].addEventListener("animationend", function() {
        if (!editorMode) {
            fileEditor.css("display", "none");
            fileSelector.css("display", "block");
            fileSelector.removeClass("fade-out").addClass("fade-in");
        }
    })
    editFileButtonImage[0].addEventListener("transitionend", function() {
        console.log(navigator.userAgent.toString().match("Chrome"));
        if (editorMode) {
            editFileButtonImage.addClass("back-arrow")
            if (!navigator.userAgent.toString().match("Chrome")) {
                editFileButtonImage.attr("src", "/static/assets/img/back-arrow-white.svg");
            } 
            $("#editFileButton").attr("title", "Go back");
        } else {
            editFileButtonImage.removeClass("back-arrow");
            if (!navigator.userAgent.toString().match("Chrome")) {
                editFileButtonImage.attr("src", "/static/assets/img/open-file-white.svg");
            }
            $("#editFileButton").attr("title", "Open/Edit files");
        }
        editFileButtonImage.removeClass("zoomout");
    })
    
    editFileButtonImage.addClass("zoomout");
    if (editorMode) {
        loadEditor();
        folderSelector.removeClass("fade-in").addClass("fade-out");
        fileSelector.removeClass("fade-in").addClass("fade-out");
        $("#selectAllButton").addClass("disabled");
    } else {
        editorSelector.removeClass("fade-in").addClass("fade-out");
        fileEditor.removeClass("fade-in").addClass("fade-out");
        $("#saveFileButton").removeClass("show");
        $("#selectAllButton").removeClass("disabled");
    }

};


function loadEditor() {
    $("#editorfilelist").empty();
    $(".file-group.active").children().each(function(i, el){
        $("#editorfilelist").append("<li name='" + el.id + "' class='list-group-item folder-item editor-item'  onclick='selectFileEditor($(this).attr(\"name\"))'>" + el.id + "</li>")
        $(".editor-item[name='" + $(".file-item.active").attr("id")).addClass("active");
    });


    $("#fileeditor").empty();

    $("#fileeditor").append("<div id='openafilediv' class='file-item empty' style='display:none'>Open a file</div>");
    $("#fileeditor").append("<div id='editor-spinner' class='spinner-border file-item-spinner' style='display:block' role='status'></div>")

    var currFolder = $(".folder-item.active").attr("id");
    var currFile = $(".file-item.active").attr("id");

    $.getJSON("/hh-neuron-builder/hhf-get-files-content/" + currFolder + "/" + req_pattern, function(data) {
        
        let jj = JSON.parse(data);
        let files = Object.keys(jj);

        for (let i = 0; i < files.length; i++) {

            if (currFolder == "modelFolder") {
                $("#fileeditor").append("<div name='" + files[i] + "' class='file-code' style='display:none'><pre><code name='" + files[i] + "' class='editor python'></code></pre></div>");
                $(".editor.python[name='" + files[i] + "']").html(jj[files[i]]);
                if (currFile) {
                    // enable current file
                    $("#editor-spinner").css("display", "none");
                    $(".file-code[name='" + currFile + "']").css("display", "block").addClass("active");
                }
            } else if(currFolder == "configFolder") {
                $("#fileeditor").append("<textarea name='" + files[i] + "' class='file-textarea' style='display:none'></textarea>");
                $(".file-textarea[name='" + files[i] + "']").val(jj[files[i]]);
                if (currFile) {
                    // enable current file
                    $("#editor-spinner").css("display", "none");
                    $(".file-textarea[name='" + currFile + "']").css("display", "block").addClass("active");
                    originalTextAreaVal = $(".file-textarea.active").val();
                    runCheckDiffWorker();
                }
            }
        } 
        hljs.highlightAll();
 
        if (!currFile) {
            $("#editor-spinner").css("display", "none");
            $("#openafilediv").css("display", "block");
        }
    });

}

function updateEditor() {
    if (editorMode) {
        loadEditor();
        originalTextAreaVal = null;
    }
}


var originalTextAreaVal = null;


function selectFileEditor(filename) {
    if ($("#editor-spinner").css("display") == "block") {
        return false;
    }

    console.log("selectFileEditor() called for file: " + filename.toString());
    $("#openafilediv").css("display", "none");
    $(".editor-item").removeClass("active");
    $(".editor-item[name='" + filename + "']").addClass("active");
    
    $(".file-code").css("display", "none").removeClass("active");
    $(".file-textarea").css("display", "none").removeClass("active");

    if ($(".folder-item.active").attr("id") == "configFolder") {
        $(".file-textarea[name='" + filename + "']").css("display", "block").addClass("active");
        console.log("set display:block on textarea of " + filename.toString());
        originalTextAreaVal = $(".file-textarea.active").val();
        runCheckDiffWorker();
    } else {
        $(".file-code[name='" + filename + "']").css("display", "block").addClass("active");
    }
}


async function runCheckDiffWorker() {
    if (window.Worker) {
        const checkDiffWorker = new Worker("/static/hhnb/js/checkDiffText.js");

        while(true) {
            checkDiffWorker.postMessage([$(".file-textarea.active").val(), originalTextAreaVal]);
            checkDiffWorker.onmessage = function(e) {
                if (e.data == "equals") {
                    $("#saveFileButton").removeClass("show");
                } else if (e.data == "different") {
                    $("#saveFileButton").addClass("show");
                }
            }
            await sleep(100);
            if (!editorMode) {
                break;
            }
        }

    } else {
        $("#saveFileButton").addClass("show");
    }
}


$("#saveFileButton").mousedown(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    $(this).addClass("clicked");
});

$("#saveFileButton").mouseup(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    $(this).removeClass("clicked").addClass("disabled");
    $("#saveFileButtonImage").css("display", "none");
    $("#saveFileButtonSpinner").css("display", "block");
    saveCurrentTextAreaVal();
});

$("#saveFileButton").mouseout(function() {
    $(this).removeClass("clicked");
});


function discardTextAreaChanges(switchmode=false) {
    $(".file-textarea.active").val(originalTextAreaVal);
    if (switchmode) {
        switchMode();
    }
}

function saveCurrentTextAreaVal() {
    var currFile = $(".file-textarea.active").attr("name");
    var currValue = $(".file-textarea.active").val();
    var jj = {};
    jj[currFile] = currValue;
    $.ajax({
        url: "/hh-neuron-builder/hhf-save-config-file/" + currFile + "/" + req_pattern,
        method: "POST",
        data: jj,
        success: function(data) {
            console.log(data);
            originalTextAreaVal = currValue;
            $("#saveFileButton").removeClass("show disabled");
            $("#saveFileButtonSpinner").css("display", "none");
            $("#saveFileButtonImage").css("display", "inline");
            $("#editorAlertText").removeClass("error").addClass("info").html("File saved successfully");
            $("#editorAlert").addClass("show");
        },
        error: function(error) {
            console.error(error);
            $("#saveFileButton").removeClass("disabled");
            $("#saveFileButtonSpinner").css("display", "none");
            $("#saveFileButtonImage").css("display", "inline");
            $("#editorAlertText").removeClass("info").addClass("error").html(JSON.parse(error.responseText).message);
            $("#editorAlert").addClass("show");
        }
    })
}


$("#editorAlert")[0].addEventListener("transitionend", async function(){
    await sleep(2000);
    $(this).removeClass("show");
});
