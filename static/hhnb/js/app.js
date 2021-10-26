import Log from "./utils/logger.js";
import Workflow from "./workflow/workflow.js";
import { UploadFileDialog, OptimizationSettingsDialog, MessageDialog } from "./ui/components/dialog.js";

Log.enabled = true;

const exc = sessionStorage.getItem("exc");
const hhf_dict = sessionStorage.getItem("hhf_dict");
const workflow = new Workflow(exc, hhf_dict);

/* 
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

 */


// New workflow button callback
$("#wf-btn-new-wf").on("click", () => {
    showLoadingAnimation("Initializing workflow...");
    $.get("/hh-neuron-builder/initialize-workflow")
        .done((result) => {
            Log.debug(result)
            window.location.href = "/hh-neuron-builder/workflow/" + result.exc;
        }).fail((error) => {
            Log.error("Status: " + error.status + " > " + error.responseText);
            MessageDialog.openErrorDialog(error.responseText);
        }).always(() => { hideLoadingAnimation() });
});

// Clone workflow button callback
$("#wf-btn-clone-wf").on("click", () => {
    showLoadingAnimation("Cloning current workflow...");
    let new_exc = null;
    $.ajax({
        url: "/hh-neuron-builder/clone-workflow/"+ exc,
        method: "GET",
        async: false,
        success: (result) => {
            let win = window.open("/hh-neuron-builder/workflow/" + result.exc);
            win.focus();
        },
        error: (error) => {
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
            Log.error(error);
        }).always(() => {hideLoadingAnimation() });
})


// File upload form submission
$("#uploadForm").submit(function(e) {
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
})

// delete features
$(".delete-btn").on("click", (button) => {
    Log.debug(button);
    switch (button.target.id) {
        case "del-feat-btn":
            if (workflow.getProps().etraces && !workflow.getUIFlags().features) {
                workflow.getProps().etraces = false;
                workflow.updateUI();
            } else {
                workflow.deleteFeatures();
            }
            break;
        
            case "del-opt-btn":
            workflow.deleteModel();
            break;
        
            case "del-sim-btn":
            workflow.deleteAnalysis();
            break;
        
        default:
    }
})

$(".download-btn").on("click", (button) => {
    Log.debug(button);
    switch (button.target.id) {
        case "down-feat-btn":
            workflow.downloadFeatures();
            break;
        
        case "down-opt-set-btn":
            workflow.downloadModel();
            break;

        default:
    }
})


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
    workflow.uploadOptimizationSettings(formData);
    OptimizationSettingsDialog.close();
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

    $.post("/hh-neuron-builder/upload-features/" + exc, {"folder": folderName})
        .done((result) => {
            console.log(result);
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
    $.getJSON("/hh-neuron-builder/fetch-models/" + exc, {'model': 'all'}, function(data){
        var counter = 0;
        if (data.length == 0) {
            openErrorDiv("Something goes wrong.<br>Please restart the application.", "error");
            return;
        }
        $.each(data, function(idx, val){
            $.each(val, function(index, e){
                Log.debug(e);
                var model_uuid = e.id;
                var model_name = e.name;
                Log.debug(model_uuid);
                Log.debug(model_name);
                $("#modelCatalogContainer" ).append("<div  id=" + model_uuid + " name=" +
                        model_name + " class='mc-model main-content model-info-div'></div>");
                $("#" + model_uuid).append(
                    "<div id=" + model_uuid + " class='row model-info-div-title'><div class='col'></div><div id=" + model_uuid + " class='col flex-grow-4 flex-center'>" + e['species'] + ' > ' + e['brain_region'] + ' > ' +  e['cell_type'] + ' > ' + model_name + "</div><div class='col flex-grow-1 flex-end'><i id='" + model_uuid + "' class='fas fa-external-link-alt fa-lg' title='Open in ModelCatalog'></i></div></div>"
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

            $.get("/hh-neuron-builder/fetch-models/" + exc, {"model": optimization_id})
                .done((result) => {
                    Log.debug(result);
                    workflow.updateProperties();
                }).fail((error) => {
                    Log.error(error);
                }).always(() => { hideLoadingAnimation() })
        });
    }).done(() => {
        modelsReady = true;
    }).fail((error) => {
        Log.error(error);
        MessageDialog.openInfoDialog(error.responseText);
    }).always(() => { hideLoadingAnimation() });
}

function formatDescription(meta = ""){
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
        if (index == 0){
            if (res.length >=4){
                res = res.slice(4,);
            } else {
                index == -1;
            }
        } else if (index > -1){
            all_strings.push(res.slice(0, index));
            res = res.slice(index + 4,);
        }
    }
    for (var i = 0; i < all_strings.length; i++){
        for (var j = 0; j < allowed_tag_meta.length; j++){
            if (all_strings[i].indexOf(allowed_tag_meta[j]) > -1){
                final_string_meta_app =  final_string_meta_app + "<br>" + all_strings[i];
                break
            }
        }
        for (var z = 0; z < allowed_tag_author.length; z++){
            if (all_strings[i].indexOf(allowed_tag_author[z]) > -1){
                final_string_author_app =  final_string_author_app + "<br>" + all_strings[i];
                break
            }
        }
    }
    final_string_meta_app = final_string_meta_app + "<br><strong>" + "id : " + "</strong>" + meta["id"]
    if (final_string_meta_app.length > 1){
        final_string = final_string + final_string_meta_title + final_string_meta_app;
    }
    if (final_string_author_app.length > 1){
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