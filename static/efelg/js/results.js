$(document).ready(function(){
    window.scrollTo(0,0);
    openMessageDiv("wait-div", "main-e-res-div");
    $.getJSON('/efelg/extract_features', function(data){
        if (data["status"] == "OK") {
            $.getJSON('/efelg/get_result_dir/', function (data) {
                document.getElementById("hiddendiv").className = JSON.parse(data).result_dir
            });
            closeMessageDiv("wait-div", "main-e-res-div");
        } else {
            closeMessageDiv("wait-div", "main-e-res-div");
            openMessageDiv("e-res-error-div", "main-e-res-div");
            writeMessage("error-message-div", "An error occurred while extracting features from traces. " + data["message"])
        }
    });
});
