$(document).ready(function(){

    $.getJSON('/efelg/features_json_path', function(data){
    document.getElementById("hiddendiv").className(data['path'])
        console.log(data['path'])
            $.get('/hh-neuron-builder/set-feature-folder/' + data['path']);
    });
});
