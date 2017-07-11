$(document).ready(function(){
    // check conditions on function activation
    checkConditions();

    // manage form for submitting run parameters
    var $form = $('#submitRunParam');
    $form.submit(function(){
        $.post($(this).attr('action'), $(this).serialize(), function(response){
            closeSideDiv();
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
    document.getElementById("run-sim-btn").onclick = inSilicoPage;
    document.getElementById("feat-efel-btn").onclick = efelPage;
    document.getElementById("feat-up-btn").onclick = reloadCurrentPage;
    document.getElementById("opt-db-hpc-btn").onclick = chooseOptModel;
    document.getElementById("opt-up-btn").onclick = reloadCurrentPage;
    document.getElementById("opt-fetch-btn").onclick = reloadCurrentPage;
    document.getElementById("del-feat").onclick = deleteFeatureFiles;
    document.getElementById("del-opt").onclick = deleteOptFiles;
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
function openSideDiv() {
    document.getElementById("optSideDiv").style.width = "250px";
    document.getElementById("mainDiv").style.marginLeft = "250px";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.getElementById("title").style.marginLeft = "250px";
}

// close side div for optimization run parameter settings
function closeSideDiv() {
    document.getElementById("optSideDiv").style.width = "0";
    document.getElementById("mainDiv").style.marginLeft= "0";
    document.getElementById("title").style.marginLeft = "0";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.backgroundColor = "white";
} 

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

        if (data['feat'] & data['opt_files'] & data['opt_set']){
            document.getElementById("launch-opt-btn").disabled = false;  
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(0, 110, 0, 0.08)';
        } else {
            document.getElementById("launch-opt-btn").disabled = true;  
            document.getElementById("cell-opt-div").style.backgroundColor='rgba(255, 255, 255,0.0)';
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


function deleteFeatureFiles() {
    var resp = confirm("Are you sure you want to delete current feature files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-feature-files", function(data){
            checkConditions();
        });
    }
}

function deleteOptFiles() {
    var resp = confirm("Are you sure you want to delete current optimization files?");
    if (resp) {
        $.getJSON("/hh-neuron-builder/delete-opt-files", function(data){
            checkConditions();
        });
    }
}
