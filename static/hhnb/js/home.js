var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;
console.log(exc);
console.log(ctx);


jQuery(document).ready(function(){
    // document.getElementById("cancel-wf-job-list-btn").onclick = closeFetchWfStorageDiv;
    // document.getElementById("ok-nowf-btn").onclick = closeNoWfDiv;
    document.getElementById("new-wf").onclick = initNewWorkflow;
    // document.getElementById("home-reload-btn").onclick = closeReloadDiv;
    /* $('#wf-storage-list-div').on('click', '.down-wf-btn', function(){
        downloadWf(this.id);
    }); */
    openPleaseWaitDiv("Initializing");
    $.getJSON("/hh-neuron-builder/set-exc-tags/" + req_pattern, function(exc_data){
        if (exc_data["response"]=="KO"){
            closePleaseWaitDiv();
            openReloadDiv(exc_data["message"]);
        } else {
            $.getJSON("/hh-neuron-builder/initialize/" + exc + "/" + ctx + "", function(data){
                if (data["response"]=="KO"){
                    closePleaseWaitDiv();
                    openReloadDiv(data["message"]);
                }
                closePleaseWaitDiv();
            });
        }
    });
});


function initNewWorkflow() {
    openPleaseWaitDiv("Initializing worklow.");
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            closePleaseWaitDiv();
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
      fetch("/hh-neuron-builder/workflow-upload/" + req_pattern, { // Your POST endpoint
        method: "POST",
        headers: {
          "Content-Type": "application/zip",
          "Content-Disposition": "attachment; filename=\"" + file.name + "\""
        },
        body: file
      }).then(
        data => {
            console.log("SONO QUI"); // Handle the success response object
            console.log(data);
            window.location.href = "/hh-neuron-builder/workflow/";
        }
      ).catch(
        error => console.log(error) // Handle the error response object
      );
    };

    // Event handler executed when a file is selected
    const onSelectFile = () => upload(input.files[0]);

    // Add a listener on your input
    // It will be triggered when a file will be selected
    input.addEventListener('change', onSelectFile, false);
}

function openPleaseWaitDiv(message) {
    // document.getElementById("overlay-wrapper-wait").style.display = "block";
    document.body.style.overflow = "auto";
    // document.getElementById("wait-dynamic-text").innerHTML = message;
}

function closePleaseWaitDiv(){
    // document.getElementById("overlay-wrapper-wait").style.display = "none";
    document.body.style.overflow = "auto";
}