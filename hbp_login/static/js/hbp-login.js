
var decodeHTML = function (html) {
    var txt = document.createElement('textarea');
    txt.innerHTML = html;
    return txt.value;
};

var LOGIN_CONFIG = JSON.parse(decodeHTML(sessionStorage.getItem("login_config", login_config)));
console.log(LOGIN_CONFIG)

let client = new jso.JSO({
    providerID: "HBP",
    client_id: LOGIN_CONFIG.hbp_client_id,
    redirect_uri: LOGIN_CONFIG.hbp_redirect_uri,
    authorization: LOGIN_CONFIG.hbp_authorization_url
})

//const csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
//
//function csrfSafeMethod(method) {
//    // these HTTP methods do not require CSRF protection
//    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
//}
//$.ajaxSetup({
//    beforeSend: function(xhr, settings) {
//        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
//            xhr.setRequestHeader("X-CSRFToken", csrftoken);
//        }
//    }
//});


function login() {
    console.log('LOGIN()');
    try {
        client.callback();
    } catch (e) {
        console.warn("Issue decoding the token");
    }
    var authorization = client.getToken();
    authorization.then((session) => {

        var div = document.getElementById("form_sample");
        div.style.display = "none";

        var form = document.createElement("form"); // Create New Element Form
        form.setAttribute("action", "")
        form.setAttribute("method", "post"); // Setting Method Attribute on Form
        div.appendChild(form);

        var token_input = document.createElement("input"); // Create Input Field for Name
        token_input.setAttribute("type", "text");
        token_input.setAttribute("name", "token");
        token_input.value = "Bearer " + session.access_token;
        form.appendChild(token_input);

        var submit = document.createElement("input"); // Append Submit Button
        submit.setAttribute("type", "submit");
        submit.setAttribute("name", "dsubmit");
        submit.setAttribute("value", "Submit");
        form.appendChild(submit);

        form.submit()
    });
}


$(document).ready(() => {
    login();
});
