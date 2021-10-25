const exc = sessionStorage.getItem("exc");

document.ready(() => {
    window.location.href = "/hh-neuron-builder/workflow/" + exc;
})