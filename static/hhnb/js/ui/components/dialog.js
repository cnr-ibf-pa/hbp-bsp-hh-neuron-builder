import Log from "../../utils/logger.js";


class MessageDialog {

    static #overlayWrapper = $("#overlaywrapperdialog");
    static #overlayContent = $("#overlaycontentdialog");
    static #overlayDialog = $("#overlaydialog");
    static #dialogMessage = $("#dialogtext");
    static #dialogButton = $("#dialog-btn");


    static #openMessageDialog(msg) {
        this.#overlayWrapper.css("display", "block");
        this.#overlayContent.css("display", "block");
        this.#dialogMessage.html(msg);
    }

    static #closeMessageDialog() {
        this.#overlayWrapper.css("display", "none");
        this.#overlayContent.css("display", "none");
    }

    static openSuccessDialog(msg) {
        this.#overlayContent.css("box-shadow", "0 0 1rem 1rem rgba(0, 128, 0, .8)")
            .css("border-color", "green");
/*         this.#overlayDialog.addClass("error-content")
            .removeClass("reload-content info-content"); */
        this.#dialogButton.text("Ok")
            .addClass("green").removeClass("blue red fill-background")
            .on("click", () => { this.#closeMessageDialog() });
        this.#openMessageDialog(msg);
    }

    static openErrorDialog(msg) {
        this.#overlayContent.css("box-shadow", "0 0 1rem 1rem rgba(255, 0, 0, .8)")
            .css("border-color", "red");
/*         this.#overlayDialog.addClass("error-content")
            .removeClass("reload-content info-content"); */
        this.#dialogButton.text("Ok")
            .addClass("red").removeClass("blue green fill-background")
            .on("click", () => { this.#closeMessageDialog() });
        this.#openMessageDialog(msg);
    }

    static openInfoDialog(msg) {
        this.#overlayContent.css("box-shadow", "0 0 1rem 1rem rgba(0, 0, 255, .8)")
            .css("border-color", "blue");
/*         this.#overlayDialog.addClass("error-content")
            .removeClass("error-content reload-content"); */
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
        // $("#overlaywrapper").css("z-index", "100").addClass("show");
        // $("#uploadForm").attr("action", uploadUrl);
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
$(".accordion-button.hpc").on("click", (button) => {
    Log.debug(button.target.className);
    let isAlreadyOpened = $("#" + button.target.id).hasClass("active");
    $(".accordion-button.hpc").removeClass("active");
    if (!isAlreadyOpened) {
        $("#" + button.target.id).addClass("active");
        $("#apply-param").prop("disabled", false);
    } else {
        $("#apply-param").prop("disabled", true);
    }
})

/* function checkField(e) {
    if (e.target.value == "") {
        $("#apply-param").prop("disabled", true);
    } else {
        $("#apply-param").prop("disabled", false);
    }
}
$("#daint_project_id").on("keyup", checkField);
$("#username_submit").on("keyup", (e) => {
    if ($("#password_submit").val() != "") {
        checkField(e);
    }
});
$("#password_submit").on("keyup", (e) => {
    if ($("#username_submit").val() != "") {
        checkField(e);
    }
}); */


class OptimizationSettingsDialog {

    static #setDefaultValue() {
        Log.debug("setting deafault values");
        $("#daint_project_id").val("");
        $("#daint-gen-max").val(2)
        $("#daint-offspring").val(10)
        $("#daint-node-num").val(6);
        $("#daint-core-num").val(24);
        $("#daint-runtime").val("120m");
        $("#sa-daint-gen-max").val(2)
        $("#sa-daint-offspring").val(10)
        $("#sa-daint-node-num").val(6);
        $("#sa-daint-core-num").val(24);
        $("#sa-daint-runtime").val(2);
        $("#username_submit").val("");
        $("#password_submit").val("");
        $("#nsg-gen-max").val(2);
        $("#nsg-offspring").val(10);
        $("#nsg-node-num").val(1);
        $("#nsg-core-num").val(2);
        $("#nsg-runtime").val(2);
    }

    static loadSettings(jObj) {
        Log.debug("settings value");
        this.#setDefaultValue();
        if (!$.isEmptyObject(jObj)) {
            Log.debug("open default accordion")
            if (jObj.hpc == "DAINT-CSCS") {
                $("#daint_project_id").val(jObj.project);
                $("#daint-gen-max").val(jObj["gen-max"]);
                $("#daint-offspring").val(jObj.offspring);
                $("#daint-node-num").val(jObj["node-num"]);
                $("#daint-core-num").val(jObj["core-num"]);
                $("#daint-runtime").val(jObj.runtime);
            } else if (jObj.hpc == "SA-CSCS") {
                $("#sa-daint-gen-max").val(jObj["gen-max"]);
                $("#sa-daint-offspring").val(jObj.offspring);
                $("#sa-daint-node-num").val(jObj["node-num"]);
                $("#sa-daint-core-num").val(jObj["core-num"]);
                $("#sa-daint-runtime").val(jObj.runtime);
            } else if (jObj.hpc == "NSG") {
                $("#nsg-gen-max").val(jObj["gen-max"]);
                $("#nsg-offspring").val(jObj.offspring);
                $("#nsg-node-num").val(jObj["node-num"]);
                $("#nsg-core-num").val(jObj["core-num"]);
                $("#nsg-runtime").val(jObj.runtime);
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
        if (hpc == "SA-CSCS") {
            data["gen-max"] = $("#sa-daint-gen-max").val();
            data["offspring"] = $("#sa-daint-offspring").val();
            data["node-num"] = $("#sa-daint-node-num").val();
            data["core-num"] = $("#sa-daint-core-num").val();
            data["runtime"] = $("#sa-daint-gen-max").val();
        }
        if (hpc == "NSG") {
            data["gen-max"] = $("#nsg-gen-max").val();
            data["offspring"] = $("#nsg-offspring").val();
            data["node-num"] = $("#nsg-node-num").val();
            data["core-num"] = $("#nsg-core-num").val();
            data["runtime"] = $("#nsg-gen-max").val();

            let nsgUser = $("#username_submit");
            let nsgPass = $("#password_submit");
            if (nsgUser.val() == "" && nsgPass.val() == "") {
                if (!nsgUser.hasClass("is-valid") && !nsgPass.hasClass("is-valid")) {
                    alert("Please fill \"username\" and \"password\" to apply settings");
                    throw "credentials empty";            
                }
            } else {
                data["username_submit"] = nsgUser.val();
                data["password_submit"] = nsgPass.val();
            } 
            
          /*   if ($("#username_submit").val() == "" || $("#password_submit").val() == "") {
                $("#username_submit").removeClass("is-valid").addClass("is-invalid");
                $("#password_submit").removeClass("is-valid").addClass("is-invalid");
                alert("Please fill \"username\" and \"password\" to apply settings");
                throw "credentials empty";
            } else {
                
            } */
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
        if (hpc == "SA-CSCS") {
            formData.append("gen-max", $("#sa-daint-gen-max").val());
            formData.append("offspring", $("#sa-daint-offspring").val());
            formData.append("node-num", $("#sa-daint-node-num").val());
            formData.append("core-num", $("#sa-daint-core-num").val());
            formData.append("runtime", $("#sa-daint-runtime").val());
        }
        if (hpc == "NSG") {
            formData.append("gen-max", $("#nsg-gen-max").val());
            formData.append("offspring", $("#nsg-offspring").val());
            formData.append("node-num", $("#nsg-node-num").val());
            formData.append("core-num", $("#nsg-core-num").val());
            formData.append("runtime", $("#nsg-gen-max").val());
            if (!$("#username_submit").hasClass("is-valid")) {
                formData.append("username_submit", $("#username_submit").val());
            }
            if (!$("#password_submit").hasClass("is-valid")) {
                formData.append("password_submit", $("#password_submit").val());
            }
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
        // $("#overlaywrapper").css("z-index", "100").addClass("show");
        $("#overlaywrapper").css("display", "block");
        $("#username_submit").removeClass("is-invalid");
        $("#password_submit").removeClass("is-invalid");
        $("#daint_project_id").removeClass("is-invalid");
    }

    static close() {
        Log.debug("close");
        $("#overlayparam").css("display", "none");
        $("#overlaywrapper").css("display", "none");
        // $("#apply-param").prop("disabled", true);
        $("#hpcAuthAlert").removeClass("show");
        // $("#overlayparam").removeClass("show");
    }

}


class ModelRegistrationDialog {

    static open() {
        $("#overlaywrapper").css("display", "block");
        $("#overlaywrapmodreg").css("display", "block"); 
        
        let modelName = $("#wf-title").text().split("Workflow ID: ")[1];
        Log.debug("modelName " + modelName);
        $("#modelName").val(modelName)
    }

    static close() {
        $("#overlaywrapper").css("display", "none");
        $("#overlaywrapmodreg").css("display", "none");
    }

    static getFormData() {
        const formData = new FormData($("#modelRegisterForm")[0]);
        for (let value of formData.values()) {
            Log.debug(value);
        }
        return formData;
    }
}


export { MessageDialog, UploadFileDialog, OptimizationSettingsDialog, ModelRegistrationDialog }