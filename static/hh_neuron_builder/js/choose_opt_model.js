$(document).ready(function(){
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
       $.get("/hh-neuron-builder/set-optimization-name/" + optimization_name, function(){
		window.location.href = "/hh-neuron-builder/set-optimization-parameters/";
       });
	});

function setHPCParameters() {

}

function launchOptimizationHPC() {
	window.location.href = "/hh-neuron-builder/launch-opt-hpc"; 
}

function reloadCurrentPage() {
	window.location.href = ""
}
