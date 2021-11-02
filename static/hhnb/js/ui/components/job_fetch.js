

var is_user_authenticated = sessionStorage.getItem("isUserAuthenticated");

function dismissAlert(el) {
    console.log($(el).parent().removeClass("show"));
}

function displayJobFetchDiv() {
    $("#overlayjobs").css("display", "block");
    // $("#overlaywrapper").css("z-index", "100").addClass("show");
    $("#overlaywrapper").css("display", "block");
    $(".list-group-item.fetch-jobs").attr("aria-disabled", "false").removeClass("disabled active");
}

function resetJobFetchDiv() {
    $("#nsgLoginRow").css("display", "none");
    $("#spinnerRow").css("display", "none");
    $("#progressRow").css("display", "none");
    $("#tableRow").css("display", "none");
    $("#job-list-body").empty();
    $("#jobsAuthAlert").removeClass("show");
    $("#cancel-job-list-btn").prop("disabled", false);
    $("#refresh-job-list-btn").prop("disabled", true);
    $(".list-group-item.fetch-jobs").removeClass("disabled active clicked").attr("aria-disabled", "false");
    $("#checkNsgSpinnerButton").css("opacity", "0");
    $("#usernameNsg").removeClass("is-invalid");
    $("#passwordNsg").removeClass("is-invalid");
    resetProgressBar();
}

function closeJobFetchDiv() {
    // $("#overlayjobs").removeClass("show scroll-long-content");
    $("#overlayjobs").css("display", "none");
    $("#overlaywrapper").css("display", "none");
}


// Manage job list div
function displayCSCSJobList(button) {
    if (button.hasClass("clicked")) {
        return false;
    }
    resetJobFetchDiv();
    $.get("/hh-neuron-builder/get-authentication")
        .done(() => {
            button.addClass("clicked");
            displayJobList(button);
        })
        .fail(() => { $("#jobsAuthAlert").addClass("show") });
}

function displayNsgJobList(button) {
    if (button.hasClass("clicked")) {
        return false;
    }
    resetJobFetchDiv();
    $("#jobsNSG").addClass("active");
    $("#tableRow").css("display", "none");
    $("#nsgLoginRow").css("display", "flex");
    button.addClass("clicked");
}

function refreshJobListDiv() {
    $("#overlayjobs").removeClass("scroll-long-content");
    $("#job-list-body").empty();
    $("#tableRow").css("display", "none");
    $("#refresh-job-list-btn").prop("disabled", true);
    resetProgressBar();
    displayJobList($(".list-group-item.fetch-jobs.active"));
}

async function displayJobList(button) {
    $("#overlayjobs").removeClass("scroll-long-content");
    $("#cancel-job-list-btn").prop("disabled", true);
    $("#spinnerRow").css("display", "flex");
    $(".list-group-item.fetch-jobs").addClass("disabled").attr("aria-disabled", "true");
    button.attr("aria-disabled", "false").removeClass("disabled").addClass("active");

    var tableBody = document.getElementById("job-list-body");
    var hpc = button.attr("name");

    $.getJSON("/hh-neuron-builder/fetch-jobs/list/" + exc, { hpc })
        .done(async (data) => {
            var jobsNumber = data.jobs.length;
            if (jobsNumber == 0) {
                console.log('No jobs submitted yet');
            } else {
                $("#spinnerRow").css("display", "none");
                $("#progressRow").css("display", "flex");
                await sleep(300);
                var step = 100 / jobsNumber + 1 * 2;
                // animateProgressBar(step);
                animateProgressBar(50);

                $.getJSON("/hh-neuron-builder/fetch-jobs/details/" + exc, { hpc })
                    .done(async (data) => {
                        console.log(data);
                        // for (let job of Object.keys(data.jobs))
                        for (let job_id of Object.keys(data.jobs)) {
                            let job = data.jobs[job_id];
                            let downloadButton = document.createElement("button");
                            downloadButton.id = job_id;
                            downloadButton.innerText = "Download";
                            downloadButton.className = "btn workflow-btn job-download-button";
                            // downloadButton.disabled = true;
                            downloadButton.setAttribute("onclick", "downloadJobButtonHandler(this)");

                            let tr = document.createElement("tr");
                            let tdWf = document.createElement("td");
                            let tdId = document.createElement("td");
                            let tdStatus = document.createElement("td");
                            let tdDate = document.createElement("td");
                            let tdButton = document.createElement("td");

                            tdWf.innerText = job.name;
                            if (tdWf.innerHTML == "") {
                                tdWf.innerHTML = "Unknown";
                            }
                            tdId.innerText = job_id;
                            tdStatus.innerText = job.status;
                            tdDate.innerHTML = moment.utc(job.submissionTime).format();
                            tdButton.appendChild(downloadButton);

                            tr.appendChild(tdWf);
                            tr.appendChild(tdId);
                            tr.appendChild(tdStatus);
                            tr.appendChild(tdDate);
                            tr.appendChild(tdButton);
                            tableBody.appendChild(tr);

                            if (job.status == "COMPLETED" ||
                                job.job_stage == "SUCCESSFUL" ||
                                job.job_stage == "FAILED") {
                                tdStatus.style.color = "#00802b";
                                tdStatus.style.fontWeight = "bolder";
                                // downloadButton.disabled = false;
                                if (job.job_stage == "FAILED") {
                                    tdStatus.style.color = "#DD9900";
                                    //downloadButton.disabled = true;
                                }
                            } else {
                                tdStatus.style.color = "#DD9900";
                                tdStatus.style.fontWeight = "bolder";
                                // downloadButton.disabled = true;
                            }
                            
                            // await sleep(300);
                            animateProgressBar(step);
                        }
                        
                        await sleep(5000);

                        // while (true) {
                            // await sleep(1000);
                        if (parseFloat($("#progressBarFetchJob").attr("aria-valuenow")) >= 99.0) {
                            var tableRows = []
                            for (let i = 0; i < tableBody.children.length; i++) {
                                tableRows[i] = tableBody.children[i];
                            }
                            tableRows.sort(function (a, b) {
                                return moment.utc(a.children[3].innerHTML) - moment.utc(b.children[3].innerHTML);
                            });
                            tableRows.reverse();
                            $("#job-list-body").empty();

                            for (let i = 0; i < tableRows.length; i++) {
                                tableBody.appendChild(tableRows[i]);
                            }

                            $("#progressRow").css("display", "none");
                            $("#tableRow").css("display", "flex");
                            $("#refresh-job-list-btn").prop("disabled", false).blur();
                            $("#cancel-job-list-btn").prop("disabled", false);
                            $(".list-group-item.fetch-jobs").attr("aria-disabled", "false").removeClass("disabled clicked");

                            windowHeight = $(window).height();
                            overlayJobsHeight = $("#overlayjobs").height();

                            if (overlayJobsHeight > (windowHeight - (windowHeight / 10))) {
                                $("#overlayjobs").addClass("scroll-long-content");
                            }

                            return true;
                        }
                        // }
                    });
            }


        }).fail((error) => {
            console.error(error);
        });
}


function animateProgressBar(progress) {
    current_progress = parseFloat($(".progress-bar").attr("aria-valuenow"));
    next_progress = current_progress + progress;
    $(".progress-bar").css("width", next_progress + "%").attr("aria-valuenow", next_progress);
    console.log($(".progress-bar").css("width"));
    console.log($(".progress-bar").attr("aria-valuenow"));
}

function setProgressBarValue(value) {
    $(".progress-bar").css("width", parseInt(value) + "%").attr("aria-valuenow", parseInt(value));
}

function resetProgressBar() {
    $(".progress-bar").css("width", "0%").attr("aria-valuenow", "0");
}



function downloadJobButtonHandler(button) {
    $("#overlayjobprocessing").removeClass("show");
    $("#overlayjobs").addClass("hide-to-left");
    setProgressBarValue(0);
    downloadJob(button);
} 

function setJobProcessingTitle(message) {
    console.log(message);
    var title = $("#jobProcessingTitle");
    
    function eventListener(transition) {
        if (transition.target == title[0]) {
            if (title.hasClass("fade-text")) {
                title.html(message);
                title.removeClass("fade-text");
                title[0].removeEventListener("transitionend", eventListener);
            }
        }
    }
    title[0].addEventListener("transitionend", eventListener);
    title.addClass("fade-text");
}


async function downloadJob(button) {
    console.log("downloadJob() called");
    // disable all buttons
    let data = {"job_id": button.id, "hpc": $("button.fetch-jobs.active").attr("name")}
    console.log(data);
    
    $("#jobProcessingTitle").html("Downloading job:<br>" + button.id + "<br>");
    // await sleep(500);
    // $("#progressBarFetchJob").addClass("s40").removeClass("s4 s2");
    // setProgressBarValue(40);
    $.getJSON("/hh-neuron-builder/fetch-job-result/" + exc, data)
        .done((result) => {
            showLoadingAnimation('')
        }).fail((error) => {

        });

    $.getJSON("/hh-neuron-builder/fetch-job-result/" + jobId + "/" + req_pattern + "/", function(data) {
        if (data["response"] == "KO") {
            closeDownloadJob();
            openErrorDiv(data["message"], "error");
            return false;
        }
        setJobProcessingTitle("Running Analysis<br> ");
        setProgressBarValue(80);
        var p = $.getJSON("/hh-neuron-builder/run-analysis/" + req_pattern, async function(modifydata) {
            var resp_flag = false;
            console.log(modifydata);
            if (modifydata["response"] == "KO") {
                closeDownloadJob();
                openErrorDiv(data["message", "error"]);
                return false;
            } else {
                var resp_flag = true;
                setJobProcessingTitle("Creating ZIP file<br> ");
                // $("#jobProcessingTitle").html("Creating ZIP file<br>")
                $("#progressBarFetchJob").addClass("s4").removeClass("s40 s2");
                setProgressBarValue(80);
                await sleep(4000);
                $.getJSON("/hh-neuron-builder/zip-sim/" + jobId + "/" + req_pattern, async function(zip_data) {
                    if (zip_data["response"] == "KO") {
                        closeDownloadJob();
                        openErrorDiv(zip_data["message"], "error");
                        return false;
                    } else {
                        // $("#jobProcessingTitle").html("Completing<br>");
                        setJobProcessingTitle("Completing...<br> ");
                        $("#progressBarFetchJob").addClass("s2").removeClass("s40 s4");
                        setProgressBarValue(100);
                        await sleep(2000);
                    }
                    checkConditions();
                    // $("#overlayjobprocessing").css("display", "none");
                    $("#overlayjobprocessing").removeClass("show");
                    // $("#overlaywrapper").css("display", "none");
                }).fail(function (error) { 
                    console.log("failing on zip-sim");
                    console.log(error);
                })
            }
        });
        setTimeout(function(){ 
            if (resp_flag) {
            } else { 
                p.abort();
                closePleaseWaitDiv();
                openErrorDiv("Your request has expired.<br>Please verify that you are not behind a firewall and/or your data are not too big to be processed in less than 10 minutes", 'error')
            }
        }, 600000);
    });
}