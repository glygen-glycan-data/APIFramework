


function renderResultMore(){
    show("result_container");

    let result = retrieve_result.result;
    let error = retrieve_result.error;
    let stat = retrieve_result.stat;

    let result_container_status = document.getElementById("result_container_status");
    let result_container_additional = document.getElementById("result_container_additional");

    if (error.length > 0){
        let tmp = error.join(", ");
        result_container_status.innerHTML += "<p style='font-size: 25px; color: red; '>Error: "+tmp+"</p>";
    }

    result_container_additional.innerHTML +=  "" +
        "View result in On-Demand alignment tool at " +
        "<a href='https://gnome.glyomics.org/StructureBrowser.html?ondemandtaskid="+retrieve_result.id+"'>Structure Browser</a> and " +
        "<a href='https://gnome.glyomics.org/CompositionBrowser.html?ondemandtaskid="+retrieve_result.id+"'>Composition Browser</a>" +
        "<br>";


}
