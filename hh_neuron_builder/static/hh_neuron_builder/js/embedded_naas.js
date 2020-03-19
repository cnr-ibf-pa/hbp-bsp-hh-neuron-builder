var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;
var modelFieldMapping = {"model_scope":"modelScope", "cell_type":"modelCellType", 
        "brain_region":"modelBrainRegion", "organization":"modelOrganization",
        "abstraction_level":"modelAbstraction", "species":"modelSpecies"};

$(document).ready(function(){
    document.getElementById("back-to-wf-btn").onclick = backToWorkflow;
    document.getElementById("msg-ok-btn").onclick = closeMsgDiv;
    document.getElementById("register-model-btn").onclick = registerModel;
    document.getElementById("reg-mod-main-btn").onclick = displayModelRegistrationDiv;
    document.getElementById("cancel-model-register-btn").onclick = closeModelRegistrationDiv;

    $.getJSON("/hh-neuron-builder/model-loaded-flag/" + req_pattern, function(data){
        var o = data["response"];
        if (o == "KO"){
            window.location.href = "";
        } else {
            document.getElementById("naas-frame").setAttribute("src","https://blue-naas.humanbrainproject.eu/#/model/" + o)
        }
    });
});

function closeMsgDiv(){
    toggleElVisibility(displayBlock=[], displayNone=['overlaywrappermsgnaas'], 
            eventsNone=[], eventsAuto=["mainPageDiv"]);
}


// open div for model catalog registration
function displayModelRegistrationDiv() {

    toggleElVisibility(displayBlock=["overlaywrappermsgnaas"], displayNone=['overlaywrapmodreg'], 
            eventsNone=["mainPageDiv"], eventsAuto=[]);
    fillMessageDiv(msg="Please wait ...", msgTag="default", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=true, 
            waitElId="#spinning-wheel-naas", okBtnFlag=false, okBtnId="#msg-ok-btn");

    $.getJSON("/hh-neuron-builder/get-data-model-catalog/" + req_pattern, function(data){
        document.getElementById("modelName").value = data["name"]
        document.getElementById("modelLicense").value = "CC BY" // default license
        
        var keys = Object.keys(modelFieldMapping);
        var k; 
        for (k in modelFieldMapping){
            //var k = keys[i];
            var field = modelFieldMapping[k];
            var crr_field = document.getElementById(field);
            var crr_options = "";
            var f;
            for (f in data["default_values"][k]){
                crr_options += "<option>" + data["default_values"][k][f]  + "</option>"
            }
            crr_field.innerHTML = crr_options;
        }
        
        
        if (data['base_model'] == "") {
            document.getElementById("base-model").innerHTML = 
                "<i>* the original model used for the optimization is not available<\i>"
        } else {
            document.getElementById("base-model").innerHTML = 
                "<i>* the original model used for the optimization is: ".concat(data["base_model"]).concat("<\i>");
        }
        if (data['response'] == "OK"){
            // TODO: populate default values for form fields with returned model JSON info
            document.getElementById("authorFirstName").value = data["fetched_values"]["author"][0]["given_name"]
            document.getElementById("authorLastName").value = data["fetched_values"]["author"][0]["family_name"]
            document.getElementById("ownerFirstName").value = data["fetched_values"]["owner"][0]["given_name"]
            document.getElementById("ownerLastName").value = data["fetched_values"]["owner"][0]["family_name"]
            document.getElementById("modelPrivate").value = data["fetched_values"]["private"]
            document.getElementById("modelOrganization").value = data["fetched_values"]["organization"]
            document.getElementById("modelSpecies").value = data["fetched_values"]["species"]
            document.getElementById("modelBrainRegion").value = data["fetched_values"]["brain_region"]
            document.getElementById("modelCellType").value = data["fetched_values"]["cell_type"]
            document.getElementById("modelScope").value = data["fetched_values"]["model_scope"]
            document.getElementById("modelAbstraction").value = data["fetched_values"]["abstraction_level"]
            document.getElementById("modelDescription").value = data["fetched_values"]["description"]
        } else {
            // TODO: populate default values for form fields with returned model JSON info
            document.getElementById("authorFirstName").value = ""
            document.getElementById("authorLastName").value = ""
            document.getElementById("ownerFirstName").value = ""
            document.getElementById("ownerLastName").value = "" 
            document.getElementById("modelPrivate").value = false
            document.getElementById("modelDescription").value = "" 
        }
 
    toggleElVisibility(displayBlock=["overlaywrapmodreg"], displayNone=['overlaywrappermsgnaas'], 
            eventsNone=[], eventsAuto=[]);
    });
} 

// Close model registration div
function closeModelRegistrationDiv() {
    toggleElVisibility(displayBlock=[], displayNone=['overlaywrapmodreg'], 
            eventsNone=[], eventsAuto=["mainPageDiv"]);
}

// 
function backToWorkflow() {
    window.location.href = "/hh-neuron-builder/workflow";
}

//
function registerModel() {
    var checks = checkEditValues(editList=["#authorFirstName", "#authorLastName",
        "#ownerFirstName", "#ownerLastName"]);

    toggleElVisibility(displayBlock=["overlaywrappermsgnaas"], displayNone=['overlaywrapmodreg'], 
            eventsNone=["mainPageDiv"], eventsAuto=[]);

    if (checks["response"] == "KO"){
        fillMessageDiv(msg=checks["message"], msgTag="error", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=fals, 
            waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
        return true
    }

    // open please wait div
    fillMessageDiv(msg="Please wait ...", msgTag="default", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=true, 
            waitElId="#spinning-wheel-naas", okBtnFlag=false, okBtnId="#msg-ok-btn");

    //manage form to register model in model catalog
    //var $modelRegisterForm = $('#modelRegisterForm');
    $('#modelRegisterForm').submit(function(e){
        e.stopImmediatePropagation();
        e.preventDefault();
        $.post('/hh-neuron-builder/register-model-catalog/' + req_pattern , $(this).serialize(), function(response){
            if (response['response'] == "KO"){
                fillMessageDiv(msg="Some error occurred", msgTag="error",  
                msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=false, 
                waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
            } else {
                fillMessageDiv(msg=response["message"], msgTag="success", 
                msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=false, 
                waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
            }
            toggleElVisibility( displayBlock=["overlaymsgnaas"], displayNone=['overlaywrapmodreg'], 
                    eventsNone=[], eventsAuto=[]);
        },'json');
    });
}

// check inserted values
function checkEditValues(editList=[]){
    for (var i = 0; i < editList.length; i++){
        if ($(editList[i]).val().trim() == ""){
            return {"response":"KO", "message":"Please fill the required fields"}
        }    
    }
    return {"response":"OK", "message":""}
}

