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

/*
$(document).ready(function () {
    //window.scrollTo(0,0);
    //document.getElementById('efelg-overview-main').style.display = "block";
    //document.getElementById('termsConditions').style.display = "none";
    var classname = document.getElementsByClassName("skip-intro");
    for (var i = 0; i < classname.length; i++) {
        //classname[i].addEventListener('click', displayTermsConditions, false);
        classname[i].addEventListener('click', loadShowTraces, false);
    }

    //document.getElementById("next_btn").onclick = displayTermsConditions;
    //document.getElementById("accept_btn").onclick = userAccepted;
    //document.getElementById("decline_btn").onclick = userDeclined;

});
*/

//function displayTermsConditions() {
//    document.getElementById('efelg-overview-main-div').style.display = "none";
//    document.getElementById('termsConditions').style.display = "block";
//    $("#termsConditions").fadeIn("slow");
//}


//function userAccepted() {
//    window.location.href = "show_traces/";
//    document.getElementById('termsConditions').style.display = "none";
//}

//function userDeclined() {
//    document.getElementById('efelg-overview-main-div').style.display = "block";
//    document.getElementById('termsConditions').style.display = "none";
//    window.location.href = "";
//}