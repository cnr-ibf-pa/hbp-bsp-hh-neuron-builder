/* 
 * RESTapi function to handle workflows 
 */

function requestsWorkflow(url, method, headers, success, error) {
    let response;

    if (!success) {
        success = (result) => { response = result };
    }
    if (!error) {
        error = (error) => { response = error };
    }
    $.ajax({
        url: url,
        method: method,
        headers: headers,
        success: success,
        error: error 
    });
}

function getWorkflow(url, headers=null, success=null, error=null) {
    let resp = requestsWorkflow(url, "GET", headers);
    console.log(resp);
}

function postWorkflow(url, headers=null, success=null, error=null) {
    return requestsWorkflow(url, "POST", headers)
} 

function newWorkflow(exc) {
    return getWorkflow("initialize-workflow/" + exc.toString());
}

function cloneWorkflow(exc) {
    return requestsWorkflow("clone-workflow/" + exc.toString());
}

function uploadWorkflow(zipName, zipFile) {
    /* return postWorkflow(
        url="upload-workflow",
        headers={
            "Content-Type": ""
        },
    ) */
}


export { newWorkflow, cloneWorkflow, uploadWorkflow };