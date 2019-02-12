var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;

$(document).ready(function(){
    document.getElementById("back-to-wf-btn").onclick = backToWorkflow;

    $.getJSON("/hh-neuron-builder/model-loaded-flag/" + req_pattern, function(data){
        var o = data["response"];
        if (o == "KO"){
            window.location.href = "";
        } else {
            document.getElementById("naas-frame").setAttribute("src","https://blue-naas.humanbrainproject.eu/#/model/" + o)
        }
    });
});

function backToWorkflow() {
    window.location.href = "/hh-neuron-builder/workflow";
}
