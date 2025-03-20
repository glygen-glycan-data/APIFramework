


function renderResultMore(){
    show("result_container");

    let result = retrieve_result.result;
    let error = retrieve_result.error;
    let stat = retrieve_result.stat;

    let result_container_status = document.getElementById("result_container_status");
    let result_container_additional = document.getElementById("result_container_additional");


    if (result.length > 0){
        result_container_status.innerHTML += "<p style='font-size: 25px;'>Found "+result.length+" motif(s)</p>";
    }
    else {
        result_container_status.innerHTML += "<p style='font-size: 25px;'>No motifs matched</p>";
    }


    if (error.length > 0){
        let tmp = error.join(", ");
        result_container_status.innerHTML += "<p style='font-size: 25px; color: red; '>Error: "+tmp+"</p>";
    }

    result_container_additional.innerHTML += "<br><img id='inputseqimg'><p>Query structure</p>";
    glymage.setOnDemandImageURL('#inputseqimg',{'seq': retrieve_result.task.seq, 'image_format': 'svg'});

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
        if (r[5]){
            at += " (strict)"
        }



        sub_table += "" +
            "<tr style='background-color: "+lightstr+"grey'>" +
            "<td><a href='https://glytoucan.org/Structures/Glycans/"+r[2]+"'>"+ r[2] +"</a></td>" +
            "<td><a href='https://glycomotif.glyomics.org/glycomotif/"+pagename+"'>"+pagename+"</a></td>" +
            "<td><img src='{{glymage_base_url}}/image/snfg/extended/"+r[2]+".svg' style='max-width: 100%; max-height: 150px;'></td>" +
            "<td>"+at+"</td>" +
            "</tr>";
        // <a href='https://glytoucan.org/Structures/Glycans/"+r[2]+"'>"+ r[2] +"</a>
        // "<td></td>" +
    }

    sub_table += "</table>";
    result_container_additional.innerHTML += sub_table + "<br>";

}
