document.getElementById("back-to-workflow").onclick = workflowPage;
document.getElementById("save-feature-files").onclick = saveFeatures;

$(document).ready(function(){

    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
    
    document.getElementById("efelgui-frame").setAttribute("src", 
                "/efelg/?ctx=" + ctx);

   // $.getJSON('/hh-neuron-builder/get-context/', function(data){
   //     var context = data["context"];         
   //     document.getElementById("efelgui-frame").setAttribute("src", 
   //             "/efelg/?ctx=" + context);
   // })

});

// activate save button if last page has been reached
function checkLastPage(iframe){
    window.scrollTo(0,0);
    var innerDiv = iframe.contentDocument || iframe.contentWindow.document;
    var test = innerDiv.getElementById("hiddendiv");

    // if the hiddendiv is present, display button 
    if(test != undefined) {
        document.getElementById("save-feature-files").style.display = "block";
    } else {
        console.log("UNDEFINED hidden div");
    }
};

//
function saveFeatures(){

    var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
    var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
    
    var innerDiv = document.getElementById("efelgui-frame").contentDocument || 
        getElementById("efelgui-frame").contentWindow.document;
    var folderName = innerDiv.getElementById("hiddendiv").classList[0];
    $.getJSON('/hh-neuron-builder/copy-feature-files/' + folderName + '/' + exc + '/' + ctx +'/', 
            function(data){
                window.location.href = "/hh-neuron-builder/workflow";
            });    
}

//
function workflowPage() {
    window.location.href = "/hh-neuron-builder/workflow/";
}
