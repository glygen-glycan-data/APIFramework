"use strict";


function APIFrameworkJS(url) {

    this.ServiceBaseURL = url;
    if (this.ServicePublicURL == undefined){
        this.ServicePublicURL = "";
    }
    if (!this.ServiceBaseURL && this.ServicePublicURL) {
        this.ServiceBaseURL = this.ServicePublicURL;
    }

    this.UserEmail = "";

    this.setServiceURL = function (url){
        this.ServiceBaseURL = url;
    }

    this.usePublicServiceURL = function (){
        this.ServiceBaseURL = this.ServicePublicURL;
    }

    this.useCurrentServiceURL = function (){

        let protocol = window.location.protocol;
        let host = window.location.hostname;
        let port = window.location.port;

        if (["", 22, "22"].includes(port)){
            port = ""
        } else {
            port = ":" + port.toString()
        }

        let res = protocol + "//" + host + port;
        this.ServiceBaseURL = res;

    }

    this.setUserEmail = function (email){
        this.UserEmail = email;
    }

    this.submit = function (para) {

        this.parameterCheck(para);
        if (this.UserEmail == ""){
            throw new Error("Please provide your email")
        }
        let url = this.ServiceBaseURL + "/submit";
        let data = {
            "task": JSON.stringify(para),
            "developer_email": this.UserEmail
        };

        return new Promise((resolve, reject) => {
            jQuery.post(url, data).then(function (d) {
                if (d == "Please submit with actual tasks") {
                    reject("Empty parameter")
                }
                resolve(d[0].id);
            });
        });
    }

    this.retrieve = function (tid, timeout) {

        let url = this.ServiceBaseURL + "/retrieve";

        if (timeout == undefined) {
            timeout = 5;
        }
        let data = {
            "task_id": tid,
            "timeout": timeout
        };

        return new Promise((resolve, reject) => {
            jQuery.post(url, data).then(function (d) {
                resolve(d[0])
            });
        });
    }

    this.request = async function (para,callback) {
        let tid = await this.submit(para);
        let dateobj = Date()
        let start = dateobj.getTime()
        let finish = false;
        while (!finish) {
            let res = await this.retrieve(tid);

            finish = res.finished
            if (finish) {
                return res
            }
            if (callback != undefined) {
                if (callback(dateobj.getTime()-start) == false) {
                    return res;
                }
            }
        }
    }

    this.parameterCheck = function (para) {
        // Parameter check before send it to service backend
    }


}









function Glylookup (url) {
    this.ServicePublicURL = "https://glylookup.glyomics.org";
    APIFrameworkJS.call(this, url);

    this.parameterCheck = function (para) {

        if ( !Object.keys(para).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

function MotifMatch (url) {
    this.ServicePublicURL = "https://motifmatch.glyomics.org";
    APIFrameworkJS.call(this, url);

    this.parameterCheck = function (para) {

        if ( !Object.keys(para).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

function Substructure (url) {
    this.ServicePublicURL = "https://substructure.glyomics.org";
    APIFrameworkJS.call(this, url);

    this.parameterCheck = function (para) {

        if ( !Object.keys(para).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

function Subsumption (url) {
    this.ServicePublicURL = "https://subsumption.glyomics.org";
    APIFrameworkJS.call(this, url);

    this.parameterCheck = function (para) {

        if ( !Object.keys(para).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

function Converter (url) {
    this.ServicePublicURL = "https://converter.glyomics.org";
    APIFrameworkJS.call(this, url);

    this.parameterCheck = function (para) {

        if ( !Object.keys(para).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

        if ( !Object.keys(para).includes("format") ){
            throw new Error("Please provide desired format")
        }

    }
}

function Glymage (url) {
    this.ServicePublicURL = "https://glymage.glyomics.org";
    APIFrameworkJS.call(this, url);

    this.parameterCheck = function (para) {

        if ( !Object.keys(para).includes("seq") && !Object.keys(para).includes("acc") ){
            throw new Error("Please provide glycan sequence or accession")
        }

    };

    this.getImageURL = async function (para) {
        let tid = await this.submit(para);
        return this.ServiceBaseURL + "/getimage?task_id=" + tid;
    };

    this.setPrecomputedImageURL = async function(selector,params) {
        let imgdis = params.display || "extended";
        let imgfmt = params.image_format || "png";
        let imgelts = document.querySelectorAll(selector);
        for (let imgelt of imgelts) {
            imgelt.src = this.ServiceBaseURL + '/image/snfg/' + imgdis + '/' + params.acc + "." + imgfmt;
        }
    };

    this.setOnDemandImageURL = async function(selector,params) {
        this.getImageURL(params).then((url) => {
           let imgelts = document.querySelectorAll(selector);
           for (let imgelt of imgelts) {
               imgelt.src = url;
           }
        });
    };
}

function Register (url) {
    this.ServicePublicURL = "https://register.glyomics.org/";
    APIFrameworkJS.call(this, url);

    this.parameterCheck = function (para) {

        if ( !Object.keys(para).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}




