function showLoadingAnimation(message="") {
    console.log("show loading animation");
    setLoadingAnimationText(message);
    $(".loading-animation").removeClass("hide");
    $(".loading-animation").addClass("show");
}

function hideLoadingAnimation() {
    console.log("hideLoadingAnimation() called.");
    $(".loading-animation").removeClass("show");
    $(".loading-animation").addClass("hide");
}

function setLoadingAnimationText(message) {
    $("#loading-text-div").html(message);
}