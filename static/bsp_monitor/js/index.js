var IDS = "ga:101800494";
var FILTERS = 'ga:pagePath=~/collab/1655(\/.*|$)';
var RT_FILTERS = 'rt:pagePath=~/collab/1655(\/.*|$)';
var DIMENSIONS = 'rt:pagePath=~/collab/1655(\/.*|$)';
var REFRESH_TIME = 60000;

var rt_pages_dim = "rt:pagePath,rt:pageTitle,rt:minutesAgo";
var rt_metrics = "rt:pageviews";

var ga_pages_dim = "ga:pagePath,ga:pageTitle";
var ga_metrics = "ga:pageviews";


$(document).ready(function(){
    printLoadingMessage(["hist-pl-cnt", "rt-pl-cnt", "hist-leg-cnt"],["Loading ...", "Loading ...", ""]);
    //
    var todayUtc = moment.utc();
    var todayUtcFormat = todayUtc.format("YYYY-MM-DD");
    var todayToDate = moment.utc(todayUtcFormat).toDate();
    var today = moment(todayToDate).local().format("YYYY-MM-DD");

    var lastMonthUtc = moment.utc().subtract(1, "month");
    var lastMonthUtcFormat = lastMonthUtc.format("YYYY-MM-DD");
    var lastMonthToDate = moment.utc(lastMonthUtcFormat).toDate();
    var lastMonth = moment(lastMonthToDate).local().format("YYYY-MM-DD");

    var from_day = document.getElementById("from-day");
    var to_day = document.getElementById("to-day");

    from_day.setAttribute("value", lastMonth);
    to_day.setAttribute("value", today);
    document.getElementById("apply-btn").onclick = executeHistoryStat;
    document.getElementById("refresh-btn").onclick = executeRealTimeStat;

    $(window).on('resize', function() {
        printLoadingMessage(["hist-pl-cnt", "rt-pl-cnt", "hist-leg-cnt"],["Loading ...", "Loading ...", ""]);
        clearTimeout(window.resizedFinished);
        window.resizedFinished = setTimeout(function(){
            reloadAll();
        }, 1000);
    });

    function reloadAll(){

        plotGeo(IDS, FILTERS);
        plotSessionNum(IDS, FILTERS);
        plotUserNum(IDS, FILTERS);
        plotUserCum(IDS, FILTERS);//
        plotPagesView(IDS, FILTERS); //
        plotHistoryUsecases();
        plotRtUsers(IDS, RT_FILTERS);
        plotRtPages(IDS, RT_FILTERS, rt_pages_dim, rt_metrics);
        plotRtUsecases();

        /* BLOCK USED FOR PLOT NEEDED FOR THE REVIEW
        //plotHistoryUsecasesReview();
        //plotHistPagesReview_02(IDS, FILTERS);
        plotHistUCReview(IDS, FILTERS);
        plotHistUCExecReview(IDS, FILTERS);
        plotHistUCExecReview(IDS, FILTERS);
        */

    }

    function printLoadingMessage(cl_name, load_str){
        for (var j = 0; j < cl_name.length; j++){
            var crr_cl = cl_name[j];
            var crr_str = load_str[j];
            var t = document.getElementsByClassName(crr_cl);
            for (var i = 0; i<t.length; i++){
                document.getElementById(t[i]["id"]).innerHTML = "<div class='center-container' style='font-size:14px;position:absolute;top: 0px;left:0px;'>" +  crr_str + "</div>";
            }
        }
    }
    // manage from_day.onchange function
    from_day.onchange = function(){
        var from_day = document.getElementById("from-day");
        var to_day = document.getElementById("to-day");
        from_day.value = this.value;
        var to_day_crr_value = to_day.value;
        var to_day_crr_date = moment(to_day_crr_value);
        var from_day_crr_value = this.value;
        var from_day_crr_date = moment(from_day_crr_value);
        var date_diff = to_day_crr_date.diff(from_day_crr_date, 'days');
        if (date_diff < 0)
            to_day.value = this.value;
    }


    // manage to_day.onchange function
    to_day.onchange = function(){
        var from_day = document.getElementById("from-day");
        var from_day_crr_value = from_day.value;
        var from_day_crr_date = moment(from_day_crr_value);
        to_day.setAttribute("value", this.value);
        var to_day_crr_date = moment(this.value);
        var date_diff = to_day_crr_date.diff(from_day_crr_date, 'days');
        if (date_diff < 0){
            from_day.value = this.value;
        }
    }

})

function executeHistoryStat(){
    plotGeo(IDS, FILTERS);
    plotSessionNum(IDS, FILTERS);
    plotUserNum(IDS, FILTERS);
    plotUserCum(IDS, FILTERS); //
    plotPagesView(IDS, FILTERS); //
    plotHistoryUsecases();
    /* BLOCK USED FOR PLOT NEEDED FOR THE REVIEW
       plotHistPagesReview(IDS, FILTERS);
       plotHistUCReview(IDS, FILTERS);
       */
}

function executeRealTimeStat(){
    plotRtUsers(IDS, RT_FILTERS);
    plotRtPages(IDS, RT_FILTERS, rt_pages_dim, rt_metrics);
    plotRtUsecases();
}

/* get real time users - start */
function plotRtUsers(IDS, FILTERS){
    gapi.client.analytics.data.realtime.get({ids:IDS, metrics:"rt:activeUsers", filters:FILTERS}).then(function(t){
        var element = document.getElementById("active-users-container");
        var value_el = document.getElementById("active-users-value");
        var active_users = t.result.totalResults?+t.result.rows[0][0]:0; 

        crr_act_users = parseInt(value_el.innerHTML);
        var delta = parseInt(active_users - crr_act_users);
        var animationClass = "";
        if (delta>0)
            animationClass = 'is-increasing';
        else if (delta < 0)
            animationClass = 'is-decreasing';
        element.className += (' ' + animationClass);

        value_el.innerHTML = active_users;

        setClassChangeTimeout(element)
    });
}

/* get real time users - end */
function setClassChangeTimeout(element){
    setTimeout(function() {
        element.className =
            element.className.replace(/ is-(increasing|decreasing)/g, '');
    }, 4000);
}

/* get real time pages- start */
function plotRtPages(IDS, FILTERS, crr_dimensions, rt_metrics){
    gapi.client.analytics.data.realtime.get({ids:IDS, 
        dimensions:crr_dimensions, 
        metrics:rt_metrics, 
        filters:FILTERS})
        .then(function(t){
            if (!("result" in t) || !("rows" in t.result)){
                data = {
                    datasets:[{data:[1]}],
                    labels:["No visit"]
                }
            }else{
                var pages = {};
                var labels = {};
                var data = {};
                t.result.rows.forEach(function(row, i) {
                    if (parseInt(row[2]) >= 0 && parseInt(row[2]) <= 5){
                        pages[row[0]] = pages[row[0]] ? pages[row[0]]+(+row[3]):+row[3];
                        labels[row[0]] = labels[row[0]] ? labels[row[0]]:row[1];
                    }
                });

                if (Object.getOwnPropertyNames(pages).length == 0){
                    data = {
                        datasets:[{data:[1],
                            backgroundColor: palette('tol', 1).map(function(hex) {
                                return '#' + hex;
                            })
                        }],
                        labels:["No visit"]
                    }
                } else {
                    var data_all = [];
                    var labels_str = [];
                    var tooltips = [];
                    Object.keys(labels).forEach(function(key, index) {
                        data_all.push(pages[key]);
                        labels_str.push(labels[key]);
                        crr_ttip = labels[key].substr(0,labels[key].indexOf('-')-1);
                        if (crr_ttip == "" || crr_ttip == " "){
                            crr_ttip = "HBP-BSP";
                        }
                        tooltips.push(crr_ttip);
                    });  
                    data = { 
                        labels:tooltips,
                        datasets:[{
                            data:data_all,
                            backgroundColor: palette('tol', data_all.length).map(function(hex) {
                                return '#' + hex;
                            })
                        }]
                    };
                }
            }
            var ctx = makeCanvas('chart-rt-pages-container');
            var chart = new Chart(ctx, {
                type: 'doughnut',
                // The data for our dataset
                data: data,
                options: {
                    legend:{
                        position: 'top',
                        labels:{
                            boxWidth: 10,
                        },
                    }
                },
            });
        });
}
/* plot  real time pages- end */
function plotHistoryUsecases(){
    var dates = getDates();
    $.getJSON('/bsp-monitor/get-uc/' + dates[0] + '/' + dates[1] + '/', function (resp){
        var uc_hist_div = document.getElementById("uc-hist-div");
        uc_hist_div.innerHTML = "";

        var all_data = resp["uc_topics_full"];
        for (var key in all_data){
            var crr_global_container=document.createElement("div");
            var crr_container = document.createElement("div");
            var crr_figure = document.createElement("figure");
            var crr_legend_container = document.createElement("div");
            var crr_legend = document.createElement("ol");
            var crr_legend_id = key + "-legend";

            crr_container.setAttribute("class", "uc-t-box");
            crr_global_container.setAttribute("class","use-case-box");
            //
            crr_figure.setAttribute('id', key);
            crr_figure.setAttribute("class", "hist-boxes hist-pl-cnt");
            //

            crr_legend.setAttribute("class", "Chartjs-legend");
            crr_legend.setAttribute("class", "Chartjs-legend center-container legends hist-leg-cnt");
            crr_legend.setAttribute("id", crr_legend_id);
            //

            crr_container.appendChild(crr_figure);
            crr_container.appendChild(crr_legend);
            crr_global_container.appendChild(crr_container);

            uc_hist_div.appendChild(crr_global_container);

            var crr_t_labels = [];
            var crr_t_plot_labels = [];
            var crr_t_data = [];
            var data = {};
            var ctx = makeCanvas(key);
            if (resp["Response"] == "KO"){
                data = {
                    datasets:[{data:[]}],
                    labels:["No use case executed"]
                } 
            } else {
                for (var yy in resp["uc_topics_full"][key]){
                    crr_t_labels.push(yy);
                    crr_t_plot_labels.push("");
                    crr_t_data.push(resp["uc_topics_full"][key][yy]);
                }
            }
            data = {
                labels: crr_t_labels,
                datasets: [{data: crr_t_data,
                    label: key, 
                    backgroundColor: palette('tol', crr_t_data.length).map(function(hex) {
                        return '#' + hex;
                    })
                }]
            }
            var chart = new Chart(ctx, {
                type: 'bar',
                // The data for our dataset
                data: data,
                options: {
                    legend: {
                        display: false},
                        title: {
                            display: true,
                            text: 'Number of use case executions for: ' + key,
                            fontSize: 16,
                        },
                        scales: {
                            xAxes: [{
                                display: false,
                                barPercentage: 0.3,
                            }],
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true
                                }
                            }]
                        },
                }
            });
            generateLegend2(crr_legend_id, data, crr_t_labels);
        }
    });
}

/**
 * Create a visual legend inside the specified element based off of a
 * Chart.js dataset.
 * @param {string} id The id attribute of the element to host the legend.
 * @param {Array.<Object>} items A list of labels and colors for the legend.
 */
function generateLegend(id, items) {
    var legend = document.getElementById(id);
    legend.innerHTML = items.map(function(item) {
        var color = item.color || item.fillColor;
        var label = item.label;
        return '<li><i style="background:' + color + '"></i>' +
            escapeHtml(label) + '</li>';
    }).join('');
}


function generateLegend2(id, items, labels){
    var legend = document.getElementById(id);
    var data = items.datasets[0].data;
    var colors = items.datasets[0].backgroundColor;
    var innHtml = ""; 
    for (var i=0; i < data.length; i++){
        innHtml = innHtml + '<li><i style="background:' + colors[i] + '"></i>' + escapeHtml(labels[i]) + '</li>';  
    }
    legend.innerHTML = innHtml;
}

/**
 * Escapes a potentially unsafe HTML string.
 * @param {string} str An string that may contain HTML entities.
 * @return {string} The HTML-escaped string.
 */
function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function plotRtUsecases(){
    $.getJSON('/bsp-monitor/get-uc/0/0/', function (resp){
        document.getElementById("rt-uc-num").innerHTML = resp["rt_uc_num"];
        var data = {};
        if (resp["rt_uc_num"] == 0){
            data = {
                datasets:[{data:[1], 
                    backgroundColor: palette('tol', 1).map(function(hex) {
                        return '#' + hex;
                    })

                }],
                labels:["No use case executed"]
            } 
        }
        else {
            data = {
                datasets:[{data:resp["uc_topics_count"],
                    backgroundColor: palette('tol', resp["uc_topics_count"].length).map(function(hex) {
                        return '#' + hex;
                    })
                }],
                labels:resp["uc_topics"]
            } 
        }
        var ctx = makeCanvas('chart-rt-uc-container');
        var chart = new Chart(ctx, {
            type: 'doughnut',
            // The data for our dataset
            data: data,
            options: {
                legend:{
                    position: 'top',
                    labels:{
                        boxWidth: 10,
                    }
                }
            },
        });
    });
}


/* plot # of sessions */
function plotSessionNum(IDS, FILTERS){
    var dates = getDates();
    var session_num = query({
        'ids': IDS,
        'filters': FILTERS,
        'dimensions': 'ga:date',
        'metrics': 'ga:sessions',
        'start-date': dates[0],
        'end-date': dates[1]
    });
    Promise.all([session_num]).then(function(results) {

        var data1 = results[0].rows.map(function(row) { return +row[1]; });
        var labels = results[0].rows.map(function(row) { return +row[0]; });
        labels = labels.map(function(label) {
            return moment(label, 'YYYYMMDD').format('DD-MM');
        });

        var data = {
            labels : labels,
            datasets : [
            {
                data : data1,
                pointRadius : 0,
                pointHoverRadius : 3,
                label: "# sessions",
                backgroundColor:'rgba(0, 102, 0, 0.4)',
            },
            ]
        };

        var ctx = makeCanvas('session-num');
        var chart = new Chart(ctx, {
            type: 'line',
            // The data for our dataset
            data: data,
            options: {
                legend: {
                    display: false},
                    title: {
                        display: false,
                        text: 'Number of sessions',
                        fontSize: 16,
                    },
            }
        });
    });
}

/* plot # of users */
function plotUserNum(IDS, FILTERS){
    var dates = getDates();
    var user_num = query({
        'ids': IDS,
        'filters': FILTERS,
        'dimensions': 'ga:date',
        'metrics': 'ga:users, ga:newUsers',
        'start-date': dates[0],
        'end-date': dates[1]
    });

    Promise.all([user_num]).then(function(results) {

        var data1 = results[0].rows.map(function(row) { return +row[1]; });
        var data2 = results[0].rows.map(function(row) { return +row[2]; });

        var labels = results[0].rows.map(function(row) { return +row[0]; });
        labels = labels.map(function(label) {
            return moment(label, 'YYYYMMDD').format('DD-MM');
        });

        var data3=[];
        for (var i = 0, len = data1.length; i < len; i++) {
            data3[i]=data1[i]-data2[i];
        }

        var data = {
            labels : labels,
            datasets : [
            {     
                label: 'All users', 
                fillColor : 'rgba(221,185,209,0.5)',
                pointColor : 'rgba(221,185,209,1)',          
                pointRadius : 0,
                pointHoverRadius : 3,
                backgroundColor: 'rgba(221,185,209,0.5)',
                borderColor:'rgba(221,185,209,1)',
                borderWidth: 0.8,
                data : data1
            },
            {   
                label:'New users',
                pointRadius : 0,
                pointHoverRadius : 3,
                fillColor : 'rgba(197,134,176,0.6)',
                pointColor : 'rgba(197,134,176,1)',
                backgroundColor: 'rgba(197,134,176,0.6)',
                borderColor:'rgba(197,134,176,1)',
                borderWidth: 0.8,
                data : data2

            },
            {   
                label:'Returning users',
                pointRadius : 0,
                pointHoverRadius : 3,
                fillColor : 'rgba(239,74,129,0.4)',
                pointColor : 'rgba(239,74,129,1)',
                backgroundColor: 'rgba(239,74,129,0.4)',
                borderColor:'rgba(239,74,129,1)',
                borderWidth: 0.8,
                data : data3
            },

            ]
        };
        var ctx = makeCanvas('user-num');
        var chart = new Chart(ctx, {
            type: 'line',
            // The data for our dataset
            data: data,
            options: {
                legend: {
                    display: false,
                },
                title: {
                    display: false,
                    text: 'Number of users',
                    fontSize: 16,
                },
            }
        });
        generateLegend('legend-plotUserNum-container', data.datasets);
    });
}

function plotUserCum(IDS, FILTERS){
    var dates = getDates();
    var user_cum = query({
        'ids': IDS,
        'filters': FILTERS,
        'dimensions': 'ga:date',
        'metrics': 'ga:users, ga:newUsers',
        'start-date': dates[0],
        'end-date': dates[1]
    });

    Promise.all([user_cum]).then(function(results) {

        var data1 = results[0].rows.map(function(row) { return +row[1]; });
        var data2 = results[0].rows.map(function(row) { return +row[2]; });

        var labels = results[0].rows.map(function(row) { return +row[0]; });
        labels = labels.map(function(label) {
            return moment(label, 'YYYYMMDD').format('DD-MM');
        });

        var data3=[];
        for (var i = 0, len = data1.length; i < len; i++) {
            data3[i]=data1[i]-data2[i];
        }

        var cum_user=[];
        cum_user[0]=data1[0];
        var cum_newuser=[];
        cum_newuser[0]=data2[0];
        var cum_olduser=[];
        cum_olduser[0]=data3[0];

        for(var i=1, len = data1.length; i < len; i++){
            cum_user[i]=data1[i]+cum_user[i-1];
            cum_newuser[i]=data2[i]+cum_newuser[i-1];
            cum_olduser[i]=data3[i]+cum_olduser[i-1];
        }
        //console.log(Object.values(data1));
        var data = {
            labels : labels,
            datasets : [
            {     
                label: 'All users', 
                fillColor : 'rgba(221,185,209,0.5)',
                pointColor : 'rgba(221,185,209,1)',          
                pointRadius : 0,
                pointHoverRadius : 3,
                backgroundColor: 'rgba(221,185,209,0.5)',
                borderColor:'rgba(221,185,209,1)',
                borderWidth: 0.8,
                data : cum_user
            },
            {   
                label:'New users',
                pointRadius : 0,
                pointHoverRadius : 3,
                fillColor : 'rgba(197,134,176,0.6)',
                pointColor : 'rgba(197,134,176,1)',
                backgroundColor: 'rgba(197,134,176,0.6)',
                borderColor:'rgba(197,134,176,1)',
                borderWidth: 0.8,
                data : cum_newuser

            },
            {   
                label:'Returning users',
                pointRadius : 0,
                pointHoverRadius : 3,
                fillColor : 'rgba(239,74,129,0.4)',
                pointColor : 'rgba(239,74,129,1)',
                backgroundColor: 'rgba(239,74,129,0.4)',
                borderColor:'rgba(239,74,129,1)',
                borderWidth: 0.8,
                data : cum_olduser
            },
            ]
        };

        var ctx = makeCanvas('user-cum');
        var chart = new Chart(ctx, {
            type: 'line',
            // The data for our dataset
            data: data,
            options: {
                legend: {
                    position: 'top',
                    display: false,
                },
                title: {
                    display: false,
                    text: 'Cumulative number users',
                    fontSize: 16,
                },
            }
        });
        generateLegend('legend-plotUserCum-container', data.datasets);
    });

}
/*generate random color rgb*/
function rgbColor(){
    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    //generate random red, green and blue intensity
    var r = getRandomInt(0, 255);
    var g = getRandomInt(0, 255);
    var b = getRandomInt(0, 255);
    return "rgb(" + r + "," + g + "," + b + ")";
}

/* plot # number page visited */
function plotPagesView(IDS, FILTERS){
    var dates = getDates();
    query({
        'ids': IDS,
        'filters': FILTERS,
        'dimensions': 'ga:pagePath, ga:pageTitle, ga:date',
        'metrics': 'ga:pageviews',
        'sort': 'ga:pagePath',
        'start-date': dates[0],
        'end-date': dates[1],
        'max-results': 10000
    })
    .then(function(response) {

        var pages = [], data0=[],day=[], title=[];

        response.rows.forEach(function(row, i) {

            var t=row[1].split("-");
            if(title.indexOf(t[0]) == -1){   
                title.push(t[0]);
            }
            if(day.indexOf(+row[2])==-1){
                day.push(+row[2]);
            }
            day.sort();
            pages.push([t[0], +row[3], moment(row[2], 'YYYYMMDD').format('DD-MM'), row[0]]);
            data0.push(t[0]); //Url
        });

        var time=[];
        for(var i=0, len=day.length; i<len; i++){
            time.push(moment(day[i].toString(), 'YYYYMMDD').format('DD-MM'));
        }
        var ind=[], value=[], j=0;
        for(var i=0, len=title.length; i<len; i++){
            var v=[];
            ind.push(data0.indexOf(title[i]));

            for(;j<ind[i]; j++){
                v.push(pages[j]);
            }
            value.push(v);
        }

        var vet=[];

        for(var i=2, len=value.length; i<len; i++){
            var x=getData(time,value[i]);
            var col=rgbColor();
            vet.push({label:x[1], data:x[0],pointRadius:0,pointHoverRadius:3, backgroundColor:'rgb(0, 0, 0, 0)',fillColor:col,borderColor:col, borderWidth:1.5})
        }
        var data={
            labels:time,
            datasets:vet
        }

        var ctx = makeCanvas('page-view');
        var chart = new Chart(ctx, {
            type: 'line',
            // The data for our dataset
            data: data,
            labels : time,
            options: {
                legend: {display: false},
                title: {
                    display: false,
                    text: 'Pages views',
                    fontSize: 16,
                },
            }
        });
        generateLegend('legend-plotPagesView-container', data.datasets);
    });
}
function getData(time,value){
    var data1=[];
    for(var i=0, len=time.length; i<len; i++){
        data1.push(0);
    }        
    for(var i=0, len=value.length; i<len; i++){ 
        var x=time.indexOf(value[i][2]);
        data1[x]=value[i][1];
    }
    return [data1, value[0][0]]
}
/* get dates from html element */
function getDates(){
    var from_day = document.getElementById("from-day").value;
    var to_day = document.getElementById("to-day").value;
    return [from_day, to_day]
}

/**
 * Extend the Embed APIs `gapi.analytics.report.Data` component to
 * return a promise the is fulfilled with the value returned by the API.
 * @param {Object} params The request parameters.
 * @return {Promise} A promise.
 */
function query(params) {
    if (!(params['filters'])){
        params['filters'] = 'ga:pagePath=~/collab/1655(\/.*|$)';
    }
    return new Promise(function(resolve, reject) {
        var data = new gapi.analytics.report.Data({query: params});
        data.once('success', function(response) { resolve(response); })
            .once('error', function(response) { reject(response); })
            .execute();
    });
}

function setInnerHtml(id){
    document.getElementById(id).innerHTML = "<div class='center-container' style='font-size:14px;'>Loading ...</div>";
}

/* plot Geography of sessions - start */
function plotGeo(IDS, FILTERS){
    return new Promise(function(resolve, reject){
        var dates = getDates();
        var dataChart = new gapi.analytics.googleCharts.DataChart({
            query: {
                'ids': IDS,
                'filters': FILTERS,
                'metrics': 'ga:sessions',
                'dimensions': 'ga:country',
                "start-date": dates[0],
                "end-date": dates[1],
                'max-results': 10000,
            },
            chart: {
                container: 'embed-geo',
                type: 'GEO',
                options: {
                    width: '100%',
                    title: "Locations",
                    fontSize: 16,
                }
            }
        });
        dataChart.once('success', function(response){resolve(response);
            document.getElementById("locations").innerHTML = "Locations";
        })
        .once('error', function(response){resolve(response); })
            .execute();
    });
}
/* plot Geography of sessions - end */

/* set dates in calendar inputs - start */


/**
 * Create a new canvas inside the specified element. Set it to be the width
 * and height of its container.
 * @param {string} id The id attribute of the element to host the canvas.
 * @return {RenderingContext} The 2D canvas context.
 */
function makeCanvas(id) {
    var container = document.getElementById(id);
    var canvas = document.createElement('canvas');

    var ctx = canvas.getContext('2d');

    container.innerHTML = '';
    canvas.width = container.offsetWidth;
    canvas.height = container.offsetHeight;
    container.appendChild(canvas);

    return ctx;
}



gapi.analytics.ready(function() {
    displayPleaseWaitDiv("");
    $.getJSON("/bsp-monitor/get-access-token/ganalytics/", function(data){
        gapi.analytics.auth.authorize({
            'serverAuth': {
                'access_token': data["access_token_ganalytics"]
            }
        });
        plotRtUsers(IDS, RT_FILTERS);
        plotRtPages(IDS, RT_FILTERS, rt_pages_dim, rt_metrics);
        plotGeo(IDS, FILTERS);
        plotSessionNum(IDS, FILTERS);
        plotUserNum(IDS, FILTERS);
        plotUserCum(IDS, FILTERS);//
        plotPagesView(IDS, FILTERS); //
        plotRtUsecases();
        plotHistoryUsecases();

        setInterval(function(){
            plotRtUsers(IDS, RT_FILTERS);
            plotRtPages(IDS, RT_FILTERS, rt_pages_dim, rt_metrics);
            plotRtUsecases();
        }, REFRESH_TIME);
    }).then(closePleaseWaitDiv())
})
//
// Display please wait div
function displayPleaseWaitDiv(message="") {
    document.getElementById("overlaywrapperwaitmon").style.display = "block";
    document.getElementById("mainDiv").style.pointerEvents = "none";
    document.body.style.overflow = "hidden";
    if (message || !(message.length === 0)){
        document.getElementById("waitdynamictextmon").innerHTML = message;
    }
}

// Hide please wait message div
function closePleaseWaitDiv() {
    document.getElementById("overlaywrapperwaitmon").style.display = "none";
    document.getElementById("mainDiv").style.pointerEvents = "auto";
    document.body.style.overflow = "auto";
}
















////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////
////////////////////////////////////////////////

function selectColor(colorNum, colors){
    if (colors < 1) colors = 1; // defaults to one color - avoid divide by zero
    return "hsl(" + (colorNum * (360 / colors) % 360) + ",100%,50%)";
}



function plotHistoryUsecasesReview(){
    var dates = getDates();
    $.getJSON('/bsp-monitor/get-uc/' + dates[0] + '/' + dates[1] + '/', function (resp){
        console.log(resp);
        var data = {};
        if (resp["rt_uc_num"] == 0){
            data = {
                datasets:[{data:[1], 
                    backgroundColor: palette('tol', 1).map(function(hex) {
                        return '#' + hex;
                    })

                }],
                labels:["No use case executed"]
            } 
        }
        else {
            data = {
                datasets:[{data:resp["uc_topics_count"],
                    backgroundColor: palette('tol', resp["uc_topics_count"].length).map(function(hex) {
                        return '#' + hex;
                    })
                }],
                labels:resp["uc_topics"]
            } 
        }
        var ctx = makeCanvas('chart-rt-uc-container-review');
        var chart = new Chart(ctx, {
            type: 'doughnut',
            // The data for our dataset
            data: data,
            options: {
                legend:{
                    position: 'top',
                    labels:{
                        boxWidth: 10,
                    }
                }
            },
        });
    });
}


/* get real time pages- start */
function plotHistPagesReview(IDS, FILTERS){
    var dates = getDates();
    query({
        'ids': IDS,
        'filters': FILTERS,
        'dimensions': 'ga:pagePath, ga:pageTitle, ga:date',
        'metrics': 'ga:pageviews',
        'sort': 'ga:pagePath',
        'start-date': dates[0],
        'end-date': dates[1],
        'max-results': 10000
    })
    .then(function(t) {
        if (!("rows" in t)){
            data = {
                datasets:[{data:[1]}],
                labels:["No visit"]
            }
        }else{
            var pages = {};
            var labels = {};
            var data = {};
            var counter_access = 0;
            var counter_no_nav = 0;
            var counter_no_dash = 0;
            var counter_all_pages = 0;
            t['rows'].forEach(function(row, i) {
                // if the bsp root has been accessed (i.e. no item visited)
                if (row[0].indexOf("nav") == -1){
                    counter_no_nav = counter_no_nav + 1;
                    return
                }else if (row[1].indexOf("-") == -1){
                    counter_no_dash = counter_no_dash + 1;
                    return
                }else{
                    crr_label = row[1].substr(0, row[1].indexOf('-')-1);
                    pages[crr_label] = pages[crr_label] ? pages[crr_label]+(+row[3]) : +row[3];
                    labels[crr_label] = crr_label;
                    counter_all_pages = counter_all_pages + (+row[3])
                }
            });

            if (Object.getOwnPropertyNames(pages).length == 0){
                data = {
                    datasets:[{data:[1],
                        backgroundColor: palette('tol', 1).map(function(hex) {
                            return '#' + hex;
                        })
                    }],
                    labels:["No visit"]
                }
            } else {
                var data_all = [];
                var labels_str = [];
                var tooltips = [];
                Object.keys(labels).forEach(function(key, index) {
                    data_all.push(pages[key]);
                    labels_str.push(labels[key]);
                    tooltips.push(labels[key]);
                });  
                var bg = [];
                for (var i=0; i < data_all.length; i++){
                    bg.push(selectColor(i, data_all.length)); 
                }
                data = { 
                    labels:tooltips,
                    datasets:[{
                        data:data_all,
                        backgroundColor: bg
                    }]
                };
            }
        }
        var ctx = makeCanvas('chart-rt-pages-container-review');
        var chart = new Chart(ctx, {
            type: 'doughnut',
            // The data for our dataset
            data: data,
            options: {
                legend:{
                    position: 'top',
                    labels:{
                        boxWidth: 10,
                    },
                }
            },
        });
    });
}

/* get real time pages- start */
function plotHistUCReview(IDS, FILTERS){
    $.getJSON('/bsp-monitor/get-all-no-alex/',function(t) {
        console.log(t);
        var bg = [];
        for (var i=0; i < t["uc_topics_count"].length; i++){
            bg.push(selectColor(i, t["uc_topics_count"].length)); 
        }
        data = { 
            labels:t["uc_topics"],
            datasets:[{
                data:t["uc_topics_count"],
                backgroundColor: bg
            }]
        };
        var ctx = makeCanvas('chart-rt-uc-container-review');
        var chart = new Chart(ctx, {
            type: 'doughnut',
            // The data for our dataset
            data: data,
            options: {
                legend:{
                    position: 'top',
                    labels:{
                        boxWidth: 10,
                    },
                }
            },
        });
    });
}

/* get real time pages- start */
function plotHistUCExecReview(IDS, FILTERS){
    $.getJSON('/bsp-monitor/get-exec-member/',function(t) {
        console.log(t);
        data = { 
            labels:t["dates"],
            datasets:[{
                data:t["count"],
                pointRadius : 0,
                pointHoverRadius : 3,
                label: "",
                backgroundColor:'rgba(30, 70, 240, 0.4)',
            }]
        };
        var ctx = makeCanvas('exec-member-container-review');
        var chart = new Chart(ctx, {
            type: 'line',
            // The data for our dataset
            data: data,
            options: {
                legend:{
                    position: 'top',
                    labels:{
                        boxWidth: 10,
                    },
                }
            },
        });
    });
}
