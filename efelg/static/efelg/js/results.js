$(document).ready(function(){
    window.scrollTo(0,0);
    openMessageDiv("load-message", "main-e-res-div");
    //
    $.getJSON('/efelg/extract-features', function(data){
        if (data["status"] == "OK"){
            $.getJSON('/efelg/features-json-files-path', function(data_path){
                document.getElementById("hiddendiv").className = 
                    data_path['path'];
                showDiv("exec-completed-div");
            });
            closeMessageDiv("load-message", "main-e-res-div");
        };
    });
});
