$(document).ready(function(){
    document.getElementById("op-btn").onclick = launchOptimizationHPC;
    document.getElementById("back-to-workflow").onclick = workflowPage;
});

function launchOptimizationHPC() {
    var gennum = document.getElementById("gen_num").value;
    var offsize = document.getElementById("off_size").value;
    var nodenum = document.getElementById("node_num").value;
    var corenum = document.getElementById("core_num").value;
    var runtime = document.getElementById("run_time").value;
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    $.get("/hh-neuron-builder/set-gen-num/" + gennum);
    $.get("/hh-neuron-builder/set-off-size/" + offsize);
    $.get("/hh-neuron-builder/set-node-num/" + nodenum);
    $.get("/hh-neuron-builder/set-core-num/" + corenum);
    $.get("/hh-neuron-builder/set-run-time/" + runtime);
    $.get("/hh-neuron-builder/set-username/" + username);
    $.get("/hh-neuron-builder/set-password/" + password);
    var resp = $.get("/hh-neuron-builder/run-optimization/");
    var res = JSON.parse(resp);
    console.log(res)

    //window.location.href = "/hh-neuron-builder/launch-opt-hpc"; 
}

function reloadCurrentPage() {
    window.location.href = ""
}

function workflowPage() {
        window.location.href = "/hh-neuron-builder/workflow/";
}
