$(document).ready(function(){
    showLoadingAnimation(message="Loading models");
    var address = "https://raw.githubusercontent.com/lbologna/bsp_data_repository/master/optimizations/";
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";

    $.getJSON("/hh-neuron-builder/get_model_list/" + exc + "/" + ctx, function(data){
        models = JSON.parse(data.models);
        console.log(models)
        var counter = 0;
        $.each(models, function(idx, e){
                var model_uuid = e.id;
                var model_name = e.name;
                $("#sub-title-div" ).after("<div  id=" + model_uuid + " name=" + model_name + " class='main-content model-info-div' ></div>");
                $("#" + model_uuid).append("<div id=" + model_uuid + "class=''>");
                $("#" + model_uuid).append("<div id=" + model_uuid + " class='navbar navbar-light bg-light model-info-div-title'>" + e['meta']['species'] + ' > ' + e['meta']['brain_region'] + ' > ' +  e['meta']['cell_type'] + ' > ' + e['meta']['name'] + "</div>");
                $("#" + model_uuid).append("<div style='display:flex;' id=" + model_uuid + 'a' + " ></div>");
                var img_div = document.createElement("DIV");
                var spk_img = document.createElement("IMG");
                var mor_img = document.createElement("IMG");
                var mor_id = "crr_mor";
                var spk_id = "crr_spk";
                var spk_url = null; 
                var mor_url = null; 
                for (let i = 0; i < e.images.length; i++) {
                    if (e.images[i].caption == "Morphology") {
                        mor_url = e.images[i].url;
                    }
                    else if (e.images[i].caption == "Responses") {
                        spk_url = e.images[i].url;
                    }
                }
                img_div.setAttribute("style", "max-width:60%;");
                mor_img.setAttribute("id", mor_id);
                mor_img.setAttribute("style", "max-width:50%;");
                spk_img.setAttribute("id", spk_id);
                spk_img.setAttribute("style", "max-width:50%;");
                spk_img.setAttribute("src", spk_url);
                spk_img.setAttribute("alt", "Responses image not available");
                mor_img.setAttribute("src", mor_url);
                mor_img.setAttribute("alt", "Morphology image not available");
                img_div.append(spk_img);
                img_div.append(mor_img);
                $("#" + model_uuid + 'a').append(img_div);
                $('#' + model_uuid + 'a').append("<div style='max-width:40%;padding:5px;font-size:13px'>" + formatDescription(e) + "</div>"); //e['meta']) + "</div>");
                spk_img.onload = function(){
                    counter += 1;
                    if (counter == 2 * data.length){
                        hideLoadingAnimation();
                    }
                };
                spk_img.onerror = function() {
                    counter += 1;
                }
                mor_img.onload = function(){
                    counter += 1;
                    if (counter == 2 * data.length){
                        hideLoadingAnimation();
                        $("#page").css("display", "block");
                    }
                };
                mor_img.onerror = function() {
                    counter += 1;
                }
            });
        //});
    });
});

$('body').on('click', '.model-info-div', function(){
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
    var optimization_name = $(this).attr('name');
    var optimization_id = $(this).attr('id');
    showLoadingAnimation(message="Fetching model from the HBP Model Catalog");
    $.get("/hh-neuron-builder/fetch-opt-set-file/" + optimization_name + "/" + optimization_id + "/" + exc + "/" + ctx + "/", function(){
                hideLoadingAnimation();
                window.location.href = "/hh-neuron-builder/workflow/";
    });
/*    $.get("/hh-neuron-builder/fetch-opt-set-file/" + optimization_id + "/" + exc + "/" + ctx + "/", function() {
        closePleaseWaitDiv();
        window.location.href = "/hh-neuron-builder/workflow/";
    });*/
});

function setHPCParameters() {

}

function launchOptimizationHPC() {
    window.location.href = "/hh-neuron-builder/launch-opt-hpc/" + exc + "/" + ctx; 
}

function reloadCurrentPage() {
    window.location.href = ""
}

// Format description
//function formatDescription(meta = ""){
function formatDescription(value="") {
    //var description = meta['description']
    var description = value.description;
    var indexes = [];
    var all_strings = [];
    var final_string = "";
    var final_string_meta_app = "";
    var final_string_author_app = "";
    var final_string_meta_title = "<span style='font-size:16px'><br>Description<br></span>";
    var final_string_author_title = "<span style='font-size:16px'><br><br><br>Credits<br></span>";
    var allowed_tag_meta = [
        "brain_structure", "cell_soma_location", 
        "cell_type", "channels", "e_type", "morphology"
    ];
    var allowed_tag_author = ["contributors", "email", "affiliations"]
    //var res = description.replace(/\\\_/g, "_");
    var res = description.replace(/\\_/g, "_");
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
        for (var j = 0; j < allowed_tag_meta.length; j++){
            if (all_strings[i].indexOf(allowed_tag_meta[j]) > -1){
                final_string_meta_app =  final_string_meta_app + "<br>" + all_strings[i];
                break
            }
        }
        for (var z = 0; z < allowed_tag_author.length; z++){
            if (all_strings[i].indexOf(allowed_tag_author[z]) > -1){
                final_string_author_app =  final_string_author_app + "<br>" + all_strings[i];
                break
            }
        }
    }
    final_string_meta_app = final_string_meta_app + "<br><strong>" + "id : " + "</strong>" + value.id; //meta["id"]
    if (final_string_meta_app.length > 1){
        final_string = final_string + final_string_meta_title + final_string_meta_app;
    }
    if (final_string_author_app.length > 1){
        final_string = final_string + final_string_author_title + final_string_author_app;
    }

    return final_string
}
