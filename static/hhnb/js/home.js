import { MessageDialog } from "./ui/components/dialog.js";
import Log from "./utils/logger.js";

Log.enabled = true;

const exc = sessionStorage.getItem("exc", null);


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


$( document ).ready(() => {
    if (exc !== "") {
        window.location.href = "/hh-neuron-builder/workflow/" + exc; 
    } else {
        hideLoadingAnimation();
    }
})

$("#new-wf").on("click", () => {
    showLoadingAnimation("Initializing workflow...");
    $.get("/hh-neuron-builder/initialize-workflow")
        .done((result) => {
            Log.debug(result);
            window.location.href = "/hh-neuron-builder/workflow/" + result.exc;                        
        }).fail((error) => {
            hideLoadingAnimation();
            checkRefreshSession(error);
            Log.error("Status: " + error.status + " > " + error.responseText);
            MessageDialog.openErrorDialog(error.responseText);
        });
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
        fetch("/hh-neuron-builder/upload-workflow", { // Your POST endpoint
            method: "POST",
            headers: {
                "Content-Type": "application/zip",
                "Content-Disposition": "attachment; filename=\"" + file.name + "\""
            },
            body: file
        }).then( response => {
            // handle expired session
            if (response.status === 403 && response.headers.get("refresh_url")) {
                $.post("/hh-neuron-builder/session-refresh/" + exc, response.responseJSON )
                    .done((result) => {
                        document.location.href = "/hh-neuron-builder/workflow/" + exc;
                    }).fail((error) => {
                        alert("Can't refresh session automatically, please refresh page");
                    })
            } else {
                response.json().then( data => {
                    if (data.response == "OK") {
                        window.location.href = "/hh-neuron-builder/workflow/" + data.exc;
                    } else {
                        hideLoadingAnimation();
                        MessageDialog.openErrorDialog(data.message);
                    }        
                })
            }
        })};

    // Event handler executed when a file is selected
    const onSelectFile = () => upload(input.files[0]);

    // Add a listener on your input
    // It will be triggered when a file will be selected
    input.addEventListener('change', onSelectFile, false);
}
