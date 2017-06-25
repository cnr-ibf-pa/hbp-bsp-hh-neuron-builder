$(document).ready(function(){
    $.getJSON('/efelg/features_json_files_path', function(data){
        document.getElementById("hiddendiv").className = data['path'];
    });
});
