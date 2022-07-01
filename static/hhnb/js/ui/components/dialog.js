import Log from "../../utils/logger.js";


class MessageDialog {

    static #overlayWrapper = $("#overlaywrapperdialog");
    static #overlayContent = $("#overlaycontentdialog");
    static #overlayDialog = $("#overlaydialog");
    static #dialogMessage = $("#dialogtext");
    static #dialogButton = $("#dialog-btn");


    static #openMessageDialog(msg) {
        if (!msg.startsWith("{\"refresh_url\"")) {
            this.#overlayWrapper.css("display", "block");
            this.#overlayContent.css("display", "block");
            this.#dialogMessage.html(msg);
        }
    }

    static #closeMessageDialog() {
        this.#overlayWrapper.css("display", "none");
        this.#overlayContent.css("display", "none");
    }

    static openSuccessDialog(msg) {
        this.#overlayContent.css("box-shadow", "0 0 1rem 1rem rgba(0, 128, 0, .8)")
            .css("border-color", "green");
        this.#dialogButton.text("Ok")
            .addClass("green").removeClass("blue red fill-background")
            .on("click", () => { this.#closeMessageDialog() });
        this.#openMessageDialog(msg);
    }

    static openErrorDialog(msg) {
        this.#overlayContent.css("box-shadow", "0 0 1rem 1rem rgba(255, 0, 0, .8)")
            .css("border-color", "red");
        this.#dialogButton.text("Ok")
            .addClass("red").removeClass("blue green fill-background")
            .on("click", () => { this.#closeMessageDialog() });
        this.#openMessageDialog(msg);
    }

    static openInfoDialog(msg) {
        this.#overlayContent.css("box-shadow", "0 0 1rem 1rem rgba(0, 0, 255, .8)")
            .css("border-color", "blue");
        this.#dialogButton.text("Ok")
            .addClass("blue").removeClass("red green fill-background")
            .on("click", () => { this.#closeMessageDialog() });
        this.#openMessageDialog(msg);
    }

    static openReloadDialog(href, msg) {
        this.#overlayDialog.addClass("reload-content")
            .removeClass("error-content info-content");
        this.#dialogButton.addClass("fill-background");
        this.#dialogButton.text("Reload").on("click", () => {
            if (href == null) {
                window.location.href = "/hh-neuron-builder";
            } else {
                window.location.href = href;
            }
        });
        if (msg == null) {
            msg = "Something goes wrong !<br>Please reload the application.";
        }
        this.#openMessageDialog(msg);
    }

}


class UploadFileDialog {

    static #open(label) {
        $("#overlayupload").css("display", "block");
        $("#overlaywrapper").css("display", "block");
        $("#uploadFormLabel").html("<strong>" + label + "<strong>");
        $("#uploadFormButton").prop("disabled", true);
    }

    static close() {
        Log.debug("Close upload box")
        $("#overlayupload").css("display", "none");
        $("#overlaywrapper").css("display", "none");
    }

    static openFeatures() {
        Log.debug("Open features upload box");
        $("#formFile").prop("multiple", true).attr("accept", ".json");
        $("#uploadImg").css("display", "none");
        let label = "Upload features files (\"features.json\" and \"protocols.json\")";
        this.#open(label);
    }

    static openModel(msg) {
        Log.debug("Open model upload box");
        $("#formFile").prop("multiple", false).attr("accept", ".zip");
        $("#uploadImg").css("display", "none");
        let label = "Upload optimization settings (\".zip\")";
        this.#open(label);
    }

    static openAnalysisResult() {
        Log.debug("Open analysis result upload box");
        $("#formFile").prop("multiple", false).attr("accept", ".zip");
        $("#uploadImg").css("display", "block");
        let label = "Upload model (\".zip\")"
        this.#open(label);
    }

}


// Enable apply button hpc selection
$(".accordion-button.hpc").on("click", async (button) => {
    let isAlreadyOpened = $("#" + button.currentTarget.id).hasClass("active");
    $(".accordion-button.hpc").removeClass("active").blur();
    if (!isAlreadyOpened) {
        $("#" + button.currentTarget.id).addClass("active");
        $("#apply-param").prop("disabled", false);
    } else {
        $("#apply-param").prop("disabled", true);
    }
    if (button.currentTarget.id == "accordionSA") {
        if ($("#sa-project-dropdown-optset-btn").text().toLowerCase() == "select project") {
            $("#apply-param").prop("disabled", true);
            $("#sa-project-dropdown-optset-btn").prop("disabled", true);
        }
    }
})


$("#username_submit").on("input", () => {
    $("#username_submit").removeClass("is-valid is-invalid");
})
$("#password_submit").on("input", () => {
    $("#password_submit").removeClass("is-valid is-invalid");
})

class OptimizationSettingsDialog {

    static #setDefaultValue() {
        Log.debug("setting deafault values");
        $("#daint_project_id").val("");
        $("#daint-gen-max").val(2)
        $("#daint-offspring").val(10)
        $("#daint-node-num").val(6);
        $("#daint-core-num").val(24);
        $("#daint-runtime").val("120m");
        $("#nsg-gen-max").val(2);
        $("#nsg-offspring").val(10);
        $("#nsg-node-num").val(1);
        $("#nsg-core-num").val(2);
        $("#nsg-runtime").val(2);
        
        $("#sa-gen-max").val(2)
        $("#sa-offspring").val(10)
        $("#sa-runtime").val(2);

    }

    static loadSettings(jObj) {
        Log.debug("settings value");
        this.#setDefaultValue();

        if (!jObj["service-account"]) {
            $("#accordionSA").addClass("disabled").prop("disabled", true);
            if (!$("#accordionSA").text().includes("unreachable")) {
                $("#accordionSA").append("&emsp;<b>*( temporarily unreachable )</b>");
            }
        }
        populateServiceAccountSettings(jObj["service-account"], "optset");
        let settings = jObj.settings;
        Log.debug(settings);
        
        if (!$.isEmptyObject(settings)) {    
            $(".accordion-button.hpc").removeClass("active").addClass("collapsed");
            $(".accordion-collapse").removeClass("show");
            if (settings.hpc == "DAINT-CSCS") {
                $("#accordionDaint").addClass("active");
                $("#daintCollapse").addClass("show");
                $("#daint_project_id").val(settings.project);
                $("#daint-gen-max").val(settings["gen-max"]);
                $("#daint-offspring").val(settings.offspring);
                $("#daint-node-num").val(settings["node-num"]);
                $("#daint-core-num").val(settings["core-num"]);
                $("#daint-runtime").val(settings.runtime);
            } else if (settings.hpc == "NSG") {
                $("#accordionNSG").addClass("active");
                $("#nsgCollapse").addClass("show");
                $("#nsg-gen-max").val(settings["gen-max"])
                $("#nsg-offspring").val(settings.offspring);
                $("#nsg-node-num").val(settings["node-num"]);
                $("#nsg-core-num").val(settings["core-num"]);
                $("#nsg-runtime").val(settings.runtime);
                if (settings["username_submit"]) {
                    $("#username_submit").addClass("is-valid").removeClass("is-invalid");
                } else { 
                    $("#username_submit").addClass("is-invalid").removeClass("is-valid");
                }
                if (settings["password_submit"]) {
                    $("#password_submit").addClass("is-valid").removeClass("is-invalid");
                } else { 
                    $("#password_submit").addClass("is-invalid").removeClass("is-valid");
                }
            } else if (settings.hpc == "SA") {
                $("#accordionSA").addClass("active");
                $("#saCollapse").addClass("show");
                $("#sa-gen-max").val(settings["gen-max"]);
                $("#sa-offspring").val(settings.offspring);
                $("#sa-node-num").val(settings["node-num"]);
                $("#sa-core-num").val(settings["core-num"]);
                $("#sa-runtime").val(settings.runtime);
                Log.debug(Object.keys(settings));
                if (Object.keys(settings).includes("sa-hpc")) {
                    $("#sa-hpc-dropdown-optset > button").html(settings["sa-hpc"].toUpperCase());
                    $("#sa-project-dropdown-optset > button").html(settings["sa-project"]).prop("disabled", false);
                    $(".dropdown-item.project." + settings["sa-hpc"]).removeClass("gone");
                }
                if ($("#sa-hpc-dropdown-optset-btn").text().toLowerCase() == "select hpc" ||
                    $("#sa-project-dropdown-optset-btn").text().toLowerCase() == "select project") {
                    $("#sa-project-dropdown-optset-btn").prop("disabled", true);
                    $("#apply-param").prop("disabled", true);
                }
            }
        }
    }

    

    static getJsonData() {
        const data = new Object();
        let hpc = $(".accordion-button.active").attr("name");
        data["hpc"] = hpc;
        if (hpc == "DAINT-CSCS") {
            if ($("#daint_project_id").val() == "") {
                $("#daint_project_id").removeClass("is-valid").addClass("is-invalid");
                alert('Please fill "Project ID" to apply settings');
                throw "daint_project empty";
            }
            data["gen-max"] = $("#daint-gen-max").val();
            data["offspring"] = $("#daint-offspring").val();
            data["node-num"] = $("#daint-node-num").val();
            data["core-num"] = $("#daint-core-num").val();
            data["runtime"] = $("#daint-runtime").val();
            data["project"] = $("#daint_project_id").val();
        }
        if (hpc == "NSG") {
            data["gen-max"] = $("#nsg-gen-max").val();
            data["offspring"] = $("#nsg-offspring").val();
            data["node-num"] = $("#nsg-node-num").val();
            data["core-num"] = $("#nsg-core-num").val();
            data["runtime"] = $("#nsg-runtime").val();

            let nsgUser = $("#username_submit");
            let nsgPass = $("#password_submit");
            
            if (nsgUser.val() == "") {
                nsgUser.addClass("is-invalid");
            }
            if (nsgPass.val() == "") {
                nsgPass.addClass("is-invalid");
            }
            if (nsgUser.val() == "" || nsgPass.val() == "") {
                alert("Please fill \"username\" and/or \"password\" to apply settings");
                throw "credentials empty";
            }
            
            
            if (nsgUser.val() == "" || nsgPass.val() == "") {
                if (nsgUser.val())
                nsgUser.addClass("is-invalid")
                
                if (!nsgUser.hasClass("is-valid") && !nsgPass.hasClass("is-valid")) {
                    alert("Please fill \"username\" and \"password\" to apply settings");
                    throw "credentials empty";            
                }
            } else {
                data["username_submit"] = nsgUser.val();
                data["password_submit"] = nsgPass.val();
            }             
        }
        if (hpc == "SA") {
            if ($("#sa-hpc-dropdown-optset > button").text().toLowerCase() == "select hpc") {
                $("#sa-hpc-dropdown-optset > button").html("Select HPC");
                $("#sa-project-dropdown-optset > button").html("Select Project").prop("disabled", true);
            } else {
                data["sa-hpc"] = $("#sa-hpc-dropdown-optset > button").text().toLowerCase();
                data["sa-project"] = $("#sa-project-dropdown-optset > button").text().toLowerCase();
            }
            data["gen-max"] = $("#sa-gen-max").val();
            data["offspring"] = $("#sa-offspring").val();
            data["node-num"] = $("#sa-node-num").val();
            data["core-num"] = $("#sa-core-num").val();
            data["runtime"] = $("#sa-runtime").val();
        }
        
        return data;
    }

    static getFomData() {
        const formData = new FormData();
        let hpc = $(".accordion-button.active").attr("name");
        formData.append("csrfmiddlewaretoken", $("input[name=csrfmiddlewaretoken]").val());
        formData.append("hpc", hpc);

        if (hpc == "DAINT-CSCS") {
            formData.append("gen-max", $("#daint-gen-max").val());
            formData.append("offspring", $("#daint-offspring").val());
            formData.append("node-num", $("#daint-node-num").val());
            formData.append("core-num", $("#daint-core-num").val());
            formData.append("runtime", $("#daint-runtime").val());
            formData.append("project", $("#daint_project_id").val());
        }
        if (hpc == "NSG") {
            formData.append("gen-max", $("#nsg-gen-max").val());
            formData.append("offspring", $("#nsg-offspring").val());
            formData.append("node-num", $("#nsg-node-num").val());
            formData.append("core-num", $("#nsg-core-num").val());
            formData.append("runtime", $("#nsg-runtime").val());
            if (!$("#username_submit").hasClass("is-valid")) {
                formData.append("username_submit", $("#username_submit").val());
            }
            if (!$("#password_submit").hasClass("is-valid")) {
                formData.append("password_submit", $("#password_submit").val());
            }
        }
        if (hpc == "SA") {
            if ($("#sa-hpc-dropdown-optset > button").text().toLowerCase() != "select hpc") {
                formData.append("sa-hpc", $("#sa-hpc-dropdown-optset > button").text().toLowerCase());
                formData.append("sa-project", $("#sa-project-dropdown-optset > button").text().toLowerCase());
            }
            formData.append("gen-max", $("#sa-gen-max").val());
            formData.append("offspring", $("#sa-offspring").val());
            formData.append("node-num", $("#sa-node-num").val());
            formData.append("core-num", $("#sa-core-num").val());
            formData.append("runtime", $("#sa-runtime").val());
        }

        if (Log.enabled) {
            for (let v of formData.values()) {
                Log.debug(v); 
            }
        }
        return formData;
    }

    static open() {
        Log.debug("open settings dialog");
        $("#overlayparam").css("display", "block");
        $("#overlaywrapper").css("display", "block");
    }

    static close() {
        Log.debug("close");
        $("#overlayparam").css("display", "none");
        $("#overlaywrapper").css("display", "none");
        $("#hpcAuthAlert").removeClass("show");
    }

}


function replaceWithSelectElement(id, options) {
    $("#" + id).remove();
    $("#" + id + "InputGroup")
        .append("<select id='" + id + "' class='form-select' name='" + id + "'>");
    $.each(options, (index, value)  => {
        $("#" + id).append("<option>" + value + "</option>");
    });
}   

class ModelRegistrationDialog {

    static open() {
        showLoadingAnimation("Loading options...");
        let modelName = $("#wf-title").text().split("Workflow ID: ")[1];
        
        $.ajax({
            url: "/hh-neuron-builder/get-model-catalog-attribute-options",
            method: "GET",
            async: false,
            success: options => {
                Log.debug(options);
                for (let key of Object.keys(options)) {
                    switch(key) {
                        case "species":
                            replaceWithSelectElement("modelSpecies", options[key]);
                            break;

                        case "brain_region":
                            replaceWithSelectElement("modelBrainRegion", options[key]);
                            break;
                    
                        case "model_scope":
                            replaceWithSelectElement("modelScope", options[key]);
                            break;
                    
                        case "abstraction_level":
                            replaceWithSelectElement("modelAbstraction", options[key]);
                            break;
                    
                        case "cell_type":
                            replaceWithSelectElement("modelCellType", options[key]);
                            break;

                        case "license":
                            
                            $("#modelLicense").empty();    
                            $.each(options[key], (index, value) => {
                                $("#modelLicense").append("<option>" + value + "</option>");
                            })
                            break
                        
                        default:
                    }
                }
            }
        })
        Log.debug("modelName " + modelName);
        $("#modelName").val(modelName)
    
        $("#overlaywrapper").css("display", "block");
        $("#overlaywrapmodreg").css("display", "block"); 
        hideLoadingAnimation();
    }

    static close() {
        $("#overlaywrapper").css("display", "none");
        $("#overlaywrapmodreg").css("display", "none");
    }

    static getFormData() {
        const formData = new FormData($("#modelRegisterForm")[0]);
        formData.append("modelPrivate", $("#modelPrivate").prop("checked"));
        for (let value of formData.values()) {
            Log.debug(value);
        }
        for (let key of formData.keys()) {
            Log.debug(key);
        }
        return formData;
    }
}


export { MessageDialog, UploadFileDialog, OptimizationSettingsDialog, ModelRegistrationDialog }
