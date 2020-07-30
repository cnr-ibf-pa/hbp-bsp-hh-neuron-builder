$(document).ready(function(){
    window.scrollTo(0,0);
    console.log("RESULT.JS CALLED");
    openMessageDiv("load-message", "main-e-res-div");
    //
    $.getJSON('/efelg/extract-features', function(data){
        if (data["status"] == "OK"){
            console.log('STATUS OK');
            $.getJSON('/efelg/features-json-files-path', function(data_path){
                console.log('DATA_PATH ACQUIRED')
                document.getElementById("hiddendiv").className =
                    data_path['path'];
                showDiv("exec-completed-div");
            });
            closeMessageDiv("load-message", "main-e-res-div");
        };
    });
});
