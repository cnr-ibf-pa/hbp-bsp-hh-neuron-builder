$(document).ready(function(){
    document.getElementById("in-silico-exp").onclick = inSilicoPage;
    document.getElementById("feat-efel-btn").onclick = efelPage;
    document.getElementById("feat-up-btn").onclick = reloadCurrentPage;
    document.getElementById("launch-opt-btn").onclick = launchOptimization;
    document.getElementById("opt-up-btn").onclick = reloadCurrentPage;
    document.getElementById("opt-fetch-btn").onclick = reloadCurrentPage;
});

function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/";
}

function inSilicoPage() {
        $.getJSON("/hh-neuron-builder/model-loaded-flag", function(data){
            var o = data["response"];
            if (o == "nothing"){
                window.location.href = "";
            } else {
                window.location.href = "/hh-neuron-builder/embedded-naas/";
            
            } 
        });
    //window.location.href = "/hh-neuron-builder/embedded-efel-gui/";
}

function launchOptimization() {
    window.location.href = "/hh-neuron-builder/choose-opt-model"; 
}

function reloadCurrentPage() {
    window.location.href = "";
}
