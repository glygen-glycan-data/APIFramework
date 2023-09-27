
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
        if (!(head.innerHTML.includes('glymagesvg.css'))) {
            head.innerHTML += '<link rel="stylesheet" href="'+glymagesvg.params.baseurl+'/css/glymagesvg.css" type="text/css" />';
        }

        let svgcontainers = document.querySelectorAll('[glymagesvg_accession]');
        for (let svgcont of svgcontainers) {
            if (svgcont.getAttribute('glymagesvg_processed') == null) {
	        var glysvgobj = new glymagesvg.GlymageSVG(svgcont);
            }
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
	    this.imageclass = elt.getAttribute('glymagesvg_imageclass') || params.imageclass
	    this.monoclass = elt.getAttribute('glymagesvg_monoclass') || params.monoclass;
	    this.linkclass = elt.getAttribute('glymagesvg_linkclass') || params.linkclass;
	    this.linkinfoclass = elt.getAttribute('glymagesvg_linkinfoclass') || params.linkinfoclass;
	    this.tooltip = elt.getAttribute('glymagesvg_tooltip') || params.tooltip;
            this.clickaction = elt.getAttribute('glymagesvg_clickaction') || params.clickaction;
            this.clickhlparentlink = (elt.getAttribute('glymagesvg_clickhlparentlink') || params.clickhlparentlink) == "true";
            this.addmonoonclick = (elt.getAttribute('glymagesvg_addmonoonclick') || params.addmonoonclick) == "true";
            this.width = elt.getAttribute('glymagesvg_width') || params.width;
            this.height = elt.getAttribute('glymagesvg_height') || params.height;
            this.position = elt.getAttribute('glymagesvg_insertpos') || params.insertpos;
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
            elt.setAttribute('glymagesvg_processed',"true");
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
                                throw new Error('JSON file not available !!!!');
			    }
			})
			.then((data) => {
			    this.data = data;
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(svgText, "image/svg+xml");
                            let svgElement = doc.documentElement;
			    			    let grelts = Array.from(svgElement.getElementsByTagName("g"));
			    for (let elt of grelts) {
				if ((elt.getAttribute("ID") != null) && (elt.getAttribute("data.type") == "Monosaccharide")) {
				    let newelt = elt.cloneNode();
				    for (let attr of newelt.attributes) {
					if (attr.name.includes("data.")) {
					    newelt.removeAttribute(attr.name);
                                        }
				    }
				    newelt.removeAttribute("ID");
				    newelt.classList.add("glymagesvg_monomask");
				    for (let ch of elt.children) {
					let newch = ch.cloneNode();
					if (newch.style.fill.includes("rgb(")) {
					    newch.style.fill = 'rgb(255,255,255)';
					} else if (newch.style.stroke == "black") {
					    newch.style.stroke = "white";
					}
					newelt.appendChild(newch);
				    }
				    svgElement.children[1].insertBefore(newelt,elt);
				    // svgElement.children[1].removeChild(elt);
				}
			    }
			    svgElement.classList.add(this.params.imageclass);
                            if (this.width != null) {
                                svgElement.setAttribute("width", this.width);
				if (this.height == null) {
                                    svgElement.setAttribute("height", "auto");
                                }
			    } 
                            if (this.height != null) {
                                svgElement.setAttribute("height", this.height);
				if (this.width == null) {
                                    svgElement.setAttribute("width", "auto");
                                }
                            }

			    if (this.position != null) {
				var refnode = this.svgContainer.childNodes[this.position];
				this.svgContainer.insertBefore(svgElement,refnode);
			    } else {
				this.svgContainer.appendChild(svgElement);
			    }
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
		if (this.data.annotations[annotation_dict] || (annotation_dict == "CanonicalResidueIDs")) {
		    if (this.data.annotations[annotation_dict] &&
			!this.data.annotations[annotation_dict][annotation] && 
			this.data.annotations[annotation_dict]['__synonyms__'] && 
			this.data.annotations[annotation_dict]['__synonyms__'][annotation]) {
			annotation = this.data.annotations[annotation_dict]['__synonyms__'][annotation];
		    }
		    var thecanonids = null;
		    if (annotation_dict == "CanonicalResidueIDs") {
                        thecanonids = annotation.split(",");
		    } else if (this.data.annotations[annotation_dict][annotation]) {
			thecanonids = this.data.annotations[annotation_dict][annotation];
                    }
		    if (thecanonids) {
			var svgids = new Set();
			for (let canonid of thecanonids) {
			    if (this.data.residuemap[canonid]){
				for (let svgid of this.data.residuemap[canonid]) {
				    svgids.add(svgid);
				}
			    }
			}
			if (this.imageclass) {
			    this.svgElement.classList.add(this.imageclass);
			}
			for (let elt of this.svgElement.getElementsByTagName("g")) {
			    if (!elt.getAttribute("ID")) {
				continue;
			    }
			    if (svgids.has(elt.getAttribute("ID"))) {
				if (elt.getAttribute("data.type") == "Monosaccharide" && this.monoclass) {
				    elt.classList.add(this.monoclass);
				}
				else if (elt.getAttribute("data.type") == "Linkage" && this.linkclass) {
				    elt.classList.add(this.linkclass);
				}
			    } else if (svgids.has(elt.getAttribute("ID").replace("li","l")) && this.linkinfoclass) {
				elt.classList.add(this.linkinfoclass);
			    }
			}
		    }
		}
	    }
	}

	this.setremotes = function() {
	    let remoteelts = document.querySelectorAll('[glymagesvg_forid='+this.container_id+']');
	    let anyremotes = false;
	    let remeltind = -1;
            for (let remelt of remoteelts) {
		remeltind += 1;
		let remelt_annotation = remelt.getAttribute("glymagesvg_annotation")
		if (remelt_annotation && this.data.annotations) {
		    let annotation_dict = remelt_annotation.split(".")[0]
		    let annotation = remelt_annotation.substring(annotation_dict.length+1,remelt_annotation.length);
		    if (this.data.annotations[annotation_dict] || (annotation_dict == "CanonicalResidueIDs")) {
		        anyremotes = true;
			if (this.data.annotations[annotation_dict] &&
			    !this.data.annotations[annotation_dict][annotation] && 
			    this.data.annotations[annotation_dict]['__synonyms__'] && 
			    this.data.annotations[annotation_dict]['__synonyms__'][annotation]) {
			    annotation = this.data.annotations[annotation_dict]['__synonyms__'][annotation];
			}
			var svgids = new Set();
			var thecanonids = null;
			if (annotation_dict == "CanonicalResidueIDs") {
                            thecanonids = annotation.split(",");
			} else if (this.data.annotations[annotation_dict][annotation]) {
			    thecanonids = this.data.annotations[annotation_dict][annotation];
                        }
			if (thecanonids) {
			    for (let canonid of thecanonids) {
				if (this.data.residuemap[canonid]){
				    for (let svgid of this.data.residuemap[canonid]) {
					svgids.add(svgid);
					if (svgid.startsWith('l-1:')) {
					    svgids.add(svgid.replace('l','li'));
					}
				    }
				}
			    }
			}
			let remeltindstr = remeltind.toString();
			this.remann2remelt[remeltindstr] = remelt;
			this.remann2monoid[remeltindstr] = svgids;
			this.remann2class[remeltindstr] = remelt.getAttribute('glymagesvg_textclass');
			for (let svgid of svgids) {
			    if (!(svgid in this.monoid2remann)) {
				this.monoid2remann[svgid] = [];
			    }
			    this.monoid2remann[svgid].push(remeltindstr);
			}
			remelt.onclick = this.handler("handle_remote_click", remeltindstr);
			remelt.style.cursor = 'pointer';
		    }
		}
            }
	    if (anyremotes) {
                this.monoid2relatedmonoid = {};
		for (let elt of this.svgElement.getElementsByTagName("g")) {
		    let svgid = elt.getAttribute("ID");
		    if (elt.getAttribute("data.type") == "Monosaccharide") {
			this.monoid2monoelt[svgid] = elt;
			if (!(svgid in this.monoid2remann)) {
			    this.monoid2remann[svgid] = [];
			}
			elt.onclick = this.handler("handle_mono_click", svgid);
			elt.style.cursor = 'pointer';
                        if (!(svgid in this.monoid2relatedmonoid)) {
                            this.monoid2relatedmonoid[svgid] = [];
                        }
		    } else if (elt.getAttribute("data.type") == "Linkage") {
			this.monoid2monoelt[svgid] = elt;
                        if (this.clickhlparentlink) {
                            let ids = svgid.split(':')[1].split(',');
                            let nodesvgid = "r-1:"+ids[1];
                            // console.log(svgid,nodesvgid);
                            if (!(nodesvgid in this.monoid2relatedmonoid)) {
                                this.monoid2relatedmonoid[nodesvgid] = [];
                            }
                            this.monoid2relatedmonoid[nodesvgid].push(svgid);
                        }
		    } else if (svgid && svgid.startsWith("li-1")) {
			this.monoid2monoelt[svgid] = elt;
                        if (this.clickhlparentlink) {
                            let ids = svgid.split(':')[1].split(',');
                            let nodesvgid = "r-1:"+ids[1];
                            // console.log(svgid,nodesvgid);
                            if (!(nodesvgid in this.monoid2relatedmonoid)) {
                                this.monoid2relatedmonoid[nodesvgid] = [];
                            }
                            this.monoid2relatedmonoid[nodesvgid].push(svgid);
                        }
		    }
		}
		this.svgElement.children[1].children[1].onclick = this.handler("handle_reset_click");
		this.svgElement.children[1].children[1].style.cursor = 'pointer';
                // console.log(this.monoid2relatedmonoid);
	    }
	}

	this.handle_reset_click = function(event) {
	    this.clicked = new Set();
	    this.click_mode = null;
	    this.refresh();
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
                if (this.addmonoonclick) {
		    for (let remann of this.monoid2remann[monoid]) {
		      for (let monoid2 of this.remann2monoid[remann]) {
			 this.clicked.delete(monoid2);
                      }
                    }
                }
	    } else {
                if (this.clickaction == "multi") {
		    this.clicked.add(monoid);
	        } else {
		    this.clicked = new Set([monoid]);
                }
                if (this.addmonoonclick) {
		    for (let remann of this.monoid2remann[monoid]) {
		      for (let monoid2 of this.remann2monoid[remann]) {
			 this.clicked.add(monoid2);
                      }
                    }
                }
	    }
	    this.refresh();
	}
	
	this.refresh = function() {
	    // console.log(this.click_mode,this.clicked)
	    let highlight_monoids = new Set();
	    let highlight_remann = new Set();
	    if (this.click_mode == "remote") {
		for (let remann of this.clicked) {
		    highlight_remann.add(remann);
		    for (let monoid of this.remann2monoid[remann]) {
			highlight_monoids.add(monoid);
                        if (this.monoid2relatedmonoid[monoid]) {
                            for (let monoid1 of this.monoid2relatedmonoid[monoid]) {
                                highlight_monoids.add(monoid1);
                            }
                        }
		    }
		}
	    } else {
		for (let monoid of this.clicked) {
		    highlight_monoids.add(monoid);
                    if (this.monoid2relatedmonoid[monoid]) {
                        for (let monoid1 of this.monoid2relatedmonoid[monoid]) {
                            highlight_monoids.add(monoid1);
                        }
                    }
		    for (let remann of this.monoid2remann[monoid]) {
			highlight_remann.add(remann);
		    }
		}
	    }
            // console.log(highlight_monoids);
            // console.log(highlight_remann);
	    if (this.imageclass) {
		if (this.clicked.size > 0) {
		    this.svgElement.classList.add(this.imageclass);
		} else {
		    this.svgElement.classList.remove(this.imageclass);
		}
	    } 
	    // console.log(highlight_monoids);
	    // console.log(highlight_remann);
	    for (let monoid in this.monoid2monoelt) {
		if (highlight_monoids.has(monoid)) {
		    this.monoid2monoelt[monoid].classList.add(this.monoclass);
		} else {
		    this.monoid2monoelt[monoid].classList.remove(this.monoclass);		
		}
            }
	    for (let remann in this.remann2remelt) {
		if (highlight_remann.has(remann)) {
		    this.remann2remelt[remann].classList.add(this.remann2class[remann]);
		} else {
		    this.remann2remelt[remann].classList.remove(this.remann2class[remann]);
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
