function initNewWorkflow() {
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";

    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        window.location.href = "/hh-neuron-builder/workflow/";
    });
}
