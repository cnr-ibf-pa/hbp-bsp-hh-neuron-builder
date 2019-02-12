$(document).ready(function(){
    displayPleaseWaitDiv(message="Loading models");
    var address = "https://raw.githubusercontent.com/lbologna/bsp_data_repository/master/optimizations/";
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";

    $.getJSON("/hh-neuron-builder/get_model_list/" + exc + "/" + ctx, function(data){
        var counter = 0;
        $.each(data, function(idx, val){
            $.each(val, function(index, e){
                $("#sub-title-div" ).after("<div  id=" + index + " class='model-info-div' style='width:100%;'></div>");
                $("#" + index).append("<div id=" + index + " class='model-info-div-title'>" + e['meta']['species'] + ' > ' + e['meta']['brain_structure'] + ' > ' + e['meta']['cell_soma_location'] + ' > ' +  e['meta']['cell_type'] + ' > ' + e['meta']['e-type'] + ' > ' + e['meta']['morphology'] +  "</div>");
                $("#" + index).append("<div style='display:flex;' id=" + index + 'a' + " ></div>");
                var img_div = document.createElement("DIV");
                var spk_img = document.createElement("IMG");
                var mor_img = document.createElement("IMG");
                var mor_id = "crr_mor";
                var spk_id = "crr_spk";
                var spk_url = address + index + "/" + e["responses"]; 
                var mor_url = address + index + "/" + e["morph"]; 
                img_div.setAttribute("style", "max-width:60%;");
                mor_img.setAttribute("id", mor_id);
                mor_img.setAttribute("style", "max-width:50%;");
                spk_img.setAttribute("id", spk_id);
                spk_img.setAttribute("style", "max-width:50%;");
                spk_img.setAttribute("src", spk_url);
                mor_img.setAttribute("src", mor_url);
                img_div.append(spk_img);
                img_div.append(mor_img);
                $("#" + index + 'a').append(img_div);
                $('#' + index + 'a').append("<div style='max-width:40%;'><br><strong>Mod files:</strong> " + e['meta']['channels'] + "<br><br>" + "<strong>Contributors:</strong> " + e['meta']['contributors'] + "<br><br><strong>Contact:</strong> " + e['meta']['email'] + "</div>");
                spk_img.onload = function(){
                    counter += 1;
                    if (counter == data.length){
                        closePleaseWaitDiv();
                    }
                };
                mor_img.onload = function(){
                    counter += 1;
                    if (counter == data.length){
                        closePleaseWaitDiv();
                    }
                };
            });
        });
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

// Hide please wait message div
function closePleaseWaitDiv() {
    document.getElementById("overlaywrapperwaitmod").style.display = "none";
    document.getElementById("mainDivMod").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

// Display please wait div
function displayPleaseWaitDiv(message="") {
    document.getElementById("overlaywrapperwaitmod").style.display = "block";
    document.getElementById("mainDivMod").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
    if (message || !(message.length === 0)){
        document.getElementById("waitdynamictextmod").innerHTML = message;
    }
}

