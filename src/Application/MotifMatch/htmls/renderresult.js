


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
        result_container_status.innerHTML += "<p style='font-size: 25px;'>No structure found</p>";
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


    result_container_additional.innerHTML += "<br><img src='"+imgurl+"'><p>Query glycan (motif)</p>";

    if (result.length == 0){
        return
    }


    let sub_table = "<br><table style='width: 100%; border: black solid 3px; font-size: 15px;'>";
    sub_table += "" +
            "<tr style='height: 28px; background-color: grey'><td>GlyTouCan</td><td>GlycoMotif</td><td>Image</td><td>Alignment type</td></tr>";


    for (let i in result){
        let lightstr = 'light';
        // Collection, pageid, gtcacc, name, alignment type, strict
        let r = result[i];


        if (i % 2 == 1){
            lightstr = "";
        }

        let pagename = r[0] + "." + r[1]

        let at = r[4];
        if (r[1]){
            at += " (strict)"
        }



        sub_table += "" +
            "<tr style='background-color: "+lightstr+"grey'>" +
            "<td><a href='https://glytoucan.org/Structures/Glycans/"+r[2]+"'>"+ r[2] +"</a></td>" +
            "<td><a href='https://glycomotif.glyomics.org/glycomotif/"+pagename+"'>"+pagename+"</a></td>" +
            "<td><img src='https://glymage.glyomics.org/image/snfg/extended/"+r[2]+".png' style='max-width: 100%; max-height: 150px;'></td>" +
            "<td>"+at+"</td>" +
            "</tr>";
        // <a href='https://glytoucan.org/Structures/Glycans/"+r[2]+"'>"+ r[2] +"</a>
        // "<td></td>" +
    }

    sub_table += "</table>";
    result_container_additional.innerHTML += sub_table + "<br>";


}