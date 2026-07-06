
function glymagesvg_init() {
    let params = {
        baseurl:               "{{glymage_base_url}}",
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

var thisws;
var glymage;

function init() {
    thisws = new APIFramework({ baseurl: ".", 
                                developer_email: "{{frontend_dev_email}}" });
    if ("{{glymage_dev_email}}" !== "" && "{{glymage_dev_email}}" !== "-") {
        glymage = new Glymage({ baseurl: "{{glymage_base_url}}", 
                                developer_email: "{{glymage_dev_email}}" });
    } else if ("{{glymage_dev_email}}" !== "-") {
        console.log("Glymage dev email is not set!")
    }
    StartApplication();
};

var script1 = document.createElement('script');
script1.src = "{{glymage_base_url}}/js/glymagesvg.js";
script1.onload = glymagesvg_init
document.head.append(script1);

var script2 = document.createElement('script');
script2.onload = init;
script2.src = "glycoapi.js";
document.head.append(script2);


