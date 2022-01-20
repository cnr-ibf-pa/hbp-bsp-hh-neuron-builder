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


async function checkLastPage(iframe){
    window.scrollTo(0,0);
    var innerDiv = iframe.contentDocument || iframe.contentWindow.document;
    var test = innerDiv.getElementById("hiddendiv");
    var flag = innerDiv.getElementById("hiddendiv2");

    // if the hiddendiv is present, display button 
    if (test == null || test == undefined) {
        $("#save-feature-files").prop("disabled", true);
    } else {
        while(1) {
            await sleep(250);
            if (flag.className == "true") {
                break;
            }
        }
        $("#save-feature-files").prop("disabled", false);
    }
};



$("#modalBlueNaas")[0].addEventListener("transitionstart", function (transition) {
    if (transition.target == $(this)[0]) {
        if ($(this).hasClass("show")) {
            $("#modalBlueNaasContainer").addClass("show");
        }
    }
})

$("#modalBlueNaas")[0].addEventListener("transitionend", function (transition) {
    if (transition.target == $(this)[0]) {
        if (!$(this).hasClass("show")) {
            $("#modalBlueNaasContainer").css("display", "none");
            $(this).css("z-index", "-100");
        }
    }
})

$("#modalBlueNaasContainer")[0].addEventListener("transitionstart", function (transition) {
    if (transition.target == $(this)[0]) {
        if (!$(this).hasClass("show")) {
            $("#modalBlueNaas").removeClass("show");
        }
    }
})


function dismissAlert(el) {
    console.log($(el).parent().removeClass("show"));
}

$("#modelPrivate").on("click", (button) => {
    console.log(button.target.checked); 
    if (button.target.checked) {
        $("#modelPrivateValue").text("Private");
    } else {
        $("#modelPrivateValue").text("Public");
    }
});