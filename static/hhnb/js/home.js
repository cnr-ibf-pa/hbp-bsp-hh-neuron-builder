import { MessageDialog } from "./ui/components/dialog.js";
import Log from "./utils/logger.js";

Log.enabled = true;


$( document ).ready(() => {
    hideLoadingAnimation();
})

$("#new-wf").on("click", () => {
    showLoadingAnimation("Initializing workflow...");
    $.get("/hh-neuron-builder/initialize-workflow")
        .done((result) => {
            Log.debug(result);
            window.location.href = "/hh-neuron-builder/workflow/" + result.exc;                        
        }).fail((error) => {
            Log.error("Status: " + error.status + " > " + error.responseText);
            MessageDialog.openErrorDialog(error.responseText);
        }).always(() => { hideLoadingAnimation() });
});

$("#fetch-wf-btn").on("click", uploadWorkflow);


function uploadWorkflow() {
    console.log("uploadWorkflow() called.")
    // Select your input type file and store it in a variable
    const input = document.getElementById('workflow-upload');
    $("#workflow-upload").trigger("click");

    // This will upload the file after having read it
    const upload = (file) => {
        showLoadingAnimation("Uploading workflow...");
        fetch("/hh-neuron-builder/upload-workflow/", { // Your POST endpoint
            method: "POST",
            headers: {
                "Content-Type": "application/zip",
                "Content-Disposition": "attachment; filename=\"" + file.name + "\""
            },
            body: file
        }).then( response => response.json()
        ).then(
            data => {
                console.log(data);
                if (data.response == "OK") {
                    window.location.href = "/hh-neuron-builder/workflow/" + data.exc;
                }
                else {
                    hideLoadingAnimation();
                    MessageDialog.openErrorDialog(data.message);
                }
            }
        )};

    // Event handler executed when a file is selected
    const onSelectFile = () => upload(input.files[0]);

    // Add a listener on your input
    // It will be triggered when a file will be selected
    input.addEventListener('change', onSelectFile, false);
}
