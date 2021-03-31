var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;
console.log(exc);
console.log(ctx);


jQuery(document).ready(function(){
    showLoadingAnimation("Inizializing");
    $.getJSON("/hh-neuron-builder/set-exc-tags/" + req_pattern, function(exc_data){
        if (exc_data["response"]=="KO"){
            // closePleaseWaitDiv();
            hideLoadingAnimation();
            openReloadDiv(exc_data["message"]);
        } else {
            $.getJSON("/hh-neuron-builder/initialize/" + exc + "/" + ctx + "", function(data){
                if (data["response"]=="KO"){
                    // closePleaseWaitDiv();
                    hideLoadingAnimation();
                    openReloadDiv(data["message"]);
                }
                // closePleaseWaitDiv();
                hideLoadingAnimation();
            });
        }
    });
});


function initNewWorkflow() {
    showLoadingAnimation("Inizializing workflow.");
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            hideLoadingAnimation();
            openReloadDiv(data["message"]);
        }else{ 
            window.location.href = "/hh-neuron-builder/workflow/";
        }
    });
}

function uploadWorkflow() {
    console.log("uploadWorkflow() called.")
    // Select your input type file and store it in a variable
    const input = document.getElementById('workflow-upload');
    $("#workflow-upload").trigger("click");

    // This will upload the file after having read it
    const upload = (file) => {
        showLoadingAnimation("Uploading workflow...");
        fetch("/hh-neuron-builder/workflow-upload/" + req_pattern, { // Your POST endpoint
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
                    window.location.href = "/hh-neuron-builder/workflow/";
                }
                else {
                    hideLoadingAnimation();
                    openErrorDiv(message=data.message, tag="error");
                }
            }
        )};

    // Event handler executed when a file is selected
    const onSelectFile = () => upload(input.files[0]);

    // Add a listener on your input
    // It will be triggered when a file will be selected
    input.addEventListener('change', onSelectFile, false);
}

function openErrorDiv(message, tag) {
    manageErrorDiv(open=true, close=false, message, tag);
}

function closeErrorDiv() {
    manageErrorDiv(open=false, close=true);
}

function manageErrorDiv(open=false, close=false, message="", tag="") {
    let overlayWrapper = $("#overlaywrapperhome");
    let overlayWrapperError = $("#overlaywrappererrorhome");
    let errorDynamicText = $("#errordynamictexthome");
    let button = $("#ok-error-div-btn-home");
    button.removeClass("blue", "red", "green");
    if (open) {
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
    } else if (close) {
        overlayWrapper.css("display", "none");
        overlayWrapperError.css("display", "none");
    }
}

function manageReloadDiv(open=false, close=false, message="") {
    let overlayWrapper = $("#overlaywrapper");
    let overlayWrapperReload = $("#overlaywrapperreload");
    let reloadDynamicText = $("#reloaddynamictext");
    if (open) {
        overlayWrapper.css("display", "block");
        overlayWrapperReload.css("display", "block");
        reloadDynamicText.html(message);
    } else if (close) {
        overlayWrapper.css("display", "none");
        overlayWrapperReload.css("display", "none");
    }
}

// Open reload div
function openReloadDiv(message="") {
    manageReloadDiv(open=true, close=false, message);
}

// Close reload div
function closeReloadDiv() {
    manageReloadDiv(open=false, close=true);
    window.location="/hh-neuron-builder/"
}
