$(".div-toggle").toggle();
$(document).ready(function(){
    $.getJSON('/efelg/features_json_address', function(data){
        document.getElementById('iframe-features').setAttribute('src', data['path']);
    });
    $.getJSON('/efelg/protocols_json_address', function(data2){
        document.getElementById('iframe-protocols').setAttribute('src', data2['path']);
    });
    $.getJSON('/efelg/pdf_path', function(data3){
        document.getElementById('iframe-pdf').setAttribute('src', data3['path']);
    });
    $(".toggle-text").on("click", function(){
        $(this).siblings("div").slideToggle("normal", function(){});
    });
});
