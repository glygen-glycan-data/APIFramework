


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


    let imgurl = "https://glymage.glyomics.org/getimage?";
    let s = retrieve_result.result.submitted_sequence;
    if ( !s.startsWith("WURCS") ){
        s = encodeURIComponent(s);
    }
    imgurl += "notation=snfg&display=extended&format=png&seq=" + s;


    result_container_additional.innerHTML += "<br><img src='"+imgurl+"'>";
    result_container_additional.innerHTML += "<br>"+"Status: "+ retrieve_result.result.status;
    if (retrieve_result.result.status == "Registered") {
      result_container_additional.innerHTML += "<br>"+"Accession: <A href=\"https://glytoucan.org/Structures/Glycans/"+retrieve_result.result.accession+"\">"+ retrieve_result.result.accession + "</A>";
    }
    result_container_additional.innerHTML += "<p></p>";


}
