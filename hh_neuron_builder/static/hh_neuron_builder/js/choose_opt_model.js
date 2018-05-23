$(document).ready(function(){
    var address = "https://raw.githubusercontent.com/lbologna/bsp_data_repository/master/optimizations/"
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";

	$.getJSON("/hh-neuron-builder/get_model_list/" + exc + "/" + ctx, function(data){
		$.each(data, function(idx, val){
			$.each(val, function(index, e){
				$("#sub-title-div" ).after("<div  id=" + index + " class='model-info-div'></div>");
				$("#" + index).append("<div id=" + index + " class='model-info-div-title'>" + e['meta']['species'] + ' > ' + e['meta']['brain_structure'] + ' > ' + e['meta']['cell_soma_location'] + ' > ' +  e['meta']['cell_type'] + ' > ' + e['meta']['e-type'] + ' > ' + e['meta']['morphology'] +  "</div>");
                $("#" + index).append("<div style='display:flex;' id=" + index + 'a' + " ></div>");
                $("#" + index + 'a').append("<div><img src=" + address + index + "/" + e['responses'] + " style='max-width:200px;' \>" + "<img src=" + address + index + "/" + e['morph'] + " style='max-width:200px;' \></div>");
				$('#' + index + 'a').append("<div><br><strong>Mod files:</strong> " + e['meta']['channels'] + "<br><br>" + "<strong>Contributors:</strong> " + e['meta']['contributors'] + "<br><br><strong>Contact:</strong> " + e['meta']['email'] + "</div>");
			})
		})
	});
});

	$('body').on('click', '.model-info-div', function(){
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
       var optimization_name = $(this).attr('id');
       $.get("/hh-neuron-builder/fetch-opt-set-file/" + optimization_name +
               "/" + exc + "/" + ctx + "/", function(){
		window.location.href = "/hh-neuron-builder/workflow/";
       });
	});

function setHPCParameters() {

}

function launchOptimizationHPC() {
	window.location.href = "/hh-neuron-builder/launch-opt-hpc/" + exc + "/" + ctx; 
}

function reloadCurrentPage() {
	window.location.href = ""
}
