$(document).ready(function(){
    //$.getJSON('/efelg/features_json_path', function(data){
    //    document.getElementById('iframe-features').setAttribute('src', data['path']);
    //});
    //$.getJSON('/efelg/protocols_json_path', function(data2){
    //    document.getElementById('iframe-protocols').setAttribute('src', data2['path']);
    //});
    //$.getJSON('/efelg/features_pdf_path', function(data3){
    //    document.getElementById('iframe-pdf').setAttribute('src', data3['path']);
    //});
    //
    var btn = document.createElement("BUTTON");
    var t = document.createTextNode("CLICK ME");
    btn.appendChild(t);
    document.body.appendChild(btn);
    $.getJSON('/efelg/features_json_path', function(data){

        console.log(data['path'])
            $.get('/hh-neuron-builder/set-feature-folder/' + data['path']);
    });
    //$(".toggle-text").on("click", function(){
    //    $(this).siblings("div").slideToggle("normal", function(){});
    //});
});
