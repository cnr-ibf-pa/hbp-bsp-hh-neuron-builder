$(document).ready(function(){
    window.scrollTo(0,0);
    openMessageDiv("wait-div", "main-e-res-div");
    $.getJSON('/efelg/extract_features', function(data){
        if (data["status"] == "OK"){
            $.getJSON('/efelg/get_result_dir/', function(data) {
                document.getElementById("hiddendiv").className = JSON.parse(data).result_dir
            });
            closeMessageDiv("wait-div", "main-e-res-div");
        } else if (data.status == "KO") {
            $(".mt-2").css("display", "none");
            $("#main-e-res-div").css("pointer-events", "auto");
            writeMessage("wmd-first", "<b style='color: red'>Error<br></b> " + data.message + "<br>");
            writeMessage("wmd-second", "Please, reload the application to complete the workflow.<br> If the problem persists contact the EBRAINS <a href='https://ebrains.eu/support' target='_blank'>support</a>.'");
        }
    });
});
