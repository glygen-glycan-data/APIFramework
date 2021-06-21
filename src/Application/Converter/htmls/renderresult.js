


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


    let imgurl = "https://glymage.glyomics.org/getimage?";
    let s = retrieve_result.task.seq;
    if ( !s.startsWith("WURCS") ){
        s = encodeURIComponent(s);
    }
    imgurl += "notation=snfg&display=extended&format=png&seq=" + s;


    result_container.innerHTML += "<br><img src='"+imgurl+"'>";
    result_container.innerHTML += "<br><p>"+retrieve_result.result.replaceAll("\n", "<br>")+"</p>"

    if (result.length == 0){
        return
    }



}