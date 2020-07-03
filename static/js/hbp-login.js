
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


function login() {
    console.log('LOGIN()');
    try {
        client.callback();
    } catch (e) {
        console.warn("Issue decoding the token");
    }
    var authorization = client.getToken();
    authorization.then((session) => {
        $.ajax({
            url: "http://127.0.0.1:8000/hbp-login/create-session",
            headers: {
                "Authorization": "Bearer " + session.access_token,
            },
            type: "GET",
            success: function(data) {
                console.log('SUCCESS')
                console.log(data);
                window.location.replace('http://127.0.0.1:8000/efelg')
            },
            error: function(data) {
                console.error("User not detected");
            }
        });
    });
}


$(document).ready(() => {
    login();
});
