
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

    result_container_additional.innerHTML += "<br><img id='inputseqimg'><p>Query</p>";
    glymage.setOnDemandImageURL("inputseqimg",{'seq': task.seq, 'image_format': 'svg'});

    if (result[align].length == 0){
        return
    }

    let sub_table = "<br><table style='width: 100%; border: black solid 3px; font-size: 15px;'>";
    sub_table += "" +
            "<tr style='height: 28px; background-color: grey'><td>Results</td></tr>";


    for (let i in result[align].slice(0,50)){
        let lightstr = 'light';
        let r = result[align][i];

        if (i % 2 == 1){
            lightstr = "";
        }

        let strictstr = ""
        if (r[1]){
            strictstr = " (strict)"
        }
        
        let canonids = r[2].join(",") + "," + r[3].join(",");

        sub_table += "" +
            "<tr style='background-color: "+lightstr+"grey'><td><figure glymagesvg_accession='"+r[0]+"' glymagesvg_annotation='CanonicalResidueIDs." + canonids + "' ></figure><br><a href='https://glytoucan.org/Structures/Glycans/"+r[0]+"'>"+ r[0] +"</a> "+strictstr+"</td></tr>";

    }

    sub_table += "</table>";
    result_container_additional.innerHTML += sub_table + "<br>";
    glymagesvg_init();

}
