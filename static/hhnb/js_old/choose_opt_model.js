$(document).ready(function(){
    showLoadingAnimation("Loading models");
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";

    $.getJSON("/hh-neuron-builder/check-cond-exist/" + exc + "/" + ctx, function(data){
        $("#wf-title").html("Workflow id: <bold>" + data["wf_id"] + "</bold>");
    });

    $.getJSON("/hh-neuron-builder/get_model_list/" + exc + "/" + ctx, function(data){
        var counter = 0;
        if (data.length == 0) {
            alert("Something goes wrong. Please reload the page.");
        }
        $.each(data, function(idx, val){
            $.each(val, function(index, e){
                console.log(e);
                var model_uuid = index; //e['meta']["id"];
                var model_name = index;
                $("#sub-title-div" ).after("<div  id=" + model_uuid + " name=" +
                        model_name + " class='main-content model-info-div'></div>");
                $("#" + model_uuid).append("<div id=" + model_uuid + " class='model-info-div-title'>" + e['meta']['species'] + ' > ' + e['meta']['brain_region'] + ' > ' +  e['meta']['cell_type'] + ' > ' + model_name + "</div>");
                $("#" + model_uuid).append("<div style='display:flex;' id=" + model_uuid + 'a' + " ></div>");
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
                $("#" + model_uuid + 'a').append(img_div);
                $('#' + model_uuid + 'a').append("<div style='max-width:40%;padding:5px;font-size:13px'>" + formatDescription(e['meta']) + "</div>");
                spk_img.onload = function(){
                    counter += 1;
                    if (counter == 2 * data.length){
                        hideLoadingAnimation();
                    }
                };
                mor_img.onload = function(){
                    counter += 1;
                    if (counter == 2 * data.length){
                        hideLoadingAnimation();
                        $("#page").css("display", "block");
                    }
                };
            });
        });
    });
});

$('body').on('click', '.model-info-div', function(){
    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
    var optimization_name = $(this).attr('name');
    var optimization_id = $(this).attr('id');
    showLoadingAnimation("Fetching model from the HBP Model Catalog");
    $.get("/hh-neuron-builder/fetch-opt-set-file/" + optimization_name +
            "/" + optimization_id + "/" + exc + "/" + ctx + "/", function(){
                hideLoadingAnimation();
                window.location.href = "/hh-neuron-builder/workflow/";
            });
});


function reloadCurrentPage() {
    window.location.href = ""
}


// Format description
function formatDescription(meta = ""){
    var description = meta['description']
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
    final_string_meta_app = final_string_meta_app + "<br><strong>" + "id : " + "</strong>" + meta["id"]
    if (final_string_meta_app.length > 1){
        final_string = final_string + final_string_meta_title + final_string_meta_app;
    }
    if (final_string_author_app.length > 1){
        final_string = final_string + final_string_author_title + final_string_author_app;
    }

    return final_string
}

function newWorkflow() {
    $("#wf-btn-new-wf").blur();
    showLoadingAnimation("Starting new workflow...");
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            openReloadDiv();
        } else {
            window.location.href = "/hh-neuron-builder/workflow/";
        }
        hideLoadingAnimation();
    });
}

function cloneWorkflow() {
    $("#wf-btn-clone-wf").blur();
    showLoadingAnimation("Cloning workflow...");
    $.getJSON("/hh-neuron-builder/clone-workflow/" + req_pattern + "/", function(data) {
        console.log(data);
        let win = window.open("/hh-neuron-builder/workflow/" + data.exc + "/" + data.ctx + "/", "_blank");
        win.focus();
        hideLoadingAnimation();
    });
}

function downloadURI(uri, name) {
  var link = document.createElement("a");
  link.download = name;
  link.href = uri;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  delete link;
}

function saveWorkflow() {
    $("#wf-btn-save").blur();
    showLoadingAnimation("Loading...");
    fetch("/hh-neuron-builder/workflow-download/" + req_pattern, {
        method: "GET"
    }).then(
        data => downloadURI(data.url, 'workflow')
    ).catch(
        error => console.log(error)
    );
}

$("#page").on("scroll", function() {
    var lastScrollTop = 0, delta = 5;
    $(window).scroll(function(){
        var nowScrollTop = $(this).scrollTop();
        if(Math.abs(lastScrollTop - nowScrollTop) >= delta){
            if (nowScrollTop > lastScrollTop){
                console.log("scroll down");
            } else {
                console.log("scroll up");
            }
        lastScrollTop = nowScrollTop;
        }
    });
});
