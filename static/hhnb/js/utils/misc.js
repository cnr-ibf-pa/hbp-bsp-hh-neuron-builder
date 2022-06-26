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


function setServiceAccountHPC(hpc, context) {
    let hpcButton = $("#sa-hpc-dropdown-" + context + " > button");
    let projectButton = $("#sa-project-dropdown-" + context + " > button");
    
    if (hpcButton.text() == hpc) {
        return false;
    }
    hpcButton.html(hpc);
    projectButton.prop("disabled", false).html("Select Project");
    if (hpc == "PIZDAINT") {
        $("#sa-node-num").val(3);
        $("#sa-core-num").val(24);
    } else if (hpc == "NSG") {
        $("#sa-node-num").val(1);
        $("#sa-core-num").val(2);
    }

    $(".dropdown-item.project").addClass("gone");
    $(".dropdown-item.project." + hpc.toLowerCase()).removeClass("gone");
    
    // automatically set the project if there is only one project for the selecte HPC system
    if ($(".dropdown-item.project." + hpc.toLowerCase()).length == 1) {
        setServiceAccountProject($(".dropdown-item.project." + hpc.toLowerCase()).text(), context)
    }
}

function setServiceAccountProject(project, context) {
    $("#sa-project-dropdown-" + context + " > button").html(project);
    if (context == "optset") {
        $("#apply-param").prop("disabled", false);
    } else if (context == "jobs") {
        $("#sa-fetch-jobs").prop("disabled", false);
    } 
}

function populateServiceAccountSettings(jObj, context) {
    var hpcList = $("#sa-hpc-dropdown-" + context + " > ul"); 
    var projectList = $("#sa-project-dropdown-" + context + " > ul");

    hpcList.empty();
    projectList.empty();

    let saHPC = Object.keys(jObj);
    let dividerNum = saHPC.length - 1;

    for (let i=0; i < saHPC.length; i++) {
        hpcList.append("<li><a id='dropdown-item-hpc-"+ saHPC[i].toLowerCase() +"' class='dropdown-item hpc' onclick='setServiceAccountHPC(this.innerText, \"" + context + "\");'>" + saHPC[i] + "</a></li>");
        if (dividerNum > 0) {
            hpcList.append("<li><hr class='dropdown-divider'></li>");
            dividerNum -= 1;
        } 
    }

    for (var hpc in jObj) {
        let projects = jObj[hpc];
        let dividerNum = projects.length - 1;
        for (let i=0; i < projects.length; i++) {
            projectList.append("<li><a class='dropdown-item project "+ hpc.toLowerCase() +" gone' onclick='setServiceAccountProject(this.innerText,\"" + context + "\");'>"+ projects[i] +"</a></li>");
            if (dividerNum > 0) {
                projectList.append("<li><hr class='dropdown-divider'></li>");
                dividerNumm -= 1;
            } 
        }
    }
}