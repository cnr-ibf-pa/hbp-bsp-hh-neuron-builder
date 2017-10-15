function initNewWorkflow() {
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/", function(data){
        window.location.href = "/hh-neuron-builder/workflow/";
    });
}
