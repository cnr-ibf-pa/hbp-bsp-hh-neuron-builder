document.getElementById("back-to-workflow").onclick = workflowPage;
document.getElementById("save-feature-files").onclick = saveFeatures;

var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var hhf_etraces_dir = sessionStorage.getItem("hhf_etraces_dir", hhf_etraces_dir) ? sessionStorage.getItem("hhf_etraces_dir") : "";
var wfid = sessionStorage.getItem("wfid", wfid) ? sessionStorage.getItem("wfid") : "";

$(document).ready(function(){
    showLoadingAnimation("Loading...");
    console.log(sessionStorage);
    if (hhf_etraces_dir) {
        document.getElementById("efelgui-frame").setAttribute("src", "/efelg/hhf_etraces/" + wfid);
    } else {
      document.getElementById("efelgui-frame").setAttribute("src", "/efelg/?ctx=" + ctx);
    }
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
    var folderName = innerDiv.getElementById("hiddendiv").classList[0];
    
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
    // window.location.href = "/hh-neuron-builder/workflow/";
    $("#modalNFE").removeClass("show").addClass("hide");
    
}


function newWorkflow() {
    $("#wf-btn-new-wf").blur();
    showLoadingAnimation("Starting new workflow...");
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            openReloadDiv();
        } else {
            window.location.href = "/hh-neuron-builder/workflow/";
        }
        hideLoadingAnimation();
    });
}


function cloneWorkflow() {
    $("#wf-btn-clone-wf").blur();
    showLoadingAnimation("Cloning workflow...");
    $.ajax({
        url: "/hh-neuron-builder/clone-workflow/" + exc + "/" + ctx + "/",
        method: "GET",
        async: false,
        success: function(data) {
            hideLoadingAnimation();
            window.open("/hh-neuron-builder/workflow/" + data.exc + "/" + data.ctx + "/", "_blank");
            win.focus();
        }
    });
}


function downloadURI(uri, name) {
    var link = document.createElement("a");
    link.download = name;
    link.href = uri;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    delete link;
}


function saveWorkflow() {
    console.log("saveWorkflow() called.");
    $("#wf-btn-save").blur();
    showLoadingAnimation("Loading...")
    fetch("/hh-neuron-builder/workflow-download/" + exc + "/" + ctx, {
        method: "GET"
    }).then(
        data => downloadURI(data.url, 'workflow')
    ).then(
        hideLoadingAnimation()
    ).catch(
        error => console.log(error)
    );
}
