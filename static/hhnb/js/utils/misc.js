$("#modalNFE")[0].addEventListener("transitionstart", function(transition) {
    if (transition.target == $(this)[0]) {
        if ($(this).hasClass("show")) {
            $("#modalNFEContainer").addClass("show");
        }
    }
})
$("#modalNFE")[0].addEventListener("transitionend", function(transition) {
    if (transition.target == $(this)[0]) {
        if (!$(this).hasClass("show")) {
            $("#modalNFEContainer").css("display", "none");
            $(this).css("z-index", "-100");
        }
    }
});
$("#modalNFEContainer")[0].addEventListener("transitionstart", function(transition) {
    if (transition.target == $(this)[0]) {
        if (!$(this).hasClass("show")) {
            $("#modalNFE").removeClass("show");
        }
    }
}); 

$("#modalMC")[0].addEventListener("transitionstart", function() {
    if ( ! $(this).hasClass("show") ) {
        $("#closeModalMCButton").removeClass("show");
    };
})


function checkLastPage(iframe){
    window.scrollTo(0,0);
    var innerDiv = iframe.contentDocument || iframe.contentWindow.document;
    var test = innerDiv.getElementById("hiddendiv");

    // if the hiddendiv is present, display button 
    if (test == null || test == undefined) {
        $("#save-feature-files").prop("disabled", true);
    } else {
        $("#save-feature-files").prop("disabled", false);
    }
};


