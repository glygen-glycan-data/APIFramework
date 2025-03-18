
function glymagesvg_init() {
    let params = {
        baseurl:               "https://glymage.glyomics.org/",
        imageclass:            "glymagesvg_hover_low_opacity",
        monoclass:             "glymagesvg_hover_high_opacity",
        substclass:            "glymagesvg_hover_high_opacity",
        linkclass:             "glymagesvg_hover_high_opacity",
        linkinfoclass:         "glymagesvg_hover_high_opacity",
        parentlinkclass:       "glymagesvg_hover_low_opacity",
        linkinfoclass:         "glymagesvg_hover_high_opacity",
        parentlinkinfoclass:   "glymagesvg_hover_high_opacity_anomer",
        highlight_parent_link: "true"
    };
    glymagesvg.init(params);
};

var script1 = document.createElement('script');
// script1.onload = glymagesvg_init;
script1.src = "https://glymage.glyomics.org/js/glymagesvg.js";
document.head.append(script1);

var glymage;

function glymage_init() {
    glymage = new Glymage();
    glymage.setUserEmail("SubstructureFrontEnd@glyomics.org");
};

var script2 = document.createElement('script');
script2.onload = glymage_init;
script2.src = "glycoapi.js";
document.head.append(script2);

