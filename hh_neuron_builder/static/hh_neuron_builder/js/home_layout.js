$(document).ready(function(){
    document.getElementById("new-wf").onclick = initNewWorkflow;
});

function initNewWorkflow() {
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/", function(data){
        window.location.href = "/hh-neuron-builder/workflow/";
    });
};

function chooseOptModel() {
    window.location.href = "/hh-neuron-builder/choose-opt-model"; 
}

function reloadCurrentPage() {
    window.location.href = "";
}

function colorBars() {
    window.location.href = "";
}

