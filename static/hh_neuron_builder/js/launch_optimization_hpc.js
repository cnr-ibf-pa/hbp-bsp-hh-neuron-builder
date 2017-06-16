$(document).ready(function(){
    document.getElementById("op-btn").onclick = launchOptimizationHPC;
    /*
       $.getJSON("/hh-neuron-builder/get_model_list", function(data){
       $.each(data, function(idx, val){
       $.each(val, function(index, e){
       $("#sub-title-div" ).after("<div id=" + index + " class='model-info-div'></div>");
       $("#" + index).append("<div id=" + index + " class='model-info-div-title'>" + e['meta']['species'] + ' > ' + e['meta']['brain_structure'] + ' > ' + e['meta']['cell_soma_location'] + ' > ' +  e['meta']['cell_type'] + ' > ' + e['meta']['e-type'] + ' > ' + e['meta']['morphology'] +  "</div>");
       $('#' + index).append("<div><br>Mod files: " + e['meta']['channels'] + "</div>");
       $('#' + index).append("<div><br>Contributors: " + e['meta']['contributors'] + "</div>");
       $('#' + index).append("<div><br>Contact: " + e['meta']['email'] + "</div>");
       })
       })
       });
       });

       $('body').on('click', '.model-info-div', function(){
       var optimization_name = $(this).attr('id');
       $.get('/hh-neuron-builder/set-optimization-name/' + optimization_name) 
       window.location.href = "/hh-neuron-builder/launch-optimization-hpc/";
       });
       */
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



    //window.location.href = "/hh-neuron-builder/launch-opt-hpc"; 
}

function reloadCurrentPage() {
    window.location.href = ""
}
