function showLoadingAnimation(message="") {
    setLoadingAnimationText(message);
    if ($(".loading-animation").hasClass("hide")) {
        $(".loading-animation").removeClass("hide").addClass("show");
        startAnimation();
    }
}

function hideLoadingAnimation() {
    stopAnimation();
    $(".loading-animation").removeClass("show").addClass("hide");
}

function setLoadingAnimationText(message) {
    $("#loading-text-div").html(message);
}

function startAnimation() {
    let anims = ["o1", "o2", "o3", "o4", "o5", "o6", "o7", "o8", "o9"]
    $("#o1").attr("dur", "3s").attr("begin", "click;o1.end+0.3s");
    for (let i = 1; i < anims.length; i++) {
        $("#" + anims[i]).attr("dur", 3.0 - 0.3*i + "s").attr("begin", anims[i-1] + ".begin+0.3s");
    };
    $("#o1")[0].beginElement();
}

function stopAnimation() {
    console.log("stopping animation");
    $("#o1").attr("begin", "unset");
    [
       "o1", "o2", "o3", "o4", "o5", "o6", "o7", "o8", "o9"
    ].forEach((id, index) => {
        $("#" + id)
            .attr("dur", "0.1s")
            .attr("begin", "0.1s")
    });
}