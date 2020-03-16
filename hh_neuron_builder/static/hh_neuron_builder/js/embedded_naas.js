var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;

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
    document.getElementById("overlaywrappermsgnaas").style.display = "none";
    document.getElementById("mainPageDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}


// open div for model catalog registration
function displayModelRegistrationDiv() {
    document.getElementById("overlaywrapmodreg").style.display = "block";
    document.getElementById("mainPageDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";

    toggleElVisibility(displayBlock=["#overlaywrappermsgnaas"], displayNone=['#overlaywrapmodreg'], 
            eventsNone=["#mainPageDiv"], eventsAuto=[]);
    fillMessageDiv(msg="Please wait ...", msgTag="default", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=true, 
            waitElId="#spinning-wheel-naas", okBtnFlag=false, okBtnId="#msg-ok-btn");

    $.getJSON("/hh-neuron-builder/get-data-model-catalog/" + req_pattern, function(data){
        document.getElementById("modelName").value = data["name"]
        document.getElementById("modelLicense").value = "CC BY" // default license
        if (data['base_model'] == "") {
            document.getElementById("base-model").innerHTML = 
                "<i>* the original model used for the optimization is not available<\i>"
        } else {
            document.getElementById("base-model").innerHTML = 
                "<i>* the original model used for the optimization is: ".concat(data["base_model"]).concat("<\i>");
        }
        if (data['response'] == "OK"){
            // TODO: populate default values for form fields with returned model JSON info
            document.getElementById("authorFirstName").value = data["author"][0]["given_name"]
            document.getElementById("authorLastName").value = data["author"][0]["family_name"]
            document.getElementById("ownerFirstName").value = data["owner"][0]["given_name"]
            document.getElementById("ownerLastName").value = data["owner"][0]["family_name"]
            document.getElementById("modelPrivate").value = data["private"]
            document.getElementById("modelOrganization").value = data["organization"]
            document.getElementById("modelSpecies").value = data["species"]
            document.getElementById("modelBrainRegion").value = data["brain_region"]
            document.getElementById("modelCellType").value = data["cell_type"]
            document.getElementById("modelScope").value = data["model_scope"]
            document.getElementById("modelAbstraction").value = data["abstraction_level"]
            document.getElementById("modelDescription").value = data["description"]
        } else {
            // TODO: populate default values for form fields with returned model JSON info
            document.getElementById("authorFirstName").value = ""
            document.getElementById("authorLastName").value = ""
            document.getElementById("ownerFirstName").value = ""
            document.getElementById("ownerLastName").value = "" 
            document.getElementById("modelPrivate").value = false
            document.getElementById("modelOrganization").value = "<<empty>>" 
            document.getElementById("modelSpecies").value = "Undefined"
            document.getElementById("modelBrainRegion").value = "other"
            document.getElementById("modelCellType").value = "other"
            document.getElementById("modelScope").value = "other"
            document.getElementById("modelAbstraction").value = "other"
            document.getElementById("modelDescription").value = "" 
        }
 
    toggleElVisibility(displayBlock=["#overlaywrapmodreg"], displayNone=['#overlaywrappermsgnaas'], 
            eventsNone=["#mainPageDiv"], eventsAuto=[]);
    });
} 

// Manage feature files upload button
function closeModelRegistrationDiv() {
    document.getElementById("overlaywrapmodreg").style.display = "none";
    document.getElementById("mainPageDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}

// 
function backToWorkflow() {
    window.location.href = "/hh-neuron-builder/workflow";
}

//
function registerModel() {
    var checks = checkEditValues(editList=["#authorFirstName", "#authorLastName",
        "#ownerFirstName", "#ownerLastName"]);
    if (checks["response"] == "KO"){
        toggleElVisibility(displayBlock=["#overlaywrappermsgnaas"], displayNone=['#overlaywrapmodreg'], 
            eventsNone=["#mainPageDiv"], eventsAuto=[]);
        fillMessageDiv(msg=checks["message"], msgTag="error", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=fals, 
            waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
        return true
    }

    // open please wait div
    toggleElVisibility( displayBlock=["#overlaywrappermsgnaas"], displayNone=['#overlaywrapmodreg'], 
            eventsNone=["#mainPageDiv"], eventsAuto=[]);
    fillMessageDiv(msg="Please wait ...", msgTag="default", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=true, 
            waitElId="#spinning-wheel-naas", okBtnFlag=false, okBtnId="#msg-ok-btn");
    //manage form to register model in model catalog
    var $modelRegisterForm = $('#modelRegisterForm');
    $modelRegisterForm.submit(function(e){
        e.preventDefault();
        $.post('/hh-neuron-builder/register-model-catalog/' + req_pattern + '/', $(this).serialize(), function(response){
            if (response['response'] == "KO"){
                fillMessageDiv(msg="Some error occurred", msgTag="error",  
                msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=false, 
                waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
            } else {
                fillMessageDiv(msg=response["message"], msgTag="success", 
                msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=false, 
                waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
            }
        },'json');
        return false;
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
