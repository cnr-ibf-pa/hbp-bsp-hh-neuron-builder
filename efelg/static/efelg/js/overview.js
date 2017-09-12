$(document).ready(function(){
    var classname = document.getElementsByClassName("skip-intro");
    
    for (var i = 0; i < classname.length; i++) {
        classname[i].addEventListener('click', displayTermsConditions, false);
    }

    document.getElementById("next_btn").onclick = displayTermsConditions;
    document.getElementById("accept_btn").onclick = userAccepted;
    document.getElementById("decline_btn").onclick = userDeclined;
});

function displayTermsConditions() {
    document.getElementById('efelg-overview-main-div').style.display = "none";
    document.getElementById('termsConditions').style.display = "block";
    $("#termsConditions").fadeIn("slow");
}


function userAccepted() {
    document.getElementById('efelg-overview-main-div').style.display = "block";
    document.getElementById('termsConditions').style.display = "none";
    window.location.href = "show_traces/";

}

function userDeclined() {
    document.getElementById('efelg-overview-main-div').style.display = "block";
    document.getElementById('termsConditions').style.display = "none";
    window.location.href = "";
}
