


function renderResultMore(){
    show("result_container");

    let result = retrieve_result.result;
    let error = retrieve_result.error;
    let stat = retrieve_result.stat;
    let task = retrieve_result.task;

    let align = (task && task.align) || 'substructure';
    if (align == "all") {
        align = 'substructure';
    }

    let result_container_status = document.getElementById("result_container_status");
    let result_container_additional = document.getElementById("result_container_additional");

    let align_text = "substructure";
    if (align == 'core') {
        align_text = 'glycan-core';
    } else if (align == 'nonreducingend') {
        align_text = 'nonreducing-end';
    } else if (align == 'wholeglycan') {
        align_text = 'whole-glycan';
    }

    if (error.length > 0){
        let tmp = error.join(", ");
        result_container_status.innerHTML += "<p style='font-size: 25px; color: red; '>Error: "+tmp+"</p>";
        return;
    } else if (result[align].length > 0){
        result_container_status.innerHTML += "<p style='font-size: 25px;'>Found "+result[align].length+" "+align_text+" alignments.</p>";
    }
    else {
        result_container_status.innerHTML += "<p style='font-size: 25px;'>No " + align_text + " alignments found.</p>";
    }




    let imgurl = "https://glymage.glyomics.org/getimage?";
    let s = task.seq;
    if ( !s.startsWith("WURCS") ){
        s = encodeURIComponent(s);
    }
    imgurl += "notation=snfg&display=extended&format=png&seq=" + s;


    result_container_additional.innerHTML += "<br><img src='"+imgurl+"'><p>Query</p>";

    if (result[align].length == 0){
        return
    }

    let sub_table = "<br><table style='width: 100%; border: black solid 3px; font-size: 15px;'>";
    sub_table += "" +
            "<tr style='height: 28px; background-color: grey'><td>Results</td></tr>";


    for (let i in result[align]){
        let lightstr = 'light';
        let r = result[align][i];

        if (i % 2 == 1){
            lightstr = "";
        }

        let strictstr = ""
        if (r[1]){
            strictstr = " (strict)"
        }

        sub_table += "" +
            "<tr style='background-color: "+lightstr+"grey'><td><img src='https://glymage.glyomics.org/image/snfg/extended/"+r[0]+".png' style='max-width: 100%; max-height: 150px;'><br><a href='https://glytoucan.org/Structures/Glycans/"+r[0]+"'>"+ r[0] +"</a> "+strictstr+"</td></tr>";

    }

    sub_table += "</table>";
    result_container_additional.innerHTML += sub_table + "<br>";


}
