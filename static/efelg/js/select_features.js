$(document).ready(function() {
    window.scrollTo(0, 0);
});

function submitForm() {
    var $featForm = $('#select_feature_form');
    $featForm.submit(function(e) {
        var all_checkboxes =
            document.getElementsByName("crr_feature_check_features");
        var counter = 0;
        for (var cbi = 0; cbi < all_checkboxes.length; cbi++) {
            if (all_checkboxes[cbi].checked) {
                counter += 1;
                break;
            }
        }
        if (counter > 0) {
            document.getElementById("select_feature_form").submit();
        } else {
            openMessageDiv("warning-div", "main-sf-div");
        }
        e.preventDefault();
    });
}

$.getJSON('/efelg/features_dict', function(data) {
    orderedOuterKeys = Object.keys(data).sort(function(a, b) {
        return a.toLowerCase().localeCompare(b.toLowerCase());
    })
    $.each(orderedOuterKeys, function(idx) {
        var i = orderedOuterKeys[idx];
        var ob = data[i];
        var crrid = i.split(' ').join('_');
        var innerDivId = crrid + "_inner";
        var crrSelectButtonId = crrid + "_button";
        var crrSelectClearButtonId = crrid + "_clear_button";
        var crrSelectInvButtonId = crrid + "_inv_button";
        var crrContainerDiv = $("<div>");
        var crrHeadingDiv = $("<div>");
        var crrElemDiv = $("<div>");
        var crrElemDivButton = $("<input>");
        var crrElemDivClearButton = $("<input>");
        var crrElemDivInvButton = $("<input>");

        crrContainerDiv.attr("id", crrid);
        crrContainerDiv.addClass("my-3");
        crrHeadingDiv.attr("name", crrid);
        crrHeadingDiv.on("click", function() {
            $(this).siblings("div").slideToggle("slow", function() {});
        });

        crrElemDiv.attr("id", innerDivId);
        crrElemDiv.addClass("mb-5")
        crrElemDivButton.attr("id", crrSelectButtonId);
        crrElemDivButton.attr("type", "button");
        crrElemDivButton.attr("value", "Select all");
        crrElemDivButton.addClass("btn btn-link");
        crrElemDivButton.on("click", function() {
            $(this).parent().children().children().prop("checked", true);
        });

        crrElemDivClearButton.attr("id", crrSelectClearButtonId);
        crrElemDivClearButton.attr("type", "button");
        crrElemDivClearButton.attr("value", "Clear all");
        crrElemDivClearButton.addClass("btn btn-link");
        crrElemDivClearButton.on("click", function() {
            $(this).parent().children().children().prop("checked", false);
        });

        crrElemDivInvButton.attr("id", crrSelectInvButtonId);
        crrElemDivInvButton.attr("type", "button");
        crrElemDivInvButton.attr("value", "Invert selection");
        crrElemDivInvButton.addClass("btn btn-link");
        crrElemDivInvButton.on("click", function() {
            $(this).parent().children().children().each(function() {
                $(this).prop('checked', !$(this).prop('checked'))
            })
        });
        $("#mainDiv").append(crrContainerDiv);
        $('#' + crrid).append(crrHeadingDiv);
        //$("div[name=" + crrid + "]").append("<button" + $("div[name=" + crrid + "]") + " class='btn btn-lg btn-outline-primary w-100 my-3 bg-light-orange'>" + i + "</button>");
        $("div[name=" + crrid + "]").append("<div class='btn btn-lg btn-primary border-primary w-100 my-3'>" + i + "</div>");

        $('#' + crrid).append(crrElemDiv);

        $('#' + innerDivId).append(crrElemDivButton);
        $('#' + innerDivId).append(crrElemDivClearButton);
        $('#' + innerDivId).append(crrElemDivInvButton).append("<br>");
        $('#' + innerDivId).toggle();
        
        orderedInnerKeys = Object.keys(
                Object.fromEntries(Object.entries(ob).filter(([key, value]) => value != ""))
            )
            .sort(function(a, b) {
                return a.toLowerCase().localeCompare(b.toLowerCase());
            }
        );

        $.each(orderedInnerKeys, function(inneridx) {

            var ind = orderedInnerKeys[inneridx];
            var obj = ob[ind];

            var crrElemLabelId = ind + "label";
            var crrElemLabel = $("<label>");
            var crrInputElem = $("<input>");
            var crrSpanElem = $("<span>");

            crrElemLabel.addClass("label-check");
            crrElemLabel.attr("id", crrElemLabelId);

            crrInputElem.attr("id", ind);
            crrInputElem.attr("type", "checkbox");
            crrInputElem.attr("name", "crr_feature_check_features");
            crrInputElem.attr("value", ind);

            crrSpanElem.attr("title", obj)
            crrSpanElem.addClass("span-check");
            crrSpanElem.append(ind);

            $('#' + innerDivId).append(crrElemLabel);
            $('#' + crrElemLabelId).append(crrInputElem);
            $('#' + crrElemLabelId).append(crrSpanElem);

            if (inneridx < orderedInnerKeys.length - 1) {
                $('#' + crrElemLabelId).append(" - ");
            }
        });
    });
});