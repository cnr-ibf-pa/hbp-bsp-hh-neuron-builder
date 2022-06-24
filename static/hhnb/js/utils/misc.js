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


function setServiceAccountHPC(hpc) {
    let hpcButton = $("#sa-hpc-dropdown-optset > button");
    let projectButton = $("#sa-project-dropdown-optset > button") 
    if (hpcButton.text() == hpc) {
        return false;
    }
    hpcButton.html(hpc);
    projectButton.prop("disabled", false).html("Select Project");
    
    $(".dropdown-item.project").addClass("gone");
    $(".dropdown-item.project." + hpc.toLowerCase()).removeClass("gone");
    
    // automatically set the project if there is only one project for the selecte HPC system
    if ($(".dropdown-item.project." + hpc.toLowerCase()).length == 1) {
        setServiceAccountProject(
            $(".dropdown-item.project." + hpc.toLowerCase()).text()
        )
    }
}

function setServiceAccountProject(project) {
    $("#sa-project-dropdown-optset > button").html(project);
}