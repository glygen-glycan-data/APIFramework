


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

    let status = retrieve_result.result.status;
    if (status == "Registered") {
      let acc = retrieve_result.result.accession;
      let gtcurl = "https://glytoucan.org/Structures/Glycans/" + acc;
      result_container_additional.innerHTML += "<br><A href='" + gtcurl + "'><img id='inputseqimg'></A>";
      result_container_additional.innerHTML += "<br>Status: " + status;
      result_container_additional.innerHTML += "<br>Accession: <A href='" + gtcurl + "'>" + acc + "</A>";
      glymage.setPrecomputedImageURL('inputseqimg',{"acc": acc, "image_format": "svg"});
    } else {
      let seq = retrieve_result.result.submitted_sequence;
      result_container_additional.innerHTML += "<br><img id='inputseqimg'>";
      result_container_additional.innerHTML += "<br>"+"Status: "+ status;
      glymage.setOnDemandImageURL('inputseqimg',{"seq": seq, "image_format": "svg"});
    }
    result_container_additional.innerHTML += "<p></p>";

}
