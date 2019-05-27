var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;
console.log(exc);
console.log(ctx);

$(document).ready(function(){
    document.getElementById("cancel-wf-job-list-btn").onclick = closeFetchWfStorageDiv;
    document.getElementById("ok-nowf-btn").onclick = closeNoWfDiv;
    document.getElementById("new-wf").onclick = initNewWorkflow;
    document.getElementById("home-reload-btn").onclick = closeReloadDiv;
    $('#wf-storage-list-div').on('click', '.down-wf-btn', function(){
        downloadWf(this.id);
    });
    openPleaseWaitDiv("Initializing");
    $.getJSON("/hh-neuron-builder/set-exc-tags/" + req_pattern, function(exc_data){
        if (exc_data["response"]=="KO"){
            closePleaseWaitDiv();
            openReloadDiv(exc_data["message"]);
        } else {
            $.getJSON("/hh-neuron-builder/initialize/" + exc + "/" + ctx + "", function(data){
                if (data["response"]=="KO"){
                    closePleaseWaitDiv();
                    openReloadDiv(data["message"]);
                }
                closePleaseWaitDiv();
            });
        }
    });
});

function fetchWorkflows() {
    openPleaseWaitDiv("Searching for workflows in your current collab storage");
    var listDivEl = document.getElementById("wf-storage-list-div");
    listDivEl.innerHTML = "";
    $.getJSON("/hh-neuron-builder/wf-storage-list/" + req_pattern + "/", function(data){
        if (data['list'].length == 0){
            closePleaseWaitDiv();
            openNoWfDiv();
        } else {
            var list = data['list'];
            for (var i=0; i<list.length; i++) {
                var crr_wf_div = document.createElement("DIV");
                var crr_wf_span = document.createElement("SPAN");
                var wf_download_button = document.createElement("button");

                crr_wf_div.className = "center-container";
                crr_wf_span.className = "col-xs-7 simple-span";
                crr_wf_span.innerHTML = list[i];
                crr_wf_div.appendChild(crr_wf_span);
                wf_download_button.id = list[i];
                wf_download_button.innerHTML = "Download";
                wf_download_button.className = "col-xs-3 btn btn-link down-wf-btn";
                crr_wf_div.appendChild(wf_download_button);

                listDivEl.prepend(crr_wf_div);
            }
            closePleaseWaitDiv();
            var overdivwf = document.getElementById("overlay-wrapper-wf");
            overdivwf.style.display = "block";
            overdivwf.scrollTop = 0;
            document.getElementById("home-main-div").style.pointerEvents = "none";
            document.body.style.overflow = "hidden";
        };
    });
}

function openNoWfDiv() {
    document.getElementById("home-overlay-wrapper-nowf").style.display = "block";
    document.getElementById("home-main-div").style.pointerEvents = "none";
    document.body.style.overflow = "auto";
}

function closeNoWfDiv() {
    document.getElementById("home-main-div").style.pointerEvents = "auto";
    document.getElementById("home-main-div").style.display = "block";
    document.body.style.overflow = "auto";
    document.getElementById("home-overlay-wrapper-nowf").style.display = "none";
}

function openPleaseWaitDiv(message) {
    document.getElementById("home-overlay-wrapper-wait").style.display = "block";
    document.getElementById("home-main-div").style.pointerEvents = "none";
    document.body.style.overflow = "auto";
    document.getElementById("home-wait-dynamic-text").innerHTML = message;
}

function openReloadDiv(message, ctx) {
    document.getElementById("home-overlay-wrapper-reload").style.display = "block";
    document.getElementById("home-main-div").style.pointerEvents = "none";
    document.body.style.overflow = "auto";
    document.getElementById("home-reload-dynamic-text").innerHTML = message;
}

function closeReloadDiv(message) {
    document.getElementById("home-overlay-wrapper-reload").style.display = "none";
    document.getElementById("home-main-div").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
    location.reload();
}

function closePleaseWaitDiv(){
    document.getElementById("home-overlay-wrapper-wait").style.display = "none";
    document.getElementById("home-main-div").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

function closeFetchWfStorageDiv() {
    document.getElementById("overlay-wrapper-wf").style.display = "none";
    document.getElementById("home-main-div").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

function initNewWorkflow() {
    openPleaseWaitDiv("Initializing worklow.");
    $.getJSON("/hh-neuron-builder/create-wf-folders/new/" + exc + "/" + ctx, function(data){
        if (data["response"] == "KO"){
            closePleaseWaitDiv();
            openReloadDiv(data["message"]);
        }else{ 

            window.location.href = "/hh-neuron-builder/workflow/";
        }
    });
}

function downloadWf(wfid) {
    openPleaseWaitDiv("Downloading workflow from the storage.");
    closeFetchWfStorageDiv();
    var wfid_no_ext = wfid.replace(/\.[^/.]+$/, "")
        $.getJSON('/hh-neuron-builder/fetch-wf-from-storage/' + wfid_no_ext + '/' + req_pattern + '/', function(data){
            closePleaseWaitDiv();
            window.location.href = "/hh-neuron-builder/workflow/";
        });
}
