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
    projectButton.prop("disabled", false);

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
    if ($(".dropdown-item.project." + context + "." + hpc.toLowerCase()).length == 1) {
        setServiceAccountProject($(".dropdown-item.project." + context + "." + hpc.toLowerCase()).text(), context)
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
            projectList.append("<li><a class='dropdown-item project " + context + " " + hpc.toLowerCase() + " gone' onclick='setServiceAccountProject(this.innerText,\"" + context + "\");'>"+ projects[i] +"</a></li>");
            if (dividerNum > 0) {
                projectList.append("<li><hr class='dropdown-divider'></li>");
                dividerNumm -= 1;
            } 
        }
    }
}


async function closeAlertDialog() {
    $("#shadow-layer").removeClass("show");
    await sleep(500);
    $("#shadow-layer").css("display", "none");
    $("#alert-dialog").remove();
} 
/* Alerts functions */


async function closeAlert(counter) {
    let alert = $("#alert[counter='" + counter.toString() + "']");
    alert.removeClass("show");
    await sleep(500);
    alert.css("display", "none");
    alert.remove();
}

var counter = 0;
/**
 * Show the alert.
 * 
 * @param {*} msg           The message to be shown in the alert.
 * @param {String} level    Optional param. Can be "danger", "warning", "success", "info" (default).
 */
async function showAlert(msg, level="", timeout, showSymbol=true, showCloseButton=true) {
    if ($("#alert[counter]:last > div#alert-text").html() == msg) {
        return false;
    }

    let alert = $("<div id='alert' role='alert' counter='" + counter.toString() + "'></>");
    let classes = "alert d-flex align-items-center alert-dismissable fade ";
    let symbol = '<svg id="alert-svg" class="bi flex-shrink-0 me-2 center" width="24" height="24" role="img" '
    let button = '<button id="alert-button" type="button" class="btn-close center" aria-label="Close" onclick="closeAlert(' + counter + ')"></button>';

    switch (level) {
        case "danger":
            classes += "alert-danger";
            symbol += 'aria-label="Danger:"><use xlink:href="#exclamation-triangle-fill"/></svg>';
            break;

        case "warning":
            classes += "alert-warning";
            symbol += 'aria-label="Danger:"><use xlink:href="#exclamation-triangle-fill"/></svg>';
            break;

        case "success":
            classes += "alert-success";
            symbol += 'aria-label="Success:"><use xlink:href="#check-circle-fill"/></svg>';
            break;

        case "info":
        default:
            classes += "alert-info";
            symbol += 'aria-label="Info:"><use xlink:href="#info-fill"/></svg>';
    }

    alert.addClass(classes);
    alert.append(symbol);
    alert.append("<div id='alert-text'>" + msg + "</div>");
    alert.append(button);

    $("body").append(alert);
    alert.css("left", (($(".page").width() - alert.width()) / 2).toString() + "px");
    counter += 1;

    await sleep(10);
    alert.addClass("show");
    await sleep(timeout);
    $("#alert-button").trigger("click");
}


function makeAlertText(head="", strong="", content="") {
    let msg = "";
    if (head) {
        msg += "<h4 class='alert-heading'>" + head + "</h4><hr>";
    }
    if (strong) {
        msg += "<strong>" + strong + "</strong>";
    }
    if (content) {
        msg += "<p>" + content + "</p>";
    }
    return msg;
}


function showInfoAlert(msg, timeout=10000) {
    showAlert(msg, "info", timeout, true, false);
}

function showSuccessAlert(msg, timeout=10000) {
    showAlert(msg, "success", timeout, true, true);
}

function showErrorAlert(msg, timeout=10000) {
    showAlert(msg, "danger", timeout, true, true);
}

function showWarningAlert(msg, timeout=10000) {
    showAlert(msg, "warning", timeout, true, false);
}

function showHpcAuthAlert() {
    console.log("showHpcAuthAlert() called.");
    showAlert(
        makeAlertText(
            head="", 
            strong="You need to be logged in to use this HPC system !",
            content="Please, click \"Cancel\" and login with the button in the top right corner before doing this operation."
        ),
        "warning",
        5000,
        true,
        false
    );
}

function showJobsAuthAlert() {
    console.log("showJobsAuthAlert()");
    showAlert(
        makeAlertText(
            head="",
            strong="You need to authenticate with Ebrains to fetch jobs on this HPC system !",
            content="Please, click \"Cancel\" and login with the button in the top right corner before doing this operation."
        ),
        "warning",
        5000,
        true,
        false
    )
}

function showServiceAccountAlert() {
    showAlert(
        makeAlertText(
            head="",
            strong="The Service Account is temporarily unreachable !",
            content="Please, try again later or contact the support if the problem persists."
        ),
        "warning",
        5000,
        true,
        false
    )
}

function splitTitleAndMessage(message) {
    let splittedMessage = message.split("</b><br><br>");
    if (splittedMessage.length == 2) {
        return {
            title: splittedMessage[0].replace("<b>", ""),
            message: splittedMessage[1]
        };
    }
    return null;
}