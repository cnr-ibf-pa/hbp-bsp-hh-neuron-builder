// fill message div
function fillMessageDiv(msg="", msgTag="", msgTextId="", msgDiv="",
        waitFlag=false, waitElId="", okBtnFlag=true, okBtnId="") {

    // manage message and message box
    $(msgTextId).html(msg);
    if (msgTag == "error"){
        $(msgDiv).css('borderColor', 'red');
    } else if (msgTag == "info"){
        $(msgDiv).css('borderColor', '#6cbaf6');
    } else if (msgTag == "success") {
        $(msgDiv).css('borderColor', 'green');
    } else if (msgTag == "default") {
        $(msgDiv).css('borderColor', '#d9d9d9');
    }

    // manage loading wheel
    if (waitFlag) {
        $(waitElId).css('display', 'block');
    } else {
        $(waitElId).css('display', 'none');
    }
    
    // manage loading wheel
    if (okBtnFlag) {
        $(okBtnId).css('display', 'block');
    } else {
        $(okBtnId).css('display', 'none');
    }
}
//
// open side div for optimization run parameter settings
function toggleElVisibility(displayBlock=[], displayNone=[], 
        eventsNone=[], eventsAuto=[]) {
    for (var i = 0; i < displayNone.length; i++){
        document.getElementById(displayNone[i]).style.display = "none"
    }

    for (var i = 0; i < displayBlock.length; i++){
        document.getElementById(displayBlock[i]).style.display = "block"
        //$(displayBlock[i]).css('display', 'block');
        $(displayBlock[i]).show();
    }

    // manage element visibility
    // for (var i = 0; i < eventsNone.length; i++){
    //     document.getElementById(eventsNone[i]).style.pointerEvents = "none"
    // }

    for (var i = 0; i < eventsAuto.length; i++){
        document.getElementById(eventsAuto[i]).style.pointerEvents = "auto"
    }
}

// open side div for optimization run parameter settings
function closeMessageDiv(onDivListIds, offDivListIds) {
    // manage divs visibility
    for (var i = 0; i < offDivListIds.length; i++){
        $(offDivListIds[i]).css('display', 'none');
    }
    for (var i = 0; i < onDivListIds.length; i++){
        $(onDivListIds[i]).css('pointerEvents', 'auto');
    }
    document.body.style.overflow = "auto";
}
