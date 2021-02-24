var exc = sessionStorage.getItem("exc", exc) ?  sessionStorage.getItem("exc") : "";
var ctx = sessionStorage.getItem("ctx", ctx) ? sessionStorage.getItem("ctx") : "";
var req_pattern = exc + '/' + ctx;
var _modelFieldMapping = {"model_scope":"modelScope", "cell_type":"modelCellType", 
    "brain_region":"modelBrainRegion", "organization":"modelOrganization",
    "abstraction_level":"modelAbstraction", "species":"modelSpecies"};
var _reg_collab;
sessionStorage.setItem("mcModUrl", "");

$(document).ready(function(){
    // set onclick events
    // document.getElementById("msg-continue-ok-btn").onclick = displayModelRegistrationDiv;
    // document.getElementById("msg-continue-cancel-btn").onclick = cancelRegistration;
    // document.getElementById("msg-ok-btn").onclick = closeMsgDiv;

    var reg_model = "";

    $.getJSON("/hh-neuron-builder/model-loaded-flag/" + req_pattern, function(data){
        var o = data["response"];
        console.log("var o = " + o);
        if (o == "KO"){
            window.location.href = "";
        } else {
            console.log("apro link !");
            document.getElementById("naas-frame").setAttribute("src", "https://blue-naas-bsp-epfl.apps.hbp.eu/#/model/" + o);
        }
    });
});

function closeMsgDiv(){
    toggleElVisibility(displayBlock=[], displayNone=['overlaywrappermsgnaas'], 
            eventsNone=[], eventsAuto=["mainPageDiv"]);
}


// open div for model catalog registration
function displayModelRegistrationDiv() {
    if (_reg_collab == "storage_collab") {
        fillMessageDiv(msg="Please wait ...", msgTag="default", 
                msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=true, 
                waitElId="#spinning-wheel-naas", okBtnFlag=false, okBtnId="#msg-ok-btn");
        toggleElVisibility(displayBlock=["overlaywrappermsgnaas"], displayNone=['overlaywrapmodreg', 'ow-msg-continue-naas'], 
                eventsNone=["mainPageDiv"], eventsAuto=[]);
    }

    $.getJSON("/hh-neuron-builder/get-data-model-catalog/" + req_pattern + "/", function(data){
        document.getElementById("modelName").value = data["name"]
            document.getElementById("modelLicense").value = "CC BY" // default license

            var keys = Object.keys(_modelFieldMapping);
        var k; 
        for (k in _modelFieldMapping){
            //var k = keys[i];
            var field = _modelFieldMapping[k];
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

    toggleElVisibility(displayBlock=["overlaywrappermsgnaas"], 
        displayNone=['overlaywrapmodreg'], eventsNone=["mainPageDiv"], 
        eventsAuto=[]);

    if (checks["response"] == "KO"){
        fillMessageDiv(msg=checks["message"], msgTag="error", 
                msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=false, 
                waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
        return true
    }

    // open please wait div
    fillMessageDiv(msg="Please wait ...", msgTag="default", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=true, 
            waitElId="#spinning-wheel-naas", okBtnFlag=false, okBtnId="#msg-ok-btn");

    //manage form to register model in model catalog
    $('#modelRegisterForm').submit(function(e){
        e.stopImmediatePropagation();
        e.preventDefault();
        $.post("/hh-neuron-builder/register-model-catalog/" + _reg_collab + "/" + req_pattern + "/", $(this).serialize(), function(response){
            if (response['response'] == "KO"){
                fillMessageDiv(msg="An error occurred.<br>Please try again later.", msgTag="error",  
                        msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=false, 
                        waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
            } else {
                fillMessageDiv(msg=response["message"], msgTag="success", 
                        msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=false, 
                        waitElId="#spinning-wheel-naas", okBtnFlag=true, okBtnId="#msg-ok-btn");
                sessionStorage.setItem("mcModUrl", response["reg_mod_url"]);
                document.getElementById("reg-mod-main-btn").innerHTML = "Show Model Catalog entry";
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
            return {"response":"KO", "message":"Please fill all the required fields"}
        }    
    }
    return {"response":"OK", "message":""}
}

// manage register button clicks
function registerModelMain(){
    var mcModUrl = sessionStorage.getItem("mcModUrl");
    toggleElVisibility(displayBlock=["overlaywrappermsgnaas"], 
        displayNone=['overlaywrapmodreg'], eventsNone=["mainPageDiv"], 
        eventsAuto=[]);
    fillMessageDiv(msg="Please wait ...", msgTag="default", 
            msgTextId="#msgtextnaas", msgDiv="#overlaymsgnaas", waitFlag=true, 
            waitElId="#spinning-wheel-naas", okBtnFlag=false, okBtnId="#msg-ok-btn");
    if (mcModUrl == ""){
        $.getJSON("/hh-neuron-builder/get-user-clb-permissions/" + req_pattern, function(data){
            if (data["response"] == "OK"){
                _reg_collab = "current_collab";
                displayModelRegistrationDiv();
            } else {
                var message = "You do not have write permissions for the present \
                               Collab: this will prevent you from saving your model \
                               in the Collab instance of the Model Catalog.<br><br>\
                               If you proceed, the model will be saved in a different\
                               Collab and its url will be shown after the registration.\
                               In this case, if you want to edit your model's metadata, \
                               you will need to contact <strong>support@humanbrainproject.eu.</strong><br><br>\
                               Alternatively, you can run the HH-Neuron-Builder \
                               tool in one of the Collabs you are a member of.\
                               This will give you full control on the registered model."
                               fillMessageDiv(msg=message, msgTag="info",  
                                       msgTextId="#continue-msg-text-naas", msgDiv="#ow-msg-continue-naas", waitFlag=false, 
                                       waitElId="", okBtnFlag=false, okBtnId="");
                toggleElVisibility( displayBlock=["ow-msg-continue-naas"], displayNone=['overlaywrappermsgnaas'], 
                        eventsNone=[], eventsAuto=[]);
                _reg_collab = "storage_collab";
            }
        });
    } else {
        window.open(mcModUrl, '_blank');
    }
}

function cancelRegistration(){
    toggleElVisibility( displayBlock=[], displayNone=['ow-msg-continue-naas', 'overlaywrappermsgnaas'], 
            eventsNone=[], eventsAuto=['mainPageDiv']);

}
