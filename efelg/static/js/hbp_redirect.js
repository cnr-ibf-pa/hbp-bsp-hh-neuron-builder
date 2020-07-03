$(document).ready(function(){
    document.getElementById('hbp-button').onclick = exitEfelg;

    function exitEfelg(){
        $get('/efelg/exit-efelg');
    }
}
