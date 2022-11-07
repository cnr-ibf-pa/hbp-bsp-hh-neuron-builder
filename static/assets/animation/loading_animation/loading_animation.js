function showLoadingAnimation(message="") {
    setLoadingAnimationText(message);
    $(".loading-animation").css("display", "block");
    $(".neuron").addClass("start-animation");

    $("#termination")[0].addEventListener("animationend", async event => {
        if (event.animationName == "termination-loading") {
            $(".neuron").removeClass("start-animation").addClass("reverse-animation");
        } else if (event.animationName == "reverse-termination-loading") {
            $(".neuron").removeClass("reverse-animation").addClass("start-animation");
        }
    })
}

function hideLoadingAnimation() {
    $(".loading-animation").css("display", "none").removeClass("start-animation reverse-animation");
}

function setLoadingAnimationText(message) {
    $("#loading-text-div").html(message);
}
