


function renderResultMore(){
    show("result_container");

    let result = retrieve_result.result;
    let error = retrieve_result.error;
    let stat = retrieve_result.stat;

    let result_container_status = document.getElementById("result_container_status");
    let result_container_additional = document.getElementById("result_container_additional");


    if (result.length > 0){
        result_container_status.innerHTML += "<p style='font-size: 25px;'>Convert successfully</p>";
    }
    else {
        result_container_status.innerHTML += "<p style='font-size: 25px;'>Convert unsuccessfully</p>";
    }


    if (error.length > 0){
        let tmp = error.join(", ");
        result_container_status.innerHTML += "<p style='font-size: 25px; color: red; '>Error: "+tmp+"</p>";
    }

    result_container_additional.innerHTML += "<br><img id='inputseqimg'>";
    glymage.setOnDemandImageURL('#inputseqimg',{'seq': retrieve_result.task.seq, 'image_format': 'svg'});

    result_container_additional.innerHTML += "<br><div style='text-align: center;'><div style='display: inline-block; text-align: left;'>"+retrieve_result.result.replaceAll("\n", "<br>")+"</div></div>"

    if (result.length == 0){
        return
    }



}
