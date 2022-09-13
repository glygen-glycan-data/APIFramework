


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

    let imgurl = "https://glymage.glyomics.org/";
    let s = retrieve_result.task.seq;
    if (error.length == 0 && result.length == 0 && (s.startsWith("WURCS") || s.startsWith("RES"))) {
        if ( !s.startsWith("WURCS") ){
            s = encodeURIComponent(s);
        }
        imgurl += "getimage?" + "notation=snfg&display=extended&format=png&seq=" + s;
        result_container_additional.innerHTML += "<br><img src='"+imgurl+"'>";
    } else if (result.length > 0) {
        imgurl += "image/snfg/extended/"+ result[0].accession +".png";
        result_container_additional.innerHTML += "<br><img src='"+imgurl+"'>";
    }

    if (result.length > 0) {
        result_container_additional.innerHTML += "<br><a href='https://glytoucan.org/Structures/Glycans/"+result[0].accession+"'>"+result[0].accession+"</a>";
    }


}
