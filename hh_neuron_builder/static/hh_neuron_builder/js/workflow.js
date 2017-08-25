$(document).ready(function(){
    // check conditions on function activation
    checkConditions();

    // manage form for submitting run parameters
    var $form = $('#submitRunParam');
    $form.submit(function(){
        $.post($(this).attr('action'), $(this).serialize(), function(response){
            closeParameterDiv();
            checkConditions();
            //window.location.href = "/hh-neuron-builder/workflow"
        },'json');
        return false;
    });

    // manage form to upload simulation zip file 
    var $uploadForm = $('#uploadForm');
    $uploadForm.submit(function(e){
        document.getElementById("res-upload-info-div").innerHTML = "Uploading file to server. Please wait ...";
        var uploadFormData = new FormData($(this)[0]);
        $.ajax({
            url: $(this).attr("action"),
            data:uploadFormData,
            type: 'POST',
            contentType: false,
            processData: false,
            success: function(resp){
                checkConditions();
                document.getElementById("res-upload-info-div").innerHTML = ""
                    //window.location.href = "/hh-neuron-builder/workflow"
            },  
        });
        e.preventDefault();
    });

    
    // assign functions to buttons' click
    //
    document.getElementById("test-button").onclick = displayPleaseWaitDiv;
    document.getElementById("test-back-button").onclick = displayOpEndDiv;
    document.getElementById("opt-set-btn").onclick = openParameterDiv;
    document.getElementById("run-sim-btn").onclick = inSilicoPage;
    document.getElementById("feat-efel-btn").onclick = efelPage;
    document.getElementById("feat-up-btn").onclick = reloadCurrentPage;
    document.getElementById("opt-db-hpc-btn").onclick = chooseOptModel;
    document.getElementById("opt-up-btn").onclick = reloadCurrentPage;
    document.getElementById("opt-fetch-btn").onclick = reloadCurrentPage;
    document.getElementById("del-feat").onclick = deleteFeatureFiles;
    document.getElementById("del-opt").onclick = deleteOptFiles;
    document.getElementById("launch-opt-btn").onclick = runOptimization;
});


// serve embedded-efel-gui page
function efelPage() {
    window.location.href = "/hh-neuron-builder/embedded-efel-gui/";
}

// serve embedded-naas page
function inSilicoPage() {
    document.getElementById("res-upload-info-div").innerHTML = "Uploading to <strong> Neuron As A Service </strong>. Please wait ..."
        $.getJSON("/hh-neuron-builder/upload-to-naas", function(uploaddata){
            $.getJSON("/hh-neuron-builder/model-loaded-flag", function(data){
                var o = data["response"];
                if (o == "nothing"){
                    window.location.href = "";
                } else {
                    document.getElementById("res-upload-info-div").innerHTML = ""
                        window.location.href = "/hh-neuron-builder/embedded-naas/";
                } 
            });

        });
}

// serve choose-opt-model page
function chooseOptModel() {
    window.location.href = "/hh-neuron-builder/choose-opt-model"; 
}

// reload current page
function reloadCurrentPage() {
    window.location.href = "";
}

// open side div for optimization run parameter settings
function openParameterDiv() {
    document.getElementById("overlaywrapper").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// close side div for optimization run parameter settings
function closeParameterDiv() {
    document.getElementById("overlaywrapper").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
} 

//
function checkConditions(){
    $.getJSON('/hh-neuron-builder/check-cond-exist', function(data){
        if (data['feat']){
            document.getElementById('feat-bar').style.background = "green";
            document.getElementById('del-feat').disabled = false;
        } else {
            document.getElementById('feat-bar').style.background = "red";
            document.getElementById('del-feat').disabled = true;
        };

        if (data['opt_files']){
            document.getElementById('opt-files-bar').style.background = "green";
            document.getElementById('del-opt').disabled = false;
        } else {
            document.getElementById('opt-files-bar').style.background = "red";
            document.getElementById('del-opt').disabled = true;
        };

        if (data['opt_set']){
            document.getElementById('opt-param-bar').style.background = "green";
        } else {
            document.getElementById('opt-param-bar').style.background = "red";
        };


        if (data['opt_flag']){
            document.getElementById("optlaunchimg").src = "/static/images/ok_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "Optimization job submitted";
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(0, 110, 0, 0.08)';
        } else {
            document.getElementById("optlaunchimg").src = "/static/images/ko_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "No job submitted";
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(255, 255, 255,0.0)';
        }

        if (data['feat'] & data['opt_files'] & data['opt_set']){
            document.getElementById("launch-opt-btn").disabled = false;  
        } else {
            document.getElementById("launch-opt-btn").disabled = true;  
        };

        // Simulation panel
        if (data['run_sim']){
            document.getElementById("opt-res-bar").style.background = "green";  
            document.getElementById("run-sim-btn").disabled = false;  
            document.getElementById("run-sim-div").style.backgroundColor='rgba(0, 110, 0, 0.08)';
        } else {
            document.getElementById("opt-res-bar").style.background = "red";  
            document.getElementById("run-sim-btn").disabled = true;  
            document.getElementById("run-sim-div").style.backgroundColor='rgba(255, 255, 255, 0.06)';
        };

    });
}

// Delete features.json and protocol.json files from containing folder
function deleteFeatureFiles() {
    var resp = confirm("Are you sure you want to delete current feature files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-feature-files", function(data){
            checkConditions();
        });
    }
}

// Delete source optimization files from folder
function deleteOptFiles() {
    var resp = confirm("Are you sure you want to delete current optimization files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-opt-files", function(data){
            checkConditions();
        });
    }
}

// Run optimization on hpc system 
function runOptimization() {
    displayPleaseWaitDiv();
    document.getElementById("waitdynamictext").innerHTML = "Launching the optimization";
    $.getJSON("/hh-neuron-builder/run-optimization", function(data){
        checkConditions();
        /*
         * var status_code = data['status_code'];
        if (status_code != 200) {
            document.getElementById("optlaunchimg").src = "/static/images/ko_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "Job not submitted with error: ".concat(status_code.toString());
        } else {
            document.getElementById("optlaunchimg").src = "/static/images/ok_red.png";
            document.getElementById("optlaunchtextspan").innerHTML = "Job successfully submitted";
        }
        */
    });
    hidePleaseWaitDiv();
}


// Display please wait div
function displayPleaseWaitDiv() {
    document.getElementById("overlaywrapperwait").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// Hide please wait message div
function hidePleaseWaitDiv() {
    document.getElementById("overlaywrapperwait").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

// Display operation ended message div
function displayOpEndDiv() {
    document.getElementById("overlaywrapperop").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
}

// Hide please wait message div
function hideOpEndDiv() {
    document.getElementById("overlaywrapperop").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

// Update please wait div message
function updatePleaseWaitDivMessage() {

}
