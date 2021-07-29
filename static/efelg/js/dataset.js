$(document).ready(() =>  {
    $.getJSON('/efelg/get_dataset/', dataset => {
        console.log(dataset)
        var container = $("#table-container");
        var contributorCounter = 1;
        Object.keys(dataset).forEach(contributor => {
            var rowCounter = 1;
            container.append("<h5><strong style='font-size: 1.3rem; color: #555'>" + contributor + "</strong></h5>")
            container.append(' \
                <table class="table table-striped table-sm table-sm-text table-hover center-first-column"> \
                    <thead> \
                        <tr> \
                            <th style="width: 5%" scope="col">#</th> \
                            <th style="width: 27%" scope="col">File name</th> \
                            <th style="width: 11%" scope="col">Download URL</th> \
                            <th style="width: 57%" scope="col">Location</th> \
                        </tr> \
                    </thead> \
                    <tbody id="contributor-' + contributorCounter + '"> \
                    </tbody> \
                </table>'
            );
            var body = $("#contributor-" + contributorCounter);
            Object.keys(dataset[contributor]).forEach(name => {
                body.append( ' \
                    <tr id="contributor-' + contributorCounter + '_' + rowCounter + '"> \
                        <th scope="row">' + rowCounter + '</th> \
                        <td>' + name + '</td> \
                    </tr>');
                var row = $("#contributor-" + contributorCounter + "_" + rowCounter);
                if ("url" in dataset[contributor][name]) {
                    row.append('<td> \
                            <a target="_blank" href="' + dataset[contributor][name]["url"] + '">link</a> \
                        </td>'
                    );
                    if ("note" in dataset[contributor][name]) {
                        row.append('<td>' + dataset[contributor][name]["note"] + '</td>');
                    } else {
                        row.append('<td></td>');
                    }
                } else {
                    row.append('<td>N/A</td>');
                    row.append('<td><em>Avalible soon</em></td>')
                }
                rowCounter +=1
            });
            container.append("<br><hr><br>");
            contributorCounter += 1;
        })
    });
});