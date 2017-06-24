
$(document).ready(function(){

var btn = document.createElement("BUTTON");
var t = document.createTextNode("CLICK ME");
btn.appendChild(t);
document.body.appendChild(btn);
    $.getJSON('/efelg/features_json_path', function(data){

        console.log(data['path'])
            $.get('/hh-neuron-builder/set-feature-folder/' + data['path']);
    });
});
