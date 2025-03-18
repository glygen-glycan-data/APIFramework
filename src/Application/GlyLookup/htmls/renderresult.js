


function renderResultMore(){
    show("result_container");

    let result = retrieve_result.result;
    let error = retrieve_result.error;
    let stat = retrieve_result.stat;

    let result_container_status = document.getElementById("result_container_status");
    let result_container_additional = document.getElementById("result_container_additional");


    if (result.length > 0){
        result_container_status.innerHTML += "<p style='font-size: 25px;'>Found "+result.length+" structure(s)</p>";
    }
    else {
        if (error.length == 0) {
            result_container_status.innerHTML += "<p style='font-size: 25px;'>No structure found</p>";
        } else {
            let tmp = error.join(", ");
            result_container_status.innerHTML += "<p style='font-size: 25px; color: red; '>Error: "+tmp+"</p>";
        }
    }

    if (result.length > 0) {
        let glytoucanurl = "https://glytoucan.org/Structures/Glycans/"+result[0].accession
        result_container_additional.innerHTML += "<br><a href='"+glytoucanurl+"'><img id='inputseqimg'></a>"
        result_container_additional.innerHTML += "<br><a href='"+glytoucanurl+"'>"+result[0].accession+"</a>";
        glymage.setPrecomputedImageURL('inputseqimg',{'acc': result[0].accession, 'image_format': 'svg'})
    } else {
        result_container_additional.innerHTML += "<br><img id='inputseqimg'>";
        glymage.setOnDemandImageURL('inputseqimg',{'seq': retrieve_result.task.seq, 'image_format': 'svg'})
    }

}
