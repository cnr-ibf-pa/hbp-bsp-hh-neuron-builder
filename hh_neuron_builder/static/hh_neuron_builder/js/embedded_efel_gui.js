$(document).ready(function(){
    document.getElementById("back-to-workflow").onclick = workflowPage;
});

function workflowPage() {
    console.log()
    window.location.href = "/hh-neuron-builder/workflow/";
}
