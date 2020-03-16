// fill message div
function fillMessageDiv(msg="", msgTag="", msgTextId="", msgDiv="",
        waitFlag=false, waitElId="", okBtnFlag=true, okBtnId="") {

    // manage message and message box
    $(msgTextId).html(msg);
    if (msgTag == "error"){
        $(msgDiv).css('borderColor', 'red');
    } else if (msgTag == "info"){
        $(msgDiv).css('borderColor', 'blue');
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
        console.log(displayNone[i])
        $(displayNone[i]).css('display', 'none');
    }

    for (var i = 0; i < displayBlock.length; i++){
        $(displayBlock[i]).css('display', 'block');
    }

    // manage element visibility
    for (var i = 0; i < eventsNone.length; i++){
        $(eventsNone[i]).css('pointerEvents', 'none');
    }

    for (var i = 0; i < eventsAuto.length; i++){
        $(eventsAuto[i]).css('pointerEvents', 'block');
    }
    
}

// open side div for optimization run parameter settings
function closeMessageDiv(onDivListIds, offDivListIds) {
    console.log("inside here")
    // manage divs visibility
    for (var i = 0; i < offDivListIds.length; i++){
        console.log(offDivListIds[i])
        console.log(offDivListIds[i])
        console.log(offDivListIds[i])
        $(offDivListIds[i]).css('display', 'none');
    }
    for (var i = 0; i < onDivListIds.length; i++){
        console.log(onDivListIds[i])
        console.log(onDivListIds[i])
        console.log(onDivListIds[i])
        $(onDivListIds[i]).css('pointerEvents', 'auto');
    }
    document.body.style.overflow = "auto";
}
