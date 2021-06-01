$(document).ready(function(){
    window.scrollTo(0,0);
    openMessageDiv("wait-div", "main-e-res-div");
    $.getJSON('/efelg/extract_features', function(data){
        if (data["status"] == "OK"){
            $.getJSON('/efelg/features_json_files_path', function(data_path){
                document.getElementById("hiddendiv").className = data_path['path'];
            });
            closeMessageDiv("wait-div", "main-e-res-div");
        };
    });
});
