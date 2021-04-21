function openMessageDiv(divId, mainDivId) {
    document.getElementById(mainDivId).style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
    document.getElementById(divId).style.display = "block";
}

//
function closeMessageDiv(divId, mainDivId) {
    document.getElementById(divId).style.display = "none";
    document.getElementById(mainDivId).style.display = "block";
    document.getElementById(mainDivId).style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

//
function writeMessage(divId, message) {
    document.getElementById(divId).innerHTML = message;
}

//
function showDiv(divId) {
    document.getElementById(divId).style.display = "block";
}

//
function hideDiv(divId) {
    document.getElementById(divId).style.display = "none";
}
