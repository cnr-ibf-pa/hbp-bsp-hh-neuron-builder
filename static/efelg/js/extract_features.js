
$(document).ready(function(){

    $.getJSON('/efelg/features_json_path', function(data){
var btn = document.createElement("BUTTON");
var t = document.createTextNode("CLICK MEEEEE");
btn.appendChild(t);
document.body.appendChild(btn);

        console.log(data['path'])
            $.get('/hh-neuron-builder/set-feature-folder/' + data['path']);
    });
});
