function showLoadingAnimation(message="") {
    console.log("showLoadingAnimation() called.");

    setLoadingAnimationText(message);
    // $(".loading-animation").css("display", "block");
    $(".loading-animation").addClass("show");
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
    console.log("hideLoadingAnimation() called.");
    // $(".loading-animation").css("display", "none").removeClass("start-animation reverse-animation");
    $(".loading-animation").removeClass("show");
    $(".neuron").removeClass("start-animation reverse-animation");
}

function setLoadingAnimationText(message) {
    $("#loading-text-div").html(message);
}
