$(document).ready(function(){
    document.getElementById('hbp-button').onclick = exitEfelg;

    function exitEfelg(){
        $get('/efelg/exit-efelg');
        // window.top.location.href = "/logout/hbp";
        //  window.top.location.href = "https://services.humanbrainproject.eu/oidc/login?next=https://collab.humanbrainproject.eu/#/collab/1655/nav/28538";
        //    window.location.href = "https://collab.humanbrainproject.eu/#/collab/1655/nav/28538";
    }
}
