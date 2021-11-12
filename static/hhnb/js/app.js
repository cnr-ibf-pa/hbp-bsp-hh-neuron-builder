import Log from "./utils/logger.js";
import Workflow from "./workflow/workflow.js";
import { UploadFileDialog, OptimizationSettingsDialog, MessageDialog, ModelRegistrationDialog } from "./ui/components/dialog.js";

Log.enabled = true;

const exc = sessionStorage.getItem("exc");
const hhf_dict = sessionStorage.getItem("hhf_dict");
const workflow = new Workflow(exc, hhf_dict);


Log.debug(hhf_dict)


function checkRefreshSession(response) {
    console.log(response);
    if (response.status === 403 && response.responseJSON.refresh_url) {
        $.post("/hh-neuron-builder/session-refresh/" + exc, response.responseJSON )
            .done((result) => {
                document.location.href = "/hh-neuron-builder/workflow/" + exc;
            }).fail((error) => {
                alert("Can't refresh session automatically, please refresh page");
            })
    } 
}


$(document).ready(() => {
    if (workflow.getProps().hhf_flag) {
        $("#modalHHF").modal("show");
    }
})


// New workflow button callback
$("#wf-btn-new-wf").on("click", () => {
    showLoadingAnimation("Initializing workflow...");
    $.get("/hh-neuron-builder/initialize-workflow")
        .done((result) => {
            Log.debug(result)
            window.location.href = "/hh-neuron-builder/workflow/" + result.exc;
        }).fail((error) => {
            checkRefreshSession(error);
            Log.error("Status: " + error.status + " > " + error.responseText);
            MessageDialog.openErrorDialog(error.responseText);
        }).always(() => { hideLoadingAnimation() });
});

// Clone workflow button callback
$("#wf-btn-clone-wf").on("click", () => {
    showLoadingAnimation("Cloning current workflow...");
    let new_exc = null;
    $.ajax({
        url: "/hh-neuron-builder/clone-workflow/" + exc,
        method: "GET",
        async: false,
        success: (result) => {
            let win = window.open("/hh-neuron-builder/workflow/" + result.exc);
            win.focus();
        },
        error: (error) => {
            checkRefreshSession(error);
            Log.error("Status: " + error.status + " > " + error.responseText);
            let message = error.responseText;
            if (error.status == 404) {
                message = "Something goes wrong.<br>Try to reload the application.";
            }
            MessageDialog.openErrorDialog(message);
        }
    }).always(() => { hideLoadingAnimation() });
});

// Save workflow button callback
$("#wf-btn-save").on("click", () => {
    showLoadingAnimation("Generating archive...");
    $.get("/hh-neuron-builder/download-workflow/" + exc)
        .done((result) => {
            Log.debug(result);
            window.location.href = "/hh-neuron-builder/download-workflow/" + exc + "?zip_path=" + result.zip_path;
        }).fail((error) => {
            checkRefreshSession(error);
            Log.error(error);
        }).always(() => { hideLoadingAnimation() });
})


$("#loginButton").on("click", () => {
    showLoadingAnimation("Loading...");
    $.get("/hh-neuron-builder/store-workflow-in-session/" + exc)
        .done(() => { window.location.href = "/oidc/authenticate" })
        .fail((error) => {
            hideLoadingAnimation();
            checkRefreshSession(error);
            Log.error(error);
            MessageDialog.openInfoDialog("Please, manually download first and then reupload the current workflow once you're logged in.");
        });
    return false;
})


// File upload form submission
$("#uploadForm").submit(function (e) {
    e.preventDefault();

    let formFileData = new FormData($("#uploadForm")[0]);
    UploadFileDialog.close();

    Log.debug("Uploading data: ");
    for (let v of formFileData.values()) {
        Log.debug(v);
    }

    workflow.uploadFile(formFileData);
});

// enable upload file button when any file is selected
$("#formFile").on("change", () => {
    $("#uploadFormButton").prop("disabled", false);
})

// empty file input when upload dialog is closed
$("#cancelUploadFormButton").on("click", () => {
    Log.debug("closing UploadFileDialog");
    UploadFileDialog.close();
})

// display upload dialog and set file type to upload
$(".upload-btn").on("click", (button) => {
    Log.debug(button);
    $("#formFile").val(""); // clean formFile input
    switch (button.target.id) {
        case "feat-up-btn":
            UploadFileDialog.openFeatures();
            workflow.setUploadFileType("features");
            break;

        case "opt-up-btn":
            UploadFileDialog.openModel();
            workflow.setUploadFileType("model");
            break;

        case "opt-res-up-btn":
            UploadFileDialog.openAnalysisResult();
            workflow.setUploadFileType("analysis");
            break;

        default:
    }
});


// delete features
$(".delete-btn").on("click", (button) => {
    Log.debug(button);
    let file_list = ""
    switch (button.target.id) {
        case "del-feat-btn":
            if (workflow.getProps().etraces && !workflow.getUIFlags().features) {
                workflow.getProps().etraces = false;
                workflow.updateUI();
                break;
            } else {
                file_list = JSON.stringify({
                    "file_list": [
                        "config/features.json",
                        "config/protocols.json"
                    ]
                });
            }
            break;

        case "del-opt-btn":
            file_list = JSON.stringify({
                "file_list": [
                    "config/parameters.json",
                    "config/morph.json",
                    "morphology/*",
                    "mechanisms/*"
                ]
            });
            break;

        case "del-sim-btn":
            file_list = JSON.stringify({
                "file_list": [
                    "../results/*",
                    "../analysis/*"
                ]
            });
            break;

        default:
    }
    if (file_list != "") {
        workflow.deleteFiles(file_list);
    }
});


$(".download-btn").on("click", (button) => {
    Log.debug(button);
    let file_list = "";
    switch (button.target.id) {
        case "down-feat-btn":
            file_list = "pack=features";
            break;

        case "down-opt-set-btn":
            file_list = "pack=model";
            break;

        case "down-opt-btn":
            file_list = "pack=results";
            break;

        case "down-sim-btn":
            file_list = "pack=analysis";
            break;

        default:
    }
    workflow.downloadFiles(file_list)
});


// display and close settings dialog
$("#opt-set-btn").on("click", () => {
    Log.debug("Set parameters button clicked");
    let settings = workflow.getOptimizationSettings();
    Log.debug(settings);
    OptimizationSettingsDialog.loadSettings(settings);
    OptimizationSettingsDialog.open();
})

$("#cancel-param-btn").on("click", () => {
    Log.debug("Close parameters button clicked");
    OptimizationSettingsDialog.close();
})

$("#apply-param").on("click", () => {
    Log.debug("Uploading optimization settings");
    let formData = OptimizationSettingsDialog.getJsonData();
    if (formData.hpc == "DAINT-CSCS" || formData.hpc == "SA-CSCS") {
        showLoadingAnimation("Checking login...");
        $.get("/hh-neuron-builder/get-authentication")
            .done(() => {
                OptimizationSettingsDialog.close();
                workflow.uploadOptimizationSettings(formData);
            }).fail((error) => {
                checkRefreshSession(error);
                $("#hpcAuthAlert").addClass("show");        
            }).always(() => { hideLoadingAnimation() });
    } else {
        OptimizationSettingsDialog.close();
        workflow.uploadOptimizationSettings(formData);
    }    
})


/* NFE */

$("#feat-efel-btn").on("click", () => {
    // showLoadingAnimation("Loading...");
    if (workflow.getProps().etraces) {
        document.getElementById("efelgui-frame").setAttribute("src", "/efelg/hhf_etraces/" + exc);
    } else {
        document.getElementById("efelgui-frame").setAttribute("src", "/efelg/?ctx=" + exc);
    }

    $("#modalNFEContainer").css("display", "block");
    $("#modalNFE").css("z-index", "100").addClass("show");
})

$("#feat-efel-btn").on("click", () => {
    $("#modalNFEContainer").css("display", "block");
    $("#modalNFE").css("z-index", "100").addClass("show");
});

$("#closeNFEButton").on("click", () => {
    $("#modalNFEContainer").removeClass("show");
})

$("#save-feature-files").on("click", () => {
    var innerDiv = document.getElementById("efelgui-frame").contentDocument ||
        getElementById("efelgui-frame").contentWindow.document;
    var folderName = innerDiv.getElementById("hiddendiv").classList[0];

    showLoadingAnimation("Saving features...");

    $.post("/hh-neuron-builder/upload-features/" + exc, { "folder": folderName })
        .done((result) => {
            $("#modalNFEContainer").removeClass("show");
            workflow.updateProperties();
        }).fail((error) => {
            alert("Something goes wrong. Please download the Features files and upload them manually.");
        }).always(() => { hideLoadingAnimation() });
});

/* **** */

/* Model Catalog */

$("#opt-db-hpc-btn").on("click", chooseOptModel);
$("#closeModalMCButton").on("click", closeModelCatalog);

function closeModelCatalog() {
    $("#closeModalMCButton").removeClass("show");
    $("#modalMC").modal("hide");
}


var modelsReady = false;
function chooseOptModel() {
    if (modelsReady) {
        $("#modalMC").modal("show");
        $("#closeModalMCButton").css("display", "block").addClass("show");
        return false;
    }
    showLoadingAnimation("Fetching models from Model Catalog...");
    $.getJSON("/hh-neuron-builder/fetch-models/" + exc, { 'model': 'all' }, function (data) {
        var counter = 0;
        if (data.length == 0) {
            openErrorDiv("Something goes wrong.<br>Please restart the application.", "error");
            return;
        }
        $.each(data, function (idx, val) {
            $.each(val, function (index, e) {
                Log.debug(e);
                var model_uuid = e.id;
                var model_name = e.name;
                Log.debug(model_uuid);
                Log.debug(model_name);
                $("#modelCatalogContainer").append("<div  id=" + model_uuid + " name=" +
                    model_name + " class='mc-model main-content model-info-div'></div>");
                $("#" + model_uuid).append(
                    "<div id=" + model_uuid + " class='row model-info-div-title'><div class='col'></div><div id=" + model_uuid + " class='col flex-grow-4 flex-center'>" + e['species'] + ' > ' + e['brain_region'] + ' > ' + e['cell_type'] + ' > ' + model_name + "</div><div class='col flex-grow-1 flex-end'><i id='" + model_uuid + "' class='fas fa-external-link-alt fa-lg' title='Open in ModelCatalog'></i></div></div>"
                );
                $("#" + model_uuid).append("<div style='display:flex;' id=" + model_uuid + 'a' + " ></div>");
                var img_div = document.createElement("DIV");
                var spk_img = document.createElement("IMG");
                var mor_img = document.createElement("IMG");
                var mor_id = "crr_mor";
                var spk_id = "crr_spk";
                var spk_url = e.images[1].url;
                var mor_url = e.images[0].url;
                img_div.setAttribute("style", "max-width:60%;");
                mor_img.setAttribute("id", mor_id);
                mor_img.setAttribute("style", "max-width:50%;");
                spk_img.setAttribute("id", spk_id);
                spk_img.setAttribute("style", "max-width:50%;");
                spk_img.setAttribute("src", spk_url);
                mor_img.setAttribute("src", mor_url);
                img_div.append(spk_img);
                img_div.append(mor_img);
                $("#" + model_uuid + 'a').append(img_div);
                $('#' + model_uuid + 'a').append("<div style='max-width:40%;padding:5px;font-size:13px'>" + formatDescription(e) + "</div>");
            });
        });
        $("#modalMC").modal("show");
        $("#closeModalMCButton").css("display", "block").addClass("show");
        $(".fa-external-link-alt").on("click", (button) => {
            let id = button.currentTarget.getAttribute("id")
            let win = window.open("https://model-catalog.brainsimulation.eu/#model_id." + id);
            win.focus();
            return false;
        })
        $(".mc-model").on("click", (button) => {
            closeModelCatalog();
            let optimization_id = button.currentTarget.getAttribute("id");

            showLoadingAnimation("Fetching model from the HBP Model Catalog");

            $.get("/hh-neuron-builder/fetch-models/" + exc, { "model": optimization_id })
                .done((result) => {
                    Log.debug(result);
                    workflow.updateProperties();
                }).fail((error) => {
                    checkRefreshSession(error);
                    Log.error(error);
                }).always(() => { hideLoadingAnimation() })
        });
    }).done(() => {
        modelsReady = true;
    }).fail((error) => {
        checkRefreshSession(error);
        Log.error(error);
        MessageDialog.openInfoDialog(error.responseText);
    }).always(() => { hideLoadingAnimation() });
}

function formatDescription(meta = "") {
    var description = meta['description']
    var indexes = [];
    var all_strings = [];
    var final_string = "";
    var final_string_meta_app = "";
    var final_string_author_app = "";
    var final_string_meta_title = "<span style='font-size:16px'><br>Description<br></span>";
    var final_string_author_title = "<span style='font-size:16px'><br><br><br>Credits<br></span>";
    var allowed_tag_meta = [
        "brain_structure", "cell_soma_location",
        "cell_type", "channels", "e_type", "morphology"
    ];
    var allowed_tag_author = ["contributors", "email", "affiliations"]
    var res = description.replace(/\\\_/g, "_");

    var index = 0;
    while (index > -1) {
        index = res.indexOf('<br>');
        if (index == 0) {
            if (res.length >= 4) {
                res = res.slice(4,);
            } else {
                index == -1;
            }
        } else if (index > -1) {
            all_strings.push(res.slice(0, index));
            res = res.slice(index + 4,);
        }
    }
    for (var i = 0; i < all_strings.length; i++) {
        for (var j = 0; j < allowed_tag_meta.length; j++) {
            if (all_strings[i].indexOf(allowed_tag_meta[j]) > -1) {
                final_string_meta_app = final_string_meta_app + "<br>" + all_strings[i];
                break
            }
        }
        for (var z = 0; z < allowed_tag_author.length; z++) {
            if (all_strings[i].indexOf(allowed_tag_author[z]) > -1) {
                final_string_author_app = final_string_author_app + "<br>" + all_strings[i];
                break
            }
        }
    }
    final_string_meta_app = final_string_meta_app + "<br><strong>" + "id : " + "</strong>" + meta["id"]
    if (final_string_meta_app.length > 1) {
        final_string = final_string + final_string_meta_title + final_string_meta_app;
    }
    if (final_string_author_app.length > 1) {
        final_string = final_string + final_string_author_title + final_string_author_app;
    }

    return final_string
}

/* *************** */

$("#launch-opt-btn").on("click", () => {
    workflow.runOptimization();

})

$("#closeFileManagerButton").on("click", () => {
    Log.debug("CLOSING FILE MANAGER");
    closeFileManager();
    workflow.updateProperties();
})





/* FETCH JOBS */


$("#opt-fetch-btn").on("click", () => {
    Log.debug('Fetch job');
    $("#overlayjobs").css("display", "block");
    // $("#overlaywrapper").css("z-index", "100").addClass("show");
    $("#overlaywrapper").css("display", "block");
    $(".list-group-item.fetch-jobs").attr("aria-disabled", "false").removeClass("disabled active");
});

$("#cancel-job-list-btn").on("click", closeJobFetchDiv);

function closeJobFetchDiv() {
    Log.debug('Close job fetch');
    resetJobFetchDiv();
    $("#overlayjobs").removeClass("show scroll-long-content");
    $("#overlayjobs").css("display", "none");
    $("#overlaywrapper").css("display", "none");
}

$("#refresh-job-list-btn").on("click", () => {
    $("#overlayjobs").removeClass("scroll-long-content");
    $("#job-list-body").empty();
    $("#tableRow").css("display", "none");
    $("#refresh-job-list-btn").prop("disabled", true);
    resetProgressBar();
    displayJobList($(".list-group-item.fetch-jobs.active"));
});


// var is_user_authenticated = sessionStorage.getItem("isUserAuthenticated");

function dismissAlert(el) {
    console.log($(el).parent().removeClass("show"));
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


// Manage job list div
$(".jobs-unicore").on("click", (button) => {
    let jButton = $("#" + button.target.id);
    Log.debug(jButton);
    if (jButton.hasClass("clicked")) {
        return false;
    }
    resetJobFetchDiv();
    $.get("/hh-neuron-builder/get-authentication")
        .done(() => {
            jButton.addClass("clicked");
            displayJobList(jButton);
        })
        .fail((error) => { 
            checkRefreshSession(error);
            $("#jobsAuthAlert").addClass("show");
        });
});

$("#jobsNSG").on("click", (button) => {
    let jButton = $("#" + button.target.id);
    if (jButton.hasClass("clicked")) {
        return false;
    }
    resetJobFetchDiv();
    $("#jobsNSG").addClass("active");
    $("#tableRow").css("display", "none");
    $("#nsgLoginRow").css("display", "flex");
    jButton.addClass("clicked");
});


function displayJobList(button) {
    $("#overlayjobs").removeClass("scroll-long-content");
    $("#cancel-job-list-btn").prop("disabled", true);
    $("#spinnerRow").css("display", "flex");
    $(".list-group-item.fetch-jobs").addClass("disabled").attr("aria-disabled", "true");
    button.attr("aria-disabled", "false").removeClass("disabled").addClass("active");
    let hpc = button.attr("name");

    $.getJSON("/hh-neuron-builder/fetch-jobs/" + exc, { hpc })
        .done((results) => {
            let jobs = results.jobs;
            for (let job_id of Object.keys(jobs)) {
                let job = jobs[job_id];
                let statusColor = "";
                if (job.status == "COMPLETED" || job.status == "SUCCESSFUL" || job.status == "FAILED") {
                    statusColor = "#00802b"
                    if (job.status == "FAILED") {
                        statusColor = "#DD9900";
                    }
                } else {
                    statusColor = "#DD9900";
                }

                $("#job-list-body").append(
                    "<tr>"
                    + "<td>" + job.workflow_id + "</td>"
                    + "<td>" + job_id.toUpperCase() + "</td>"
                    + "<td style='font-weight: bold; color: " + statusColor + "'>" + job.status + "</td>"
                    + "<td>" + job.date + "</td>"
                    + "<td>"
                    + "<button type='button' id='" + job_id + "' class='btn workflow-btn job-download-button'>Download</button>"
                    + "</td>"
                    + "</tr>"
                )
            }

            $(".job-download-button").on("click", (button) => {
                closeJobFetchDiv();
                openJobProcessingDiv();
                downloadJob(button.target.id);
            });

            $("#spinnerRow").css("display", "none");
            $("#progressRow").css("display", "none");
            $("#tableRow").css("display", "flex");
            $("#refresh-job-list-btn").prop("disabled", false).blur();
            $("#cancel-job-list-btn").prop("disabled", false);
            $(".list-group-item.fetch-jobs").attr("aria-disabled", "false").removeClass("disabled clicked");
            
            let windowHeight = $(window).height();
            let overlayJobsHeight = $("#overlayjobs").height();
            if (overlayJobsHeight > (windowHeight - (windowHeight / 10))) {
                $("#overlayjobs").addClass("scroll-long-content");
            }
        }).fail((error) => {
            checkRefreshSession(error);
            Log.error("Status: " + error.status + " > " + error.responseText);
            MessageDialog.openErrorDialog(error.responseText);
        });
}

function animateProgressBar(progress) {
    let current_progress = parseFloat($(".progress-bar").attr("aria-valuenow"));
    let next_progress = current_progress + progress;
    $(".progress-bar").css("width", next_progress + "%").attr("aria-valuenow", next_progress);
    // console.log($(".progress-bar").css("width"));
    // console.log($(".progress-bar").attr("aria-valuenow"));
}

function setProgressBarValue(value) {
    $(".progress-bar").css("width", parseInt(value) + "%").attr("aria-valuenow", parseInt(value));
}

function resetProgressBar() {
    $(".progress-bar").css("width", "0%").attr("aria-valuenow", "0");
}

/* 
function setJobProcessingTitle(message) {
    console.log(message);
    var title = $("#jobProcessingTitle");

    function eventListener(transition) {
        if (transition.target == title[0]) {
            if (title.hasClass("fade-text")) {
                title.html(message);
                title.removeClass("fade-text");
                title[0].removeEventListener("transitionend", eventListener);
            }
        }
    }
    title[0].addEventListener("transitionend", eventListener);
    title.addClass("fade-text");
} */
function setJobProcessingTitle(message) {
    $("#jobProcessingTitle").html(message);
}

function openJobProcessingDiv() {
    $("#overlaywrapper").css("display", "block");
    $("#overlayjobprocessing").css("display", "block");
    setProgressBarValue(0);
    // $("#overlayjobprocessing").removeClass("show");
    // $("#overlayjobs").addClass("hide-to-left");
}

function closeJobProcessingDiv() {
    $("#overlaywrapper").css("display", "none");
    $("#overlayjobprocessing").css("display", "none");
    setProgressBarValue(0);
    // $("#overlayjobprocessing").removeClass("show");
    // $("#overlayjobs").addClass("hide-to-left");
}

async function downloadJob(jobId) {
    Log.debug("Downloading " + jobId);
    // disable all buttons
    let data = { "job_id": jobId, "hpc": $("button.fetch-jobs.active").attr("name") }

    $("#jobProcessingTitle").html("Downloading job:<br>" + jobId.toUpperCase() + "<br>");

    closeJobFetchDiv();
    openJobProcessingDiv();

    await sleep(500);
    $("#progressBarFetchJob").addClass("s40").removeClass("s4 s2");
    setProgressBarValue(40);

    $.get("/hh-neuron-builder/fetch-job-result/" + exc, data)
        .done((downloadResult) => {
            Log.debug(downloadResult);
            setJobProcessingTitle("Running Analysis<br>");
            setProgressBarValue(80);
            $.get("/hh-neuron-builder/run-analysis/" + exc)
                .done(async (analysisResult) => {
                    setJobProcessingTitle("Completing...<br>");
                    $("#progressBarFetchJob").addClass("s4").removeClass("s40 s2");
                    setProgressBarValue(100);
                    await sleep(4000);
                    closeJobProcessingDiv(); 
                    workflow.updateProperties();
                }).fail((analysisError) => {
                    checkRefreshSession(error);
                    Log.error("Status: " + analysisError.status + " > " + analysisError.responseText);
                    closeJobProcessingDiv();
                    MessageDialog.openErrorDialog(analysisError.responseText);
                    workflow.updateProperties();
                })
        }).fail((downloadError) => {
            checkRefreshSession(error);
            closeJobProcessingDiv();
            Log.error("Status: " + downloadError.status + " > " + downloadError.responseText);
            MessageDialog.openErrorDialog(downloadError.responseText)
            workflow.updateProperties();
        });
}

$("#checkNsgLoginButton").on("click", () => {
    $("#checkNsgSpinnerButton").css("opacity", "1");

    let data = {
        "username": $("#usernameNsg").val(),
        "password": pass$("#passwordNsg").val()
    };
    $.post("/hh-neuron-builder/get-authentication", data)
        .done(() => {
            $("#checkNsgSpinnerButton").css("opacity", "0");
            $("#usernameNsg").removeClass("is-invalid");
            $("#passwordNsg").removeClass("is-invalid");
            $("#nsgLoginRow").css("display", "none");
            displayJobList($("#jobsNSG"));
        }).fail(() => {
            $("#checkNsgSpinnerButton").css("opacity", "0");
            $("#usernameNsg").addClass("is-invalid").attr("aria-describedby", "User not valid");
            $("#passwordNsg").addClass("is-invalid").attr("aria-describedby", "Password not valid");
        })
});


/* ****************************** */

$("#run-sim-btn").on("click", () => {
    /* showLoadingAnimation("Uploading to BlueNaas...");
    $("#run-sim-btn").prop("disable", true);
    $.get("/hh-neuron-builder/upload-to-naas/" + exc)
        .done((data) => {
            Log.debug("Filename uploaded " + data);
            $("#bluenaas-frame").attr("src", "https://blue-naas-bsp-epfl.apps.hbp.eu/#/model/" + data);
            $("#bluenaas-frame").on("load", function () {
                hideLoadingAnimation();
                $("#modalBlueNaasContainer").css("display", "block");
                $("#modalBlueNaas").css("z-index", "100").addClass("show");
            })
        }).fail((error) => {
            checkRefreshSession(error);
            Log.error("Status: " + downloadError.status + " > " + downloadError.responseText);
            MessageDialog.openErrorDialog(downloadError.responseText);
            hideLoadingAnimation();
        }).always(() => {
            $("#run-sim-btn").prop("disable", false);
        }) */
    
    ModelRegistrationDialog.open();
})


$("#back-to-wf-btn").on("click", () => {
    $("#modalBlueNaasContainer").removeClass("show");
});


/*          Registration Model           */

$("#reg-mod-mail-btn").on("click", () => {
    ModelRegistrationDialog.open();
})

$("#cancel-model-register-btn").on("click", () => {
    ModelRegistrationDialog.close();
})


/* ************************************* */