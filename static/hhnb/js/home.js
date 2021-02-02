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
      fetch("/hh-neuron-builder/workflow-upload/" + req_pattern, { // Your POST endpoint
        method: "POST",
        headers: {
          "Content-Type": "application/zip",
          "Content-Disposition": "attachment; filename=\"" + file.name + "\""
        },
        body: file
      }).then(
        data => {
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