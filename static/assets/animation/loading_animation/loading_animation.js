class Log {
    
    static enable = false;
    
    static debug(message) {
        if (this.enable) {
            console.log(message);
        }
    }
}

if (window.location.href.startsWith("https://127.0.0.1")) {
    Log.enable = true;
}

function showLoadingAnimation(message="") {
    Log.debug("showLoadingAnimation(\"" + message + "\") called");

    setLoadingAnimationText(message);
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
    Log.debug("hideLoadingAnimation() called");
    $(".loading-animation").removeClass("show");
    $(".neuron").removeClass("start-animation reverse-animation");
}

function setLoadingAnimationText(message) {
    $("#loading-text-div").html(message);
}
