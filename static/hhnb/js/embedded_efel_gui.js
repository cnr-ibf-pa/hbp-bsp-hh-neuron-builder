document.getElementById("back-to-workflow").onclick = workflowPage;
document.getElementById("save-feature-files").onclick = saveFeatures;

$(document).ready(function(){
    showLoadingAnimation("Loading...");
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
    
    document.getElementById("efelgui-frame").setAttribute("src", "/efelg/?ctx=" + ctx);

    $.getJSON("/hh-neuron-builder/check-cond-exist/" + exc + "/" + ctx, function(data){
        $("#wf-title").html("Workflow id: <bold>" + data["wf_id"] + "</bold>");
        hideLoadingAnimation();
    });
});

// activate save button if last page has been reached
function checkLastPage(iframe){
    window.scrollTo(0,0);
    var innerDiv = iframe.contentDocument || iframe.contentWindow.document;
    var test = innerDiv.getElementById("hiddendiv");

    // if the hiddendiv is present, display button 
    if(test != undefined) {
        document.getElementById("save-feature-files").disabled = false;
    } else {
        console.log("UNDEFINED hidden div");
    }
};

//
function saveFeatures(){

    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
    
    var innerDiv = document.getElementById("efelgui-frame").contentDocument || 
        getElementById("efelgui-frame").contentWindow.document;
    var folderNameOrig = innerDiv.getElementById("hiddendiv").classList[0];
    
    console.log(folderNameOrig)
    folderName = folderNameOrig.replace(/\./g, "______")
   
    showLoadingAnimation("Saving features...");
    $.ajax({
        url: "/hh-neuron-builder/copy-feature-files/" + exc + "/" + ctx + "/",
        method: "POST",
        data: {"folder": folderName},
        success: function(result) {
            console.log(result);
            hideLoadingAnimation();
            if (result.resp == "OK") {
                window.location.href = "/hh-neuron-builder/workflow";
            } else {
                alert("Something goes wrong. Please download the Features files and upload them manually."); 
            }
        }
    });
}

//
function workflowPage() {
    window.location.href = "/hh-neuron-builder/workflow/";
}
