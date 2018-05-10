var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;

$(document).ready(function(){
    openPleaseWaitDiv("Initializing");
    document.getElementById("cancel-wf-job-list-btn").onclick = closeFetchWfStorageDiv;
    document.getElementById("ok-nowf-btn").onclick = closeNoWfDiv;
    document.getElementById("new-wf").onclick = initNewWorkflow;
    $('#wf-storage-list-div').on('click', '.down-wf-btn', function(){
        downloadWf(this.id);
    });

    $.getJSON("/hh-neuron-builder/initialize/" + exc + "/" + ctx + "", function(data){
    closePleaseWaitDiv();
    });
});

function fetchWorkflows() {
    openPleaseWaitDiv("Searching for workflows in your storage");
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
                var textnode = document.createTextNode(list[i]); 
                var wf_download_button = document.createElement("button");

                crr_wf_div.className = "center-container row-center";
                crr_wf_span.className = "simple-span w-40pc center-container row-center-container";
                crr_wf_span.appendChild(textnode);
                crr_wf_div.appendChild(crr_wf_span);
                wf_download_button.id = list[i];
                wf_download_button.innerHTML = "Download";
                wf_download_button.className = "btn btn-default down-wf-btn";
                crr_wf_div.appendChild(wf_download_button);

                listDivEl.prepend(crr_wf_div);
            }
            closePleaseWaitDiv();
            document.getElementById("overlay-wrapper-wf").style.display = "block";
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

function downloadWf(wfid) {
    openPleaseWaitDiv("Downloading workflow from the storage.");
    closeFetchWfStorageDiv();
    var wfid_no_ext = wfid.replace(/\.[^/.]+$/, "")
        $.getJSON('/hh-neuron-builder/fetch-wf-from-storage/' + wfid_no_ext + '/' + req_pattern + '/', function(data){
            closePleaseWaitDiv();
            window.location.href = "/hh-neuron-builder/workflow/";
        });
}
