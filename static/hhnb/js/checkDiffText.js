onmessage = function(e) {
    console.log("starting checkTextareaValue worker");
    const currentValue = e.data[0];
    const storedValue = e.data[1];
    
    if (currentValue != storedValue) {
        postMessage("different");
    } else {
        postMessage("equals");
    }
}