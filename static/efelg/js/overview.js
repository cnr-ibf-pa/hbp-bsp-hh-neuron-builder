var button = $('#tutorial_button');
var tutorial = $('#tutorial_div');
var carousel = tutorial.find('#carousel_div');

$(window).resize(function() {
    setCarouselHeight()
});

function toggleTutorial() {
    setCarouselHeight();
    if (tutorial.css('maxHeight') != "0px") {
        tutorial.css({maxHeight: 0 + "px"});
        button.text("Show Tutorial");
    } else {
        tutorial.css({maxHeight: tutorial[0].scrollHeight + "px"}); 
        button.text("Hide Tutorial");
    }
}

function setCarouselHeight() {
    var h = 0;
    $('.carousel-item').each(function() {
        var item = $(this);
        if (item.height() > h) {
            h = item.height()
        }
    });
    carousel.css({height: h});
}

function loadShowTraces() {	
    window.location.href = "/efelg/show_traces/";	
}