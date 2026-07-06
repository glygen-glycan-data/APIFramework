
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

var script2 = document.createElement('script');
script2.onload = init;
script2.src = "glycoapi.js";
document.head.append(script2);

