
var glymage;

function glymage_init() {
    glymage = new Glymage();
    glymage.setServiceURL("{{glymage_base_url}}");
    glymage.setUserEmail("RegisterFrontEnd@glyomics.org");
};

var script2 = document.createElement('script');
script2.onload = glymage_init;
script2.src = "glycoapi.js";
document.head.append(script2);

