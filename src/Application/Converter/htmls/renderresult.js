


function renderResultMore(){
    show("result_container");

    let result = retrieve_result.result;
    let task = retrieve_result.task;
    let error = retrieve_result.error;
    let stat = retrieve_result.stat;

    let result_container_status = document.getElementById("result_container_status");
    let result_container_additional = document.getElementById("result_container_additional");


    if (error.length > 0){
        let tmp = error.join(", ");
        result_container_status.innerHTML += "<p style='font-size: 25px; color: red; '>Error: "+tmp+"</p>";
    } else {
        if (task.format == "composition") {
            result_container_additional.innerHTML += "<br><img id='inputseqimg'>";
            glymage.setOnDemandImageURL('#inputseqimg',{'seq': result, 'image_format': 'svg'});
        } else {
            result_container_additional.innerHTML += "<br><img id='inputseqimg'>";
            glymage.setOnDemandImageURL('#inputseqimg',{'seq': task.seq, 'image_format': 'svg'});
        }
        result_container_additional.innerHTML += "<br><div style='text-align: center;'><div style='display: inline-block; text-align: left;'><tt>"+retrieve_result.result.replaceAll("\n", "<br>")+"</tt></div></div>"

    }


}
