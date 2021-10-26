import { MessageDialog, OptimizationSettingsDialog } from "../ui/components/dialog.js";
import Log from "../utils/logger.js";


const GET_PROPS_BASE_URL = "/hh-neuron-builder/get-workflow-properties/";
const UPLOAD_FILES_BASE_URL = "/hh-neuron-builder/upload-files/";


const featuresFiles = JSON.stringify({
        "file_list": [
            "config/features.json", 
            "config/protocols.json"
        ]
});

function enable(jObj) {
    jObj.prop("disabled", false);
}

function disable(jObj) {
    jObj.prop("disabled", true);
}


export default class Workflow {

    #exc = null;
    #props = null;
    
    #uploadFileType = null;


    #featuresBlock = false;
    #optfilesBlock = false;
    #optsettingsBlock = false;

    constructor(exc) { 
        this.#exc = exc;
        this.updateProperties();
    }

    getProps() {
        return this.#props;
    }

    getUIFlags() {
        return {
            'features': this.#featuresBlock,
            'optimization_files': this.#optfilesBlock,
            'optimization_settings': this.#optsettingsBlock
        }
    }

    updateProperties() {
        showLoadingAnimation("Loading...");
        $.ajax({
            url: GET_PROPS_BASE_URL + this.#exc,
            method: "GET",
            async: false,
            success: (props) => {
                this.#props = props;
                $("#wf-title").text("Workflow id: " + this.#props.id);
                Log.debug(this.#props);
            },
            error: (error) => {
                Log.error("Status: " + error.status + " > " + error.responseText);
                if (error.status == 404) {
                    MessageDialog.openReloadDialog();
                }
            }
        }).done(() => { this.updateUI() })
        .fail((error) => {
            if (error.status == 500) {
                return MessageDialog.openReloadDialog("/hh-neuron-builder", "<b>A critical error occurred</b>.<br>Please restart the application and if the the problem persists contact us.");
            }
        })
        .always(() => { hideLoadingAnimation() });
    }

    #updateFeaturesUIBlock() {
        let features = this.#props.model.features.features;
        let protocols = this.#props.model.features.protocols;
        let bar = $("#feat-bar");
        let nfeButton = $("#feat-efel-btn");
        let uploadButton = $("#feat-up-btn");
        let downloadLink = $("#down-feat-btn");
        let deleteLink = $("#del-feat-btn");

        if (features != "" && protocols != "") {
            bar.html(features + "<br>" + protocols);
        } else if (features != "" && protocols == "") {
            bar.text(features);
        } else {
            bar.text(protocols);
        }
        bar.removeClass("green orange").addClass("red");
        enable(nfeButton);
        enable(uploadButton);
        disable(downloadLink);
        disable(deleteLink);
        this.#featuresBlock = false;

        if (features == "" && protocols == "") {
            bar.removeClass("red orange").addClass("green");
            bar.text("");
            disable(nfeButton);
            disable(uploadButton);
            enable(downloadLink);
            enable(deleteLink);
            this.#featuresBlock = true
        } else if (this.#props.etraces) {
            bar.removeClass("red green").addClass("orange");
            bar.text("Extract features from fetched etraces");
            disable(uploadButton);
            disable(downloadLink);
            disable(uploadButton);
            enable(deleteLink);
        }
    }

    #updateModelBlock() {
        let morphology = this.#props.model.optimization_files.morphology.morphology;
        let mechanisms = this.#props.model.optimization_files.mechanisms;
        let parameters = this.#props.model.optimization_files.parameters;
        let bar = $("#opt-files-bar");
        let chooseOptModelButton = $("#opt-db-hpc-btn");
        let uploadModelButton = $("#opt-up-btn");
        let downloadLink = $("#down-opt-set-btn");
        let deleteLink = $("#del-opt-btn");

        if (morphology == "" && mechanisms == "" && parameters == "") {
            bar.removeClass("red").addClass("green");
            bar.text("");
            disable(chooseOptModelButton);
            disable(uploadModelButton);
            enable(downloadLink);
            enable(deleteLink);
            this.#optfilesBlock = true;
        } else {
            bar.removeClass("green").addClass("red");
            bar.html(morphology + "<br>" + mechanisms + "<br>" + parameters);
            enable(chooseOptModelButton);
            enable(uploadModelButton);
            disable(downloadLink);
            disable(deleteLink);
            this.#optfilesBlock = false;
        }
    }

    #updateSettingsBlock() {
        let bar = $("#opt-param-bar");
        if (this.#props.optimization_settings) {
            bar.addClass("green").removeClass("red");
            bar.text("");
            this.#optsettingsBlock = true;
        } else {
            bar.addClass("red").removeClass("green");
            bar.text("Optimization parameters NOT set");
            this.#optsettingsBlock = false;
        }
    }

    #updateCellOptimizationBlock() {
        let runOptimizationButton = $("#launch-opt-btn");
        if (this.#featuresBlock && this.#optfilesBlock && this.#optsettingsBlock) {
            enable(runOptimizationButton);
        } else {
            disable(runOptimizationButton);
        }
    }

    updateUI() {
        this.#updateFeaturesUIBlock();
        this.#updateModelBlock();
        this.#updateSettingsBlock();
        this.#updateCellOptimizationBlock();
    }
    
    #deleteFiles(jFilesList) {
        showLoadingAnimation("Deleting files...")
        Log.debug("Deleting files: " + jFilesList);
        $.ajax({
            url: "/hh-neuron-builder/delete-files/" + this.#exc,
            method: "POST",           
            dataType: "json",
            contentType: "application/json",
            data: jFilesList,
            success: (result) => { 
                Log.debug(result);
                this.updateProperties();
            },
            error: (error) => { 
                Log.error("Status: " + error.status + " > " + error.responseText); 
                MessageDialog.openErrorDialog(error.responseText);
            },
        }).always(() => { hideLoadingAnimation() });
    }

    setUploadFileType(fileType) {
        this.#uploadFileType = fileType;
    }
    
    uploadFile(formFileData) {
        showLoadingAnimation("Uploading file/s...");
        Log.debug("Uploading files");
        $.ajax({
            url: "/hh-neuron-builder/upload-" + this.#uploadFileType + "/" + this.#exc,
            method: "POST",
            data: formFileData,
            contentType: false, // need to upload files correctly
            processData: false,
            async: false,
            success: (result) => { 
                Log.debug(result);
                this.updateProperties();
            },
            error: (error) => { 
                Log.error("Status: " + error.status + " > " + error.responseText); 
                MessageDialog.openErrorDialog(error.responseText);
            },
        }).always(() => { hideLoadingAnimation();});
    }

    deleteFeatures() {
        let file_list = JSON.stringify({
                "file_list": [
                    "config/features.json", 
                    "config/protocols.json"
                ]
            });
        this.#deleteFiles(file_list);
    }

    deleteModel() {
        let file_list = JSON.stringify({
            "file_list": [
                "config/parameters.json",
                "config/morph.json",
                "morphology/*",
                "mechanisms/*"
            ]
        });
        this.#deleteFiles(file_list);
    }

    deleteAnalysis() {

    }

    downloadFiles(jFilesList) {
        showLoadingAnimation("Generating download package...");
        $.get("/hh-neuron-builder/download-files/" + this.#exc + "?" + jFilesList)
            .done((result) => {
                Log.debug("Files downloaded correctly");
                window.location.href = "/hh-neuron-builder/download-files/" + this.#exc + "?" + jFilesList;
            }).fail((error) => {
                Log.error("Status: " + error.status + " > " + error.responseText); 
                MessageDialog.openErrorDialog(error.responseText);
            }).always(() => { hideLoadingAnimation() });
    } 

    downloadFeatures() {
        let file_list = "pack=features";
        this.downloadFiles(file_list);
    }

    downloadModel() {
        let file_list = "pack=model";
        this.downloadFiles(file_list);
    }

    downloadAnalysis() {

    }

    getOptimizationSettings() {
        let settings = null;
        showLoadingAnimation("Getting settings...");
        $.ajax({
            url: "/hh-neuron-builder/optimization-settings/" + this.#exc,
            method: "GET",
            async: false,
            headers: {"Accept": "application/json"},
            success: (result) => {
                // Log.debug(result);
                settings = result;
                if (settings.hpc == "NSG") {
                    $("#username_submit").removeClass("is-invalid").addClass("is-valid");
                    $("#password_submit").removeClass("is-invalid").addClass("is-valid");
                }
            },
            error: (error) => {
                Log.error("Status: " + error.status + " > " + error.responseText); 
                MessageDialog.openErrorDialog(error.responseText);
            }
        }).always(() => { hideLoadingAnimation() });
        return settings;
    }

    uploadOptimizationSettings(jData) {
        showLoadingAnimation("Loading...");
        Log.debug("Uploading settings");
        $.ajax({
            url: "/hh-neuron-builder/optimization-settings/" + this.#exc,
            method: "POST",
            data: JSON.stringify(jData),
            processData: false,
            contentType: false,
            async: false,
            success: (result) => { 
                Log.debug(result)
                if (jData.hpc == "NSG") {
                    $("#username_submit").removeClass("is-invalid").addClass("is-valid");
                    $("#password_submit").removeClass("is-invalid").addClass("is-valid");
                }
                this.updateProperties();
            },
            error: (error) => { 
                Log.error("Status: " + error.status + " > " + error.responseText); 
                MessageDialog.openErrorDialog(error.responseText);
                if (error.responseText == "Invalid credentials") {
                    $("#username_submit").removeClass("is-valid").addClass("is-invalid");
                    $("#password_submit").removeClass("is-valid").addClass("is-invalid");
                }
            }
        }).always(() => { hideLoadingAnimation() });
    }

    runOptimization() {
        showLoadingAnimation("Run optimization on HPC system...");
        Log.debug("Run optimization");
        $.ajax({
            url: "/hh-neuron-builder/run-optimization/" + this.#exc,
            method: "GET",
            async: false,
            success: (result) => {
                Log.debug(result);
                MessageDialog.openSuccessDialog(result.responseText);
            },
            error: (error) => {
                Log.error("Status: " + error.status + " > " + error.responseText);
                MessageDialog.openErrorDialog(error.responseText);
            }
        }).always(() => { hideLoadingAnimation() });
    }

}