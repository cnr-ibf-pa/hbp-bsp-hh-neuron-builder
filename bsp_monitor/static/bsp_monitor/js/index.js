function query_ga()
    var dataChart = new gapi.analytics.googleCharts.DataChart({
        query: {
            ids: 'ga:101800494',
            metrics: 'ga:users,ga:sessions',
            dimensions: 'ga:date',
            'start-date': '30daysAgo',
            'end-date': 'yesterday',
            filters:'ga:pagePath=~/collab/1655(\/.*|$)'
        }
               return dataChart;
    });
