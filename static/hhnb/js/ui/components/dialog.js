import Log from "../../utils/logger.js";


class MessageDialog {

    static #createAlertDialog(level, title, msg) {
        console.log(level, title, msg);
        let alert = $("<div id='alert-dialog' role='alert'></>");
        let classes = "alert alert-dismissable fade ";
        let button;
        if (level != "warning") {
            button = "<button class='btn workflow-btn alert-dialog-button' data-bs-dismiss='alert' onclick='closeAlertDialog()'>Ok</button>";
        } else {
            button = "<button class='btn workflow-btn alert-dialog-button' data-bs-dismiss='alert' onclick='window.location.reload();'>Reload</button>";
        }
        switch (level) {
            case "danger":
                if (!title) {
                    title = "Error !";
                }
                classes += "alert-danger";
                break;

            case "warning":
                if (!title) {
                    title = "Unexpected behavior occurred !"
                }
                classes += "alert-warning";
                break;

            case "success":
                if (!title) {
                    title = "Success !";
                }
                classes += "alert-success";
                break;

            case "info":
            default:
                if (!title) {
                    title = "Info";
                }
                classes += "alert-info";
        }
        alert.addClass(classes);
        alert.append("\
            <h4 class='alert-heading' style='text-align: center;'>" + title + "</h4>\
            <br>\
            <p style='text-align: justify'>" + msg + "</p>\
            <hr>\
            <div class='row'>" + button + "</div>"
        );
        return alert;
    }

    static async #openDialog(level, text) {
        if (text.startsWith("{\"refresh_url\"")) {
            return false;
        }
        let alertDialog;
        let sm = splitTitleAndMessage(text);
        $("#shadow-layer").css("display", "block").addClass("show");
        if (sm) {
            alertDialog = this.#createAlertDialog(level, sm.title, sm.message);
        } else {
            alertDialog = this.#createAlertDialog(level, undefined, text);
        }
        $("body").append(alertDialog);
        alertDialog.addClass("show");
    }

    static openSuccessDialog(msg) {
        this.#openDialog("success", msg)
    }

    static openErrorDialog(msg) {
        this.#openDialog("danger", msg);
    }

    static openInfoDialog(msg) {
        this.#openDialog("info", msg);
    }

    static openReloadDialog(msg) {
        this.#openDialog("warning", msg);
    }
}


class UploadFileDialog {

    static async #open(label) {
        $("#overlaywrapper").css("display", "block");
        $("#overlayupload").css("display", "block");
        await sleep(10);
        $("#overlaywrapper").addClass("show");
        $("#overlayupload").addClass("show");
        $("#uploadFormLabel").html("<strong>" + label + "<strong>");
        $("#uploadFormButton").prop("disabled", true);
    }

    static async close() {
        Log.debug("Close upload box")
        $("#overlayupload").removeClass("show");
        $("#overlaywrapper").removeClass("show");
        await sleep(500);
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
$(".accordion-button.hpc").on("click",async event => {
    let btn = $(event.currentTarget);

    if (btn.parent().siblings().hasClass("show")) {
        return false;
    }

    if (btn.hasClass("active")) {
        $(".accordion-button.hpc").removeClass("active").blur();
    } else {
        $(".accordion-button.hpc").removeClass("active").blur();
        btn.addClass("active");
    }
    
    if ($(".accordion-button.hpc.active").length == 1) {
        Log.debug("Accordion button active = 1... Enabling ApplyParam button");
        $("#apply-param").prop("disabled", false);
    } else {
        $("#apply-param").prop("disabled", true);
    }

    if ($(".accordion-collapse.collapsing").length >= 3) {
        Log.debug("Accordion collapsing >= 3... Disabling ApplyParam button");
        await sleep(400);
        $(".accordion-collapse.show").each((i, e) => {
            console.log($(e).children().hasClass("active"));
            // if (!$(e).siblings().children().hasClass("active")) {
                // $(e).removeClass("show");
            // }
            let b = $(e).siblings().children();
            if (!b.hasClass("active")) {
                b.trigger("click").removeClass("active");
            }
        });
    }
}); 

$("#username_submit").on("input", () => {
    $("#username_submit").removeClass("is-valid is-invalid");
})
$("#password_submit").on("input", () => {
    $("#password_submit").removeClass("is-valid is-invalid");
})

$("#job-action-start").on("click", () => {
    $("#job-action").text("Start");

    let jobName = $("#job-name").val().toString();
    if (jobName.endsWith("_resume")) {
        $("#job-name").val($("#job-name").val().toString().split("_resume")[0]);
    }
    
    let jObj = JSON.parse(window.sessionStorage.getItem("job_settings"));
    OptimizationSettingsDialog.loadSettings(jObj, "start");
})  

$("#job-action-resume").on("click", () => {
    $("#job-action").text("Resume");
    let jObj = JSON.parse(window.sessionStorage.getItem("job_settings"));
    OptimizationSettingsDialog.loadSettings(jObj, "resume");
})  


class OptimizationSettingsDialog {

    static #resetSettingsDialog() {
        $(".accordion-button").removeClass("active").addClass("collapsed").attr("aria-expanded", "false");
        $(".accordion-collapse").removeClass("show");
    }

    static #setDefaultValue() {
        Log.debug("setting deafault values");
        $("#daint_project_id").val("");
        $("#daint-gen-max").val(2);
        $("#daint-offspring").val(10).prop("disabled", false)
        $("#daint-node-num").val(6);
        $("#daint-core-num").val(24);
        $("#daint-runtime").val("120m");
        $("#nsg-gen-max").val(2);
        $("#nsg-offspring").val(10).prop("disabled", false);
        $("#nsg-node-num").val(1);
        $("#nsg-core-num").val(2);
        $("#nsg-runtime").val(2);
        
        $("#sa-gen-max").val(2);
        $("#sa-offspring").val(10).prop("disabled", false);
        $("#sa-runtime").val(2);
    }

    static loadSettings(jObj, mode="start") {
        window.sessionStorage.setItem("job_settings", JSON.stringify(jObj));
        Log.debug(jObj);        

        if (!jObj["service-account"]) {
            $("#accordionSA").addClass("disabled").prop("disabled", true);
            if (!$("#accordionSA").text().includes("unreachable")) {
                $("#accordionSA").append("&emsp;<b>*( temporarily unreachable )</b>");
            }
        }
        populateServiceAccountSettings(jObj["service-account"], "optset");
        
        let settings = jObj.settings;
        let resume = jObj.resume;

        $("#job-name").val($("#wf-title").text().split("Workflow ID: ")[1]);

        if (mode == "start") {
            if ($.isEmptyObject(settings)) {
                this.#setDefaultValue();
            } else {
                $("#apply-param").prop("disabled", false)
                // $(".accordion-button.hpc").removeClass("active").addClass("collapsed");
                // $(".accordion-collapse").removeClass("show");
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
        } else if (mode == "resume") {
            if (!$.isEmptyObject(resume)) {
                $("#sa-offspring").val(resume["offspring_size"]).prop("disabled", true);
                $("#nsg-offspring").val(resume["offspring_size"]).prop("disabled", true);
                $("#daint-offspring").val(resume["offspring_size"]).prop("disabled", true);
                $("#sa-gen-max").val("").attr("placeholder", "Last gen: " + resume["max_gen"].toString());
                $("#nsg-gen-max").val("").attr("placeholder", "Last gen: " + resume["max_gen"].toString());
                $("#daint-gen-max").val("").attr("placeholder", "Last gen: " + resume["max_gen"].toString());
                // $(".accordion-button").removeClass("active");
                // $(".accordion-collapse").removeClass("show");
            }
            $("#job-name").val(resume.job_name ? resume.job_name + "_resume" : $("#job-name").val() + "_resume");
        }
    }

    static getJsonData() {
        const data = new Object();
        let hpc = $(".accordion-button.active").attr("name");
        data["hpc"] = hpc;
        data["job_name"] = $("#job-name").val();
        if (hpc == "DAINT-CSCS") {
            if ($("#daint_project_id").val() == "") {
                $("#daint_project_id").removeClass("is-valid").addClass("is-invalid");
                showWarningAlert('Please fill "Project ID" to apply settings and cotinue your workflow.');
                throw "daint_project empty";
            }
            data["gen-max"] = parseInt($("#daint-gen-max").val());
            if (!$("#daint-offspring").prop("disabled")) {
                data["offspring"] = parseInt($("#daint-offspring").val());
            }
            data["node-num"] = parseInt($("#daint-node-num").val());
            data["core-num"] = parseInt($("#daint-core-num").val());
            data["runtime"] = $("#daint-runtime").val();
            data["project"] = $("#daint_project_id").val();
        }
        if (hpc == "NSG") {
            data["gen-max"] = parseInt($("#nsg-gen-max").val());
            if (!$("#nsg-offspring").prop("disabled")) {
                data["offspring"] = parseInt($("#nsg-offspring").val());
            }
            data["node-num"] = parseInt($("#nsg-node-num").val());
            data["core-num"] = parseInt($("#nsg-core-num").val());
            data["runtime"] = parseFloat($("#nsg-runtime").val());

            let nsgUser = $("#username_submit");
            let nsgPass = $("#password_submit");
            
            if (nsgUser.val() == "") {
                nsgUser.addClass("is-invalid");
            }
            if (nsgPass.val() == "") {
                nsgPass.addClass("is-invalid");
            }
            if (nsgUser.val() == "" || nsgPass.val() == "") {
                showWarningAlert("Please fill \"username\" and/or \"password\" to apply settings and continue your workflow.");
                throw "credentials empty";
            }
            
            
            if (nsgUser.val() == "" || nsgPass.val() == "") {
                if (nsgUser.val())
                nsgUser.addClass("is-invalid")
                
                if (!nsgUser.hasClass("is-valid") && !nsgPass.hasClass("is-valid")) {
                    showWarningAlert("Please fill \"username\" and/or \"password\" to apply settings and continue your workflow.");
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
            data["gen-max"] = parseInt($("#sa-gen-max").val());
            if (!$("#sa-offspring").prop("disabled")) {
                data["offspring"] = parseInt($("#sa-offspring").val());
            }
            data["node-num"] = parseInt($("#sa-node-num").val());
            data["core-num"] = parseInt($("#sa-core-num").val());
            data["runtime"] = parseFloat($("#sa-runtime").val());
        }
        data["mode"] = $("#job-action").text().toLowerCase();


        for (let x in data) {
            console.log(typeof(data[x]))
            if (typeof(data[x]) === 'number' && isNaN(data[x])) {
                showWarningAlert("Missing correct value for <b>" + x.toUpperCase() + "</b>");
                throw Error("Not a number error on " + x);
            }
        }

        return data;
    }

    static getFomData() {
        const formData = new FormData();
        let hpc = $(".accordion-button.active").attr("name");
        let job_name = $("#job-name").val();
        formData.append("csrfmiddlewaretoken", $("input[name=csrfmiddlewaretoken]").val());
        formData.append("job_name", $("#job-name").text());
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

    static async open() {
        Log.debug("open settings dialog");
        $("#overlaywrapper").css("display", "block");
        $("#overlayparam").css("display", "block");
        await sleep(10);
        $("#overlaywrapper").addClass("show")
        $("#overlayparam").addClass("show");
    }
    
    static async close() {
        Log.debug("close");
        $("#overlayparam").removeClass("show");
        $("#overlaywrapper").removeClass("show");
        await sleep(500);
        $("#overlayparam").css("display", "none");
        $("#overlaywrapper").css("display", "none");
        $("#apply-param").prop("disabled", true);
        this.#resetSettingsDialog();
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

    static async open() {
        showLoadingAnimation("Loading options...");
        let modelName = $("#wf-title").text().split("Workflow ID: ")[1];
        $.getJSON("/hh-neuron-builder/get-model-catalog-attribute-options")
            .then(async options => {
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
                Log.debug("modelName " + modelName);
                $("#modelName").val(modelName)
                
                $("#overlaywrapper").css("display", "block");
                $("#overlaywrapmodreg").css("display", "block");
                await sleep(10);
                $("#overlaywrapper").addClass("show");
                $("#overlaywrapmodreg").addClass("show");
            }).catch(error => {
                Log.error("Error while getting options from model catalog: ", error);
                MessageDialog.openErrorDialog(error);
            }).always(() => {
                hideLoadingAnimation();
            })
    }

    static async close() {
        $("#overlaywrapmodreg").removeClass("show");
        $("#overlaywrapper").removeClass("show");
        await sleep(500);
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
