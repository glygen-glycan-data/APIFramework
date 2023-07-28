
var glymagesvg = {

    params: {
        baseurl: "http://glymage.glyomics.org/",
        display: "snfg",
        style: "extended",
	imageclass: "glycanimage"
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

        let svgcontainers = document.querySelectorAll('[glymagesvg_accession]');
        for (let svgcont of svgcontainers) {
	    var glysvgobj = new glymagesvg.GlymageSVG(svgcont);
        } 

    },

    GlymageSVG: function(__element__) {

	this.initialize = function(params,elt) {
	    this.mono_clicked = {};
            this.text_clicked = {};
            this.type_last_clicked = "";
            this.classes_to_remove = new Set ();
	    this.params = params;
	    this.svgContainer = elt;
	    this.acc = elt.getAttribute('glymagesvg_accession');
	    this.container_id = elt.getAttribute('id');
	    this.annotation = elt.getAttribute('glymagesvg_annotation');
	    this.monoclass = elt.getAttribute('glymagesvg_monoclass');
	    this.linkclass = elt.getAttribute('glymagesvg_linkclass');
	    if (!this.monoclass) {
                this.monoclass = elt.getAttribute('glymagesvg_class');
            }
	    if (!this.linkclass) {
                this.linkclass = elt.getAttribute('glymagesvg_class');
            }
	    this.dofetch();
        }

	this.dofetch = function() {
	    
	    fetch(this.imageurl())
		.then((response) => {
		    if (response.ok) {
			return response.text();
		    } else { 
			console.log("I need an svg file:", svg_file, response.text())
			throw new Error('SVG file not available !!!!');
		    }
		})
		.then((svgText) => {
		    fetch(this.jsonurl())
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
			    this.setclass();
			})
			.catch((error) => {
			    console.error('JSON file not Found:', this.acc, error);
			}); // JSON get
		})
		.catch((error) => {
		    console.error('SVG file not Found:', this.acc, error);
		}); // SVG get
	}

	this.setclass = function() {
            if (this.annotation && this.data.annotations) {
		let annotation_dict = this.annotation.split(".")[0]
		let annotation = this.annotation.split(".")[1]
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

        this.jsonurl = function() {
            return this.params.baseurl + "/" + this.params.display + "/" + this.params.style + "/" + this.acc + ".json";
        }

        this.imageurl = function() {
            return this.params.baseurl + "/" + this.params.display + "/" + this.params.style + "/" + this.acc + ".svg";
        }

        // event handlers (such as for onclick) take event as an argument

        this.callback = function(event) {
            //console.log("Type Last Clicked", this.type_last_clicked)
            //console.log("text_clicked:", this.text_clicked)
            //console.log("mono_clicked:", this.mono_clicked)
            //console.log("classes to remove:", this.classes_to_remove)
            //console.log("string classes to remove:", String(this.classes_to_remove))
            

           for (e of this.classes_to_remove){
            const els = document.querySelectorAll('.' + e);
            els.forEach((element) => { element.classList.remove(e)
             });
           }
           
           
           
        //const allElements = document.querySelectorAll('*');
          // allElements.forEach((element) => {

              // for (e of this.classes_to_remove) {
              //element.classList.remove(e);}
               
            //});

            
            this.classes_to_remove = new Set ()




            for (k in this.text_clicked) {
                figure_id = k.split("-")[0]
                annot = k.split("-")[1]
                selected_figure = document.getElementById(figure_id)
                selected_svg = selected_figure.children[0]
                //console.log(selected_svg)
                selected_monos = this.text_clicked[k]
                //console.log(selected_monos)
                for (m of selected_monos) {
                    selected_mono = selected_svg.getElementById(m)
                    //selected_mono.classList.add("highlight_static_outline_green")
                    selected_mono.classList.add(document.getElementById(this.container_id).getAttribute("svg_class"))
                    hl_text = document.querySelector(`[glymagesvg_annotation="${annot}"][glymagesvg_forid="${figure_id}"]`)
                    //console.log(hl_text)
                    //hl_text.classList.add("change_text")
                    hl_text.classList.add(hl_text.getAttribute("glymagesvg_textclass"))
                    console.log("text test",hl_text )

                    this.classes_to_remove.add(document.getElementById(this.container_id).getAttribute("svg_class"))
                    this.classes_to_remove.add(hl_text.getAttribute("glymagesvg_textclass"))

                    //console.log ("class", document.getElementById(this.container_id).getAttribute("svg_class"))
                }

            }

            for (k in this.mono_clicked) {
                selected_text = this.mono_clicked[k]
                for (let t of selected_text) {
                    figure_id = t.split("-")[0]
                    annot = t.split("-")[1]
                    hl_text = document.querySelector(`[glymagesvg_annotation="${annot}"][glymagesvg_forid="${figure_id}"]`)
                    //console.log(hl_text)
                    //hl_text.classList.add("change_text")
                    hl_text.classList.add(hl_text.getAttribute("glymagesvg_textclass"))
                    selected_figure = document.getElementById(figure_id)
                    selected_svg = selected_figure.children[0]
                    selected_mono = selected_svg.getElementById(k)
                    //selected_mono.classList.add("highlight_static_outline_green")
                    selected_mono.classList.add(document.getElementById(this.container_id).getAttribute("svg_class"))
                    
                    this.classes_to_remove.add(document.getElementById(this.container_id).getAttribute("svg_class"))
                    this.classes_to_remove.add(hl_text.getAttribute("glymagesvg_textclass"))
                
                } // end of for t 

            }




            return true;


        }




        // event with additional (optional) argument with default value

        this.incx = function(event, container_id, clicked_dict, clicked_id, element_type) {


            this.container_id = container_id
            this.clicked_dict = clicked_dict
            this.clicked_id = clicked_id
            this.element_type = element_type
            
            //console.log(this.element_type)
            //console.log(this)


            if (this.element_type == "mono") {

                if (this.type_last_clicked == "text") {
                    this.text_clicked = {}
                    this.mono_clicked = {}
                }

                this.type_last_clicked = this.element_type

                if (this.clicked_id in this.mono_clicked) {
                    delete this.mono_clicked[this.clicked_id];
                } else {
                    //console.log ("here:", this.clicked_dict, this.clicked_id)
                    this.mono_clicked[this.clicked_id] = this.clicked_dict[this.clicked_id]
                }
            } else {

                //console.log(this.clicked_dict)

                if (this.type_last_clicked == "mono") {
                    this.text_clicked = {}
                    this.mono_clicked = {}
                }
                this.type_last_clicked = this.element_type
                //console.log(this.clicked_id)
                if (this.clicked_id in this.text_clicked) {
                    delete this.text_clicked[this.clicked_id];
                } else {
                    this.text_clicked[this.clicked_id] = this.clicked_dict[this.clicked_id]
                }
            }


            return this.callback(event);
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

        this.initialize(glymagesvg.params,__element__);

    }

} // end of var NameSpace 
