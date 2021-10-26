const exc = sessionStorage.getItem("exc");
const req_pattern = exc;

$("#show-opt-files-btn").on("click", openFileManager);


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function openFileManager(showConfig=false) {
    refreshHHFFileList();
    console.log("openFileManager() called with showConfi=" + showConfig.toString())
    if (showConfig) {
        showFileList($("#configFolder"));
    }

    console.log("fetchHHFFileList() on openFileManager()");
    $("#overlaywrapper").css("display", "block");
    $("#overlayfilemanager").css("display", "block");
    $("#overlayfilemanager").addClass("open");
    $.ajax({
        url: "/hh-neuron-builder/hhf-get-model-key/" + req_pattern,
        method: "GET",
        success: function(response) {
            console.log(response);
            $("#modelKeyInput").val(response.model_key);
        }
    });
}
/* 
function fetchHHFFileList() {
    const folderList = $("#folderselector > .folder-group");
    const fileList = $("#fileselector");
    $.getJSON("/hh-neuron-builder/hhf-list-files/" + exc, (file_list) => {
        folderList.empty();
        fileList.empty();
        $.each(file_list, (dir) => {
            let elementName = dir[0].toUpperCase() + dir.substring(1); // Upper first char
            if (dir != "root") {
                folderList.append("<li id='" + dir + "Folder" + "' class='list-group-item filder-item'>" + elementName + "</li>");
                fileList.append("<ul id='" + dir + "FileList" + "' class='list-group file-manager-group file-group' style='display:none'></ul");
            } else {
                for (let file of file_list[dir]) {
                    console.log(file);
                    let id = file.split(".")[0];
                    let lang = file.split(".")[1] == "py" ? "python" : "unknown";                
                    folderList.append("<div id='" + id +"' class='file-code' style='display:none'><pre><code id='" + id + "Code" + "' class='" + lang + "'></code></pre></div>");
                    // folderList.append("<div id='" + dir.split(".")[0] ")
                }
            }
            $("#" + dir + "FileList").addClass("empty-list");
            for (let file of file_list[dir]) {
            }
        })
    })
} */


function fetchHHFFileList() {
    $.getJSON("/hh-neuron-builder/hhf-list-files/" + exc, function(data) {
        
        if (data.morphology && data.morphology.length > 0) {
            for (let i = 0; i < data.morphology.length; i++) {
                let name = data.morphology[i]
                $("#morphologyFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>");
                $("#morphologyFileList").removeClass("empty-list");
            }
        } else {
            console.log("append Empty on morpFileList");
            $("#morphologyFileList").addClass("empty-list");
            $("#morphologyFileList").append("<div class='file-item empty'>Empty</div>");
        }

        if (data.mechanisms && data.mechanisms.length > 0) {
            for (let i = 0; i < data.mechanisms.length; i++) {
                let name = data.mechanisms[i]
                $("#mechanismsFileList").append("<li id='" + name + "' class='list-group-item file-item' onclick='selectFileItem(this)'>" + name + "</li>");
                $("#mechanismsFileList").removeClass("empty-list");
            }
        } else {
            console.log("append Empty on modFileList");
            $("#mechanismsFileList").append("<div class='file-item empty'>Empty</div>");
            $("#mechanismsFileList").addClass("empty-list");
        }
        
        if (data.config && data.config.length > 0) {
            for (let i = 0; i < data.config.length; i++) {
                let name = data.config[i];
                $("#configFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>");
                $("#configFileList").removeClass("empty-list");
            }
        } else {
            $("#configFileList").append("<div class='file-item empty'>Empty</div>");
            $("#configFileList").addClass("empty-list");
        }

        if (data.model && data.model.length > 0) {
            for (let i = 0; i < data.model.length; i++) {
                let name = data.model[i];
                $("#modelFileList").append("<li id='" + name + "' class='list-group-item file-item'  onclick='selectFileItem(this)'>" + name + "</li>")
                $("#modelFileList").removeClass("empty-list");
            }
        } else {
            $("#modelFileList").append("<div class='file-item empty'>Empty</div>");
            $("#modelFileList").addClass("empty-list");
        }

        if (data["opt_neuron.py"]) {
            $("#optNeuronCode").html(data["opt_neuron.py"]);
        }
        hljs.highlightAll();
   
        $("#fileItemSpinner").css("display", "none");
        showFileList($(".folder-item.active"));
    });
}


function refreshHHFFileList() {
    $(".file-group").css("display", "none");
    $(".file-group").empty();
    // $(".file-textarea").css("display", "none");
    $(".file-code").css("display", "none");
    $("code").html();
    $("#fileItemSpinner").css("display", "flex");
    fetchHHFFileList();
    console.log("fetchHHFFileList() on refreshHHFFileList()");
}


function closeFileManager() {
    $("#overlaywrapper").css("display", "none");
    $("#overlayfilemanager").css("display", "none");

    $(".file-item").removeClass("active");
    $(".file-group").empty();
    $("code").html();

    resetEditorMode();

    setModelKey(onClose=true);
};


$("#deleteFileButton").click(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    if ($(".file-item.active").length == 0 && $("editor-item.active").length == 0) {
        return false;
    }

    if ($(".file-item.active").length > 1) {
        $("#confirmationDialogModalTitle").html("Are you sure to delete these files ?");
    } else {
        $("#confirmationDialogModalTitle").html("Are you sure to delete this file ?");
    }
    $("#confirmationDialogModalCancelButton").html("Cancel");
    $("#confirmationDialogModalOkButton").html("Yes").attr("onclick", "deleteHHFFiles()");
    $("#confirmationDialogModal").modal("show");
});


function deleteHHFFiles() {

    if ($(".folder-item.active").attr("id") == "morphologyFolder") {
        if ($("#morphologyFileList").hasClass("empty-list")) {
            $("#uploadFileButton").removeClass("disabled");
        }
    }
    
    var data = {"file_list": []};
    var directory = $(".folder-item.active").attr("id").split("Folder")[0];

    console.log(directory);

    if (editorMode) {
        if ($(".editor-item.active").length == 0) {
            return false;
        }
        data.file_list.push(directory + "/" + $(".editor-item.active").attr("name"));
    } else {
        if ($(".file-item.active").length == 0) {
            return false;
        }
        $(".file-item.active").each(function(i) {
            data.file_list.push(directory + "/" + $(this).attr("id"));
        });
    }

    if (directory == "morphology") {
        data.file_list.push("config/morph.json");
    }

    console.log(data);

    $.ajax({
        url: "/hh-neuron-builder/delete-files/" + exc,
        method: "POST",           
        dataType: "json",
        contentType: "application/json",
        data: JSON.stringify(data),
        error: (error) => { 
            console.error("Status: " + error.status + " > " + error.responseText); 
            // MessageDialog.openErrorDialog(error.responseText);
        },
    }).always(() => { 
        hideLoadingAnimation();
        refreshHHFFileList()
    });
}


$("#downloadFileButton").click(function() {

    var jj_ids = {'path': []};

    if (!editorMode) {
        if ($(".folder-item.active").attr("id") == "optNeuronFolder") {
            jj_ids.path.push("opt_neuron.py");
            showLoadingAnimation("Downloading files...");
            $.get("/hh-neuron-builder/download-files/" + req_pattern + "?file_list=" + encodeURIComponent(JSON.stringify(jj_ids)))
            .done(() => { window.location.href = "/hh-neuron-builder/download-files/" + req_pattern + "?file_list=" + encodeURIComponent(JSON.stringify(jj_ids)) })
            .always(() => { hideLoadingAnimation() })
        } 
        if ($(".file-item.active").length == 0) {
            return false;
        } else {
            $(".file-item.active").each(function(i) {
                console.log($(".folder-item.active"));
                jj_ids.path.push($(".folder-item.active").attr("id").split("Folder")[0] + "/" + $(this).attr("id"));

            });
        }
    } else {
        if ($(".editor-item.active").length == 0) {
            return false;
        }
        jj_ids.path.push($(".editor-item.active").attr("name"));
    }

    showLoadingAnimation("Downloading files...");

    $.get("/hh-neuron-builder/download-files/" + req_pattern + "?file_list=" + encodeURIComponent(JSON.stringify(jj_ids)))
        .done(() => { window.location.href = "/hh-neuron-builder/download-files/" + req_pattern + "?file_list=" + encodeURIComponent(JSON.stringify(jj_ids)) })
        .always(() => { hideLoadingAnimation() })
});


$("#uploadFileButton").click(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    
    const input = document.createElement("input");
    if ($(".folder-item.active").attr("id") == "mechanismsFolder") {
        input.setAttribute("multiple", "true");
    }
    input.setAttribute("multiple", "true");
    input.setAttribute("type", "file");
    input.click();
    
    var counter = 0;
    var files = 0

    var filePath = $(".folder-item.active").attr("id").split("Folder")[0] + "/";
    console.log(filePath);

    const upload = (file) => {
        
        fetch("/hh-neuron-builder/upload-files/" + req_pattern, {
            method: "POST",
            headers: {
                "Content-Type": "application/octet-stream",
                "Content-Disposition": "attachment; filename=\"" + filePath + file.name + "\""
            },
            body: file
        })
        .then((result) => {
            console.log(result);
            if (result.statusText == "OK") {
                counter += 1;
                if (counter == files) {
                    hideLoadingAnimation();
                    refreshHHFFileList();
                    updateEditor();
                }
            } else {
                closeFileManager();
                openErrorDiv(result.message, "error");
            }
        });
    }

    const onSelectFile = async function(x) {        
        files = input.files.length;
        $(".file-group").css("display", "none");
        $("#fileItemSpinner").css("display", "flex");
        showLoadingAnimation('Uploading files...');
        for (let i = 0; i < input.files.length; i++) {
            upload(input.files[i]);
        }
        input.files = null;
    }
    input.addEventListener('change', onSelectFile, false);
});


$("#selectAllButton").click(function() {
    if ($(this).hasClass("active")) {
        $(this).removeClass("active");
        $(".file-item").removeClass("active");
    } else {
        $(this).addClass("active");
        $(".file-group.active").children().addClass("active");
    }
})


$(".folder-item").click(function() {
    showFileList($(this));
})


function showFileList(folder) {
    var currFolder = folder.attr("id");
    var currList = null;

    $("#selectAllButton").removeClass("active");
    $(".file-item").removeClass("active");
    $(".folder-item").removeClass("active").attr("aria-current", false);
    $(".file-group").css("display", "none").removeClass("active");
    $(".file-code").css("display", "none");
    $(".ui-button").removeClass("disabled");
    
    hideFloatingOpenFileButton();


    folder.addClass("active").attr("aria-current", true);

    if (currFolder == "morphologyFolder") {
        currList = $("#morphologyFileList"); 
        if (!currList.hasClass("empty-list")) {
            $("#uploadFileButton").addClass("disabled");
        }
    } else if (currFolder == "mechanismsFolder") {
        currList = $("#mechanismsFileList");
    } else if (currFolder == "configFolder") {
        currList = $("#configFileList"); 
        showFloatingOpenFileButton();
    } else if (currFolder == "modelFolder") {
        currList = $("#modelFileList"); 
        $("#uploadFileButton").addClass("disabled");
        $("#deleteFileButton").addClass("disabled");
        showFloatingOpenFileButton();
    } else if (currFolder == "optNeuronFolder") {
        currList = $("#optNeuronTextArea"); 
        $("#deleteFileButton").addClass("disabled");
        $("#selectAllButton").addClass("disabled");
        $("#uploadFileButton").addClass("disabled");
    }
    currList.css("display", "block");
    currList.addClass("active");
    if (currList.hasClass("empty-list")) {
        $("#downloadFileButton").addClass("disabled");
        $("#selectAllButton").addClass("disabled");
        $("#deleteFileButton").addClass("disabled"); 
    }
}


function selectFileItem(item) {
    $(item).toggleClass("active");
}


$("#refreshFileListButton").click(function() {
    refreshHHFFileList();
    updateEditor();
})


let alpha = []
$("#modelKeyInput").on("input", function(){
    let k = $("#modelKeyInput").val()[0];
    if (k in [""]){
    }
})


function setModelKey(onClose=false) {
    var k = $("#modelKeyInput").val();
    $.post("/hh-neuron-builder/hhf-apply-model-key/" + req_pattern, {"model_key": k.toString()})
        .done(() => { refreshHHFFileList() });
}


$("#infoFileManagerButton").click(function() {
    $("#modalHHF").modal("show");
});


function showFloatingOpenFileButton() {
    $("#editFileButton").addClass("show");
}

function hideFloatingOpenFileButton() {
    $("#editFileButton").removeClass("show");
    $("#saveFileButton").removeClass("show");
}

var editorMode = false;



$("#editFileButton").mousedown(function() {
    $(this).addClass("clicked")
})

$("#editFileButton").mouseup(function() {
    $(this).removeClass("clicked")
    if (editorMode && $("#saveFileButton").hasClass("show")) {
        $("#confirmationDialogModalTitle").html("Discards changes ?");
        $("#confirmationDialogModalCancelButton").html("No");
        $("#confirmationDialogModalOkButton").html("Yes").attr("onclick", "discardTextAreaChanges(true)");
        $("#confirmationDialogModal").modal("show");
    } else {
        switchMode();
    }
});

$("#editFileButton").mouseout(function() {
    $(this).removeClass("clicked")
})


function resetEditorMode() {
    editorMode = false;
    $("#folderselector").css("display", "block").removeClass("fade-out fade-in");
    $("#editorselector").css("display", "none").removeClass("fade-out fade-in");
    $("#fileselector").css("display", "block").removeClass("fade-out fade-in");
    $("#fileeditor").css("display", "none").removeClass("fade-out fade-in");
    $("#editFileButtonImage").removeClass("show zoomout").css("top", "8px").css("left", "2px").attr("src", "/static/assets/img/open-file-white.svg");
    $("#editFileButton").attr("title", "Open/Edit files");
    $("#editorfilelist").empty();
    $("#saveFileButton").removeClass("show disabled");
    $("#saveFileButtonSpinner").css("display", "none");
    $("#saveFileButtonImage").css("display", "inline");        
}


function switchMode() {
    let folderSelector = $("#folderselector");
    let editorSelector = $("#editorselector");
    let fileSelector = $("#fileselector");
    let fileEditor = $("#fileeditor")
    let editFileButtonImage = $("#editFileButtonImage");


    editorMode = !editorMode;
    
    folderSelector[0].addEventListener("animationend", function(){
        if (editorMode) {
            folderSelector.css("display", "none");
            editorSelector.css("display", "block");
            editorSelector.removeClass("fade-out").addClass("fade-in");
        }
    })
    editorSelector[0].addEventListener("animationend", function() {
        if (!editorMode) {
            editorSelector.css("display", "none");
            folderSelector.css("display", "block");
            folderSelector.removeClass("fade-out").addClass("fade-in")
        }
    })

    fileSelector[0].addEventListener("animationend", function() {
        if (editorMode) {
            fileSelector.css("display", "none");
            fileEditor.css("display", "block");
            fileEditor.removeClass("fade-out").addClass("fade-in");
        }
    })
    fileEditor[0].addEventListener("animationend", function() {
        if (!editorMode) {
            fileEditor.css("display", "none");
            fileSelector.css("display", "block");
            fileSelector.removeClass("fade-out").addClass("fade-in");
        }
    })
    editFileButtonImage[0].addEventListener("transitionend", function() {
        console.log(navigator.userAgent.toString().match("Chrome"));
        if (editorMode) {
            editFileButtonImage.addClass("back-arrow")
            if (!navigator.userAgent.toString().match("Chrome")) {
                editFileButtonImage.attr("src", "/static/assets/img/back-arrow-white.svg");
            } 
            $("#editFileButton").attr("title", "Go back");
        } else {
            editFileButtonImage.removeClass("back-arrow");
            if (!navigator.userAgent.toString().match("Chrome")) {
                editFileButtonImage.attr("src", "/static/assets/img/open-file-white.svg");
            }
            $("#editFileButton").attr("title", "Open/Edit files");
        }
        editFileButtonImage.removeClass("zoomout");
    })
    
    editFileButtonImage.addClass("zoomout");
    if (editorMode) {
        loadEditor();
        folderSelector.removeClass("fade-in").addClass("fade-out");
        fileSelector.removeClass("fade-in").addClass("fade-out");
        $("#selectAllButton").addClass("disabled");
    } else {
        editorSelector.removeClass("fade-in").addClass("fade-out");
        fileEditor.removeClass("fade-in").addClass("fade-out");
        $("#saveFileButton").removeClass("show");
        $("#selectAllButton").removeClass("disabled");
    }

};


function loadEditor() {
    $("#editorfilelist").empty();
    $(".file-group.active").children().each(function(i, el){
        if (el.className == "file-item empty") {
            return;
        };
        $("#editorfilelist").append("<li name='" + el.id + "' class='list-group-item folder-item editor-item'  onclick='selectFileEditor($(this).attr(\"name\"))'>" + el.id + "</li>")
        $(".editor-item[name='" + $(".file-item.active").attr("id")).addClass("active");
    });


    $("#fileeditor").empty();

    $("#fileeditor").append("<div id='openafilediv' class='file-item empty' style='display:none'>Open a file</div>");
    $("#fileeditor").append("<div id='editor-spinner' class='spinner-border file-item-spinner' style='display:block' role='status'></div>")

    var currFolder = $(".folder-item.active").attr("id");
    var currFile = $(".file-item.active").attr("id");

    $.getJSON("/hh-neuron-builder/hhf-get-files-content/" + currFolder + "/" + exc, function(jj) {
        
        let files = Object.keys(jj);

        for (let i = 0; i < files.length; i++) {
            console.log(files[i]);
            if (currFolder == "modelFolder") {
                $("#fileeditor").append("<div name='" + files[i] + "' class='file-code' style='display:none'><pre><code name='" + files[i] + "' class='editor python'></code></pre></div>");
                $(".editor.python[name='" + files[i] + "']").html(jj[files[i]]);
                if (currFile) {
                    // enable current file
                    $("#editor-spinner").css("display", "none");
                    $(".file-code[name='" + currFile + "']").css("display", "block").addClass("active");
                }
            } else if(currFolder == "configFolder") {
                $("#fileeditor").append("<textarea name='" + files[i] + "' class='file-textarea' style='display:none'></textarea>");
                $(".file-textarea[name='" + files[i] + "']").val(jj[files[i]]);
                if (currFile) {
                    // enable current file
                    $("#editor-spinner").css("display", "none");
                    $(".file-textarea[name='" + currFile + "']").css("display", "block").addClass("active");
                    originalTextAreaVal = $(".file-textarea.active").val();
                    runCheckDiffWorker();
                }
            }

        } 
        hljs.highlightAll();
 
        if (!currFile) {
            $("#editor-spinner").css("display", "none");
            $("#openafilediv").css("display", "block");

            if ($("#editorfilelist").children().length == 0) {
                $("#openafilediv").text("Upload a file");
            } else {
                $("#openafilediv").text("Open a file");
            }
        }
    });

}


function updateEditor() {
    if (editorMode) {
        loadEditor();
        originalTextAreaVal = null;
    }
}


var originalTextAreaVal = null;


function selectFileEditor(filename) {
    if ($("#editor-spinner").css("display") == "block") {
        return false;
    }

    console.log("selectFileEditor() called for file: " + filename.toString());
    $("#openafilediv").css("display", "none");
    $(".editor-item").removeClass("active");
    $(".editor-item[name='" + filename + "']").addClass("active");
    
    $(".file-code").css("display", "none").removeClass("active");
    $(".file-textarea").css("display", "none").removeClass("active");

    if ($(".folder-item.active").attr("id") == "configFolder") {
        $(".file-textarea[name='" + filename + "']").css("display", "block").addClass("active");
        console.log("set display:block on textarea of " + filename.toString());
        originalTextAreaVal = $(".file-textarea.active").val();
        runCheckDiffWorker();
    } else {
        $(".file-code[name='" + filename + "']").css("display", "block").addClass("active");
    }
}


async function runCheckDiffWorker() {
    if (window.Worker) {
        const checkDiffWorker = new Worker("/static/hhnb/js/utils/checkDiffText.js");

        while(true) {
            checkDiffWorker.postMessage([$(".file-textarea.active").val(), originalTextAreaVal]);
            checkDiffWorker.onmessage = function(e) {
                if (e.data == "equals") {
                    $("#saveFileButton").removeClass("show");
                } else if (e.data == "different") {
                    $("#saveFileButton").addClass("show");
                }
            }
            await sleep(100);
            if (!editorMode) {
                break;
            }
        }

    } else {
        $("#saveFileButton").addClass("show");
    }
}
    

$("#saveFileButton").mousedown(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    $(this).addClass("clicked");
});

$("#saveFileButton").mouseup(function() {
    if ($(this).hasClass("disabled")) {
        return false;
    }
    $(this).removeClass("clicked").addClass("disabled");
    $("#saveFileButtonImage").css("display", "none");
    $("#saveFileButtonSpinner").css("display", "block");
    saveCurrentTextAreaVal();
});

$("#saveFileButton").mouseout(function() {
    $(this).removeClass("clicked");
});


function discardTextAreaChanges(switchmode=false) {
    $(".file-textarea.active").val(originalTextAreaVal);
    if (switchmode) {
        switchMode();
    }
}

function saveCurrentTextAreaVal() {
    var currFile = $(".file-textarea.active").attr("name");
    var currValue = $(".file-textarea.active").val();
    var jj = {};
    jj[currFile] = currValue;
    $.ajax({
        url: "/hh-neuron-builder/hhf-save-config-file/" + currFile + "/" + req_pattern,
        method: "POST",
        data: jj,
        success: function(data) {
            console.log(data);
            originalTextAreaVal = currValue;
            $("#saveFileButton").removeClass("show disabled");
            $("#saveFileButtonSpinner").css("display", "none");
            $("#saveFileButtonImage").css("display", "inline");
            $("#editorAlertText").removeClass("error").addClass("info").html("File saved successfully");
            $("#editorAlert").addClass("show");
        },
        error: function(error) {
            console.error(error);
            $("#saveFileButton").removeClass("disabled");
            $("#saveFileButtonSpinner").css("display", "none");
            $("#saveFileButtonImage").css("display", "inline");
            $("#editorAlertText").removeClass("info").addClass("error").html(JSON.parse(error.responseText).message);
            $("#editorAlert").addClass("show");
        }
    })
}


$("#editorAlert")[0].addEventListener("transitionend", async function(){
    await sleep(2000);
    $(this).removeClass("show");
});
