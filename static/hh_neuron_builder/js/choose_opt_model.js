$(document).ready(function(){
    var mainDiv = document.getElementById("mainDivMod");
    mainDiv.style.display = "none";
    displayPleaseWaitDiv(message="Loading models");
    var address = "https://raw.githubusercontent.com/lbologna/bsp_data_repository/master/optimizations/";
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";

    $.getJSON("/hh-neuron-builder/get_model_list/" + exc + "/" + ctx, function(data){
        var counter = 0;
        $.each(data, function(idx, val){
            $.each(val, function(index, e){
                $("#sub-title-div" ).after("<div  id=" + index + 
                        " class='model-info-div' style='width:100%;'></div>");
                $("#" + index).append("<div id=" + index + " class='model-info-div-title'>" + e['meta']['species'] + ' > ' + e['meta']['brain_region'] + ' > ' +  e['meta']['cell_type'] + "</div>");
                $("#" + index).append("<div style='display:flex;' id=" + index + 'a' + " ></div>");
                var img_div = document.createElement("DIV");
                var spk_img = document.createElement("IMG");
                var mor_img = document.createElement("IMG");
                var mor_id = "crr_mor";
                var spk_id = "crr_spk";
                var spk_url = e["responses"]; 
                var mor_url = e["morph"]; 
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
                $('#' + index + 'a').append("<div style='max-width:40%;padding:5px'>" + formatDescription(e['meta']['description']) + "</div>");
                spk_img.onload = function(){
                    counter += 1;
                    if (counter == 2 * data.length){
                        closePleaseWaitDiv();
                    }
                };
                mor_img.onload = function(){
                    counter += 1;
                    if (counter == 2 * data.length){
                        closePleaseWaitDiv();
                        mainDiv.style.display = "block";
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
    displayPleaseWaitDiv(message="Fetching model from the HBP Model Catalog");
    $.get("/hh-neuron-builder/fetch-opt-set-file/" + optimization_name +
            "/" + exc + "/" + ctx + "/", function(){
                closePleaseWaitDiv();
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

// Format description
function formatDescription(description = ""){
    var indexes = [];
    var all_strings = [];
    var final_string = "<br><strong>Description</strong><br>";
    var allowed_tag = [
        "affiliations", "brain_structure", "cell_soma_location", 
        "cell_type", "channels", "contributors", "e_type", 
        "email", "morphology"
    ];
    var res = description.replace(/\\\_/g, "_");

    var index = 0;
    while (index > -1) {
        index = res.indexOf('<br>');
        if (index == 0){
            if (res.length >=4){
                res = res.slice(4,);
            } else {
                index == -1;
            }
        } else if (index > -1){
            all_strings.push(res.slice(0, index));
            res = res.slice(index + 4,);
        }
    }
    for (var i = 0; i < all_strings.length; i++){
        for (var j = 0; j < allowed_tag.length; j++){
            if (all_strings[i].indexOf(allowed_tag[j]) > -1){
                final_string =  final_string + "<br>" + all_strings[i];
                break
            }
        }
    }
    return final_string
}
