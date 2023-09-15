
function getglymagesvgloc() {
   let scripts = document.getElementsByTagName("script");
   let jsurl = scripts[scripts.length-1].src;
   return jsurl.substring(0,jsurl.length-'/js/glymagesvg.js'.length)
}

var glymagesvg = {

    params: {
        baseurl: getglymagesvgloc(),
        display: "snfg",
        style: "extended",
	imageclass: "glymagesvg_glycanimage",
        clickaction: "multi"
    },

    config: function(params) {
        for (var param in params) {
            glymagesvg.params[param] = params[param]
        }
    },

    init: function(params) {
        if (params) {
            glymagesvg.config(params);
        }
        console.log("GlymageSVG Global Parameters:");
        console.log(glymagesvg.params);
        var head = document.getElementsByTagName('head')[0];
        head.innerHTML += '<link rel="stylesheet" href="'+glymagesvg.params.baseurl+'/css/glymagesvg.css" type="text/css" />';

        let svgcontainers = document.querySelectorAll('[glymagesvg_accession]');
        for (let svgcont of svgcontainers) {
	    var glysvgobj = new glymagesvg.GlymageSVG(svgcont);
        } 

    },

    GlymageSVG: function(__element__, __params__) {

	this.initialize = function(params,elt) {
            this.click_mode = "";
            this.clicked = new Set();
	    this.remann2remelt = {};
	    this.remann2class = {};
	    this.monoid2monoelt = {};
	    this.remann2monoid = {};
	    this.monoid2remann = {};

	    this.params = params;
	    this.svgContainer = elt;
	    this.acc = elt.getAttribute('glymagesvg_accession');
	    this.container_id = elt.getAttribute('id');
	    this.annotation = elt.getAttribute('glymagesvg_annotation') || params.annotation;
	    this.monoclass = elt.getAttribute('glymagesvg_monoclass') || params.monoclass;
	    this.linkclass = elt.getAttribute('glymagesvg_linkclass') || params.linkclass;
	    this.tooltip = elt.getAttribute('glymagesvg_tooltip') || params.tooltip;
            this.clickaction = elt.getAttribute('glymagesvg_clickaction') || params.clickaction;
	    if (!this.monoclass) {
                this.monoclass = elt.getAttribute('glymagesvg_class');
            }
	    if (!this.linkclass) {
                this.linkclass = elt.getAttribute('glymagesvg_class');
            }

            if (this.params.imageurl != null) {
                this.imageurl = this.params.imageurl;
            }
            if (this.params.jsonurl != null) {
                this.jsonurl = this.params.jsonurl;
            }

	    this.dofetch();
        }

	this.dofetch = function() {
	    
	    fetch(this.imageurl(this.acc))
		.then((response) => {
		    if (response.ok) {
			return response.text();
		    } else { 
			console.log("I need an svg file:", svg_file, response.text())
			throw new Error('SVG file not available !!!!');
		    }
		})
		.then((svgText) => {
		    fetch(this.jsonurl(this.acc))
			.then((response) => {
			    if (response.ok) {
				return response.json();
			    } else {
				console.log("error check");
			    }
			})
			.then((data) => {
			    this.data = data;
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(svgText, "image/svg+xml");
                            let svgElement = doc.documentElement;
                            svgElement.setAttribute("class", this.params.imageclass);			    
                            this.svgContainer.appendChild(svgElement);
			    this.svgElement = svgElement;
			    this.settooltip();
			    this.setclass();
			    this.setremotes();
			})
			.catch((error) => {
			    console.error('JSON file not Found:', this.acc, error);
			}); // JSON get
		})
		.catch((error) => {
		    console.error('SVG file not Found:', this.acc, error);
		}); // SVG get
	}

	this.settooltip = function() {
	    if ((this.tooltip != null) && (this.tooltip != "-")) {
		let svgid2title = {};
		for (let res of this.data.residues) {
		    let resid = res.residueid;
		    let svgid = this.data.residuemap[resid][0];
		    svgid2title[svgid] = res[this.tooltip];
		}
		for (let elt of this.svgElement.getElementsByTagName("g")) {
		    let svgid = elt.getAttribute("ID");
		    if (svgid in svgid2title) {
			elt.innerHTML += '<title>' + svgid2title[svgid] + '</title>';
		    }
		}
	    }
	}

	this.setclass = function() {
            if (this.annotation && this.data.annotations) {
		let annotation_dict = this.annotation.split(".")[0]
		let annotation = this.annotation.substring(annotation_dict.length+1,this.annotation.length);
		if (this.data.annotations[annotation_dict]) {
		    if (!this.data.annotations[annotation_dict][annotation] && 
			 this.data.annotations[annotation_dict]['__synonyms__'] && 
			 this.data.annotations[annotation_dict]['__synonyms__'][annotation]) {
			annotation = this.data.annotations[annotation_dict]['__synonyms__'][annotation];
		    }
		    if (this.data.annotations[annotation_dict][annotation]) {
			var svgids = new Set();
			for (let canonid of this.data.annotations[annotation_dict][annotation]) {
			    if (this.data.residuemap[canonid]){
				for (let svgid of this.data.residuemap[canonid]) {
				    svgids.add(svgid);
				}
			    }
			}
			for (let elt of this.svgElement.getElementsByTagName("g")) {
			    if (svgids.has(elt.getAttribute("ID"))) {
				if (elt.getAttribute("data.type") == "Monosaccharide" && this.monoclass) {
				    elt.setAttribute("class",this.monoclass);
				}
				if (elt.getAttribute("data.type") == "Linkage" && this.linkclass) {
				    elt.setAttribute("class",this.linkclass);
				}
			    }
			}
		    }
		}
	    }
	}

	this.setremotes = function() {
	    let remoteelts = document.querySelectorAll('[glymagesvg_forid='+this.container_id+']');
	    let anyremotes = false;
            for (let remelt of remoteelts) {
		anyremotes = true;
		let remelt_annotation = remelt.getAttribute("glymagesvg_annotation")
		if (remelt_annotation && this.data.annotations) {
		    let annotation_dict = remelt_annotation.split(".")[0]
		    let annotation = remelt_annotation.substring(annotation_dict.length+1,remelt_annotation.length);
		    if (this.data.annotations[annotation_dict]) {
			if (!this.data.annotations[annotation_dict][annotation] && 
			    this.data.annotations[annotation_dict]['__synonyms__'] && 
			    this.data.annotations[annotation_dict]['__synonyms__'][annotation]) {
			    annotation = this.data.annotations[annotation_dict]['__synonyms__'][annotation];
			}
			var svgids = new Set();
			if (this.data.annotations[annotation_dict][annotation]) {
			    for (let canonid of this.data.annotations[annotation_dict][annotation]) {
				if (this.data.residuemap[canonid]){
				    for (let svgid of this.data.residuemap[canonid]) {
					svgids.add(svgid);
				    }
				}
			    }
			}
			this.remann2remelt[remelt_annotation] = remelt;
			this.remann2monoid[remelt_annotation] = svgids;
			this.remann2class[remelt_annotation] = remelt.getAttribute('glymagesvg_textclass');
			for (let svgid of svgids) {
			    if (!(svgid in this.monoid2remann)) {
				this.monoid2remann[svgid] = [];
			    }
			    this.monoid2remann[svgid].push(remelt_annotation);
			}
			remelt.onclick = this.handler("handle_remote_click", remelt_annotation);
			remelt.style.cursor = 'pointer';
		    }
		}
            }
	    if (anyremotes) {
		for (let elt of this.svgElement.getElementsByTagName("g")) {
		    let svgid = elt.getAttribute("ID");
		    if (elt.getAttribute("data.type") == "Monosaccharide") {
			this.monoid2monoelt[svgid] = elt;
			if (!(svgid in this.monoid2remann)) {
			    this.monoid2remann[svgid] = [];
			}
			elt.onclick = this.handler("handle_mono_click", svgid);
			elt.style.cursor = 'pointer';
		    } else if (elt.getAttribute("data.type") == "Linkage") {
			if (svgid in this.monoid2remann) {
			    this.monoid2monoelt[svgid] = elt;
			}
		    }
		}
	    }
	}

	this.handle_remote_click = function(event, remann) {
	    if (this.click_mode != "remote") {
		this.clicked = new Set();
		this.click_mode = "remote";
	    }
	    if (this.clicked.has(remann)) {
	        this.clicked.delete(remann);
	    } else {
                if (this.clickaction == "multi") {
		    this.clicked.add(remann);
	        } else {
		    this.clicked = new Set([remann]);
                }
            }
	    this.refresh();
	}

	this.handle_mono_click = function(event, monoid) {
	    if (this.click_mode != "mono") {
		this.clicked = new Set();
		this.click_mode = "mono";		
	    }
	    if (this.clicked.has(monoid)) {
		this.clicked.delete(monoid);
	    } else {
                if (this.clickaction == "multi") {
		    this.clicked.add(monoid);
	        } else {
		    this.clicked = new Set([monoid]);
                }
	    }
	    this.refresh();
	}
	
	this.refresh = function() {
	    let highlight_monoids = new Set();
	    let highlight_remann = new Set();
	    if (this.click_mode == "remote") {
		for (let remann of this.clicked) {
		    highlight_remann.add(remann);
		    for (let monoid of this.remann2monoid[remann]) {
			highlight_monoids.add(monoid);
		    }
		}
	    } else {
		for (let monoid of this.clicked) {
		    highlight_monoids.add(monoid);
		    for (let remann of this.monoid2remann[monoid]) {
			highlight_remann.add(remann);
		    }
		}
	    }
	    for (let monoid in this.monoid2monoelt) {
		this.monoid2monoelt[monoid].classList.remove(this.monoclass);		
		if (highlight_monoids.has(monoid)) {
		    this.monoid2monoelt[monoid].classList.add(this.monoclass);
		}
            }
	    for (let remann in this.remann2remelt) {
		this.remann2remelt[remann].classList.remove(this.remann2class[remann]);
		if (highlight_remann.has(remann)) {
		    this.remann2remelt[remann].classList.add(this.remann2class[remann]);
		}
	    }
	}

        this.jsonurl = function(acc) {
            return this.params.baseurl + "/image/" + this.params.display + "/" + this.params.style + "/" + acc + ".json";
        }

        this.imageurl = function(acc) {
            return this.params.baseurl + "/image/" + this.params.display + "/" + this.params.style + "/" + acc + ".svg";
        }

        // use this handler to deal with "anonymous" instances.
        this.handler = function(methodname, arg1, arg2, arg3, arg4, arg5, arg6) {
            var that = this;
            var a1 = arg1;
            var a2 = arg2;
            var a3 = arg3;
            var a4 = arg4;
            var a5 = arg5;
            var a6 = arg6;
            return function(event) {
                return that[methodname](event, a1, a2, a3, a4, a5, a6);
            }
        }

        this.initialize(__params__||glymagesvg.params,__element__);

    }

} // end of var glymagesvg 
