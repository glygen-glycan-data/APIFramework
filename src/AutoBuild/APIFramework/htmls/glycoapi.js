"use strict";

/**
 * Base framework for interacting with Glyomics web services.
 * Handles configuration, submission, retrieval, and polling logic.
 * * @param {Object} options - Configuration options (baseurl, developer_email, delay, timeout).
 */
function APIFramework(options = {}) {

    this.ServiceBaseURL = options.baseurl !== undefined ? options.baseurl : this.ServicePublicURL;
    this.UserEmail = options.developer_email !== undefined ? options.developer_email : "";
    this.delay = options.delay !== undefined ? options.delay : 1; // delay between retrieve requests
    this.timeout = options.timeout !== undefined ? options.timeout : 0; // how long retrieve should wait for the job to finish
    this.nocache = options.nocache !== undefined ? options.nocache : false;

    /**
     * Explicitly sets the base URL for the web service requests.
     * * @param {string} url - The base URL to use.
     */
    this.set_service_url = function (url){
        this.ServiceBaseURL = url;
    }

    /**
     * Reverts the service URL to the default public endpoint for this specific service.
     */
    this.use_public_service_url = function (){
        this.ServiceBaseURL = this.ServicePublicURL;
    }

    /**
     * Dynamically sets the service URL based on the browser's current window location.
     */
    this.use_current_service_url = function (){

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

    /**
     * Sets the developer email required for authentication and tracking.
     * * @param {string} email - The developer's email address.
     */
    this.set_developer_email = function (email){
        this.UserEmail = email;
    }

    /**
     * Sets the default delay (in seconds) between polling attempts.
     * * @param {number} delay - Time in seconds.
     */
    this.set_delay = function (delay){
        this.delay = delay;
    }

    /**
     * Sets the default timeout (in seconds) for how long the retrieve request should wait.
     * * @param {number} timeout - Time in seconds.
     */
    this.set_timeout = function (timeout){
        this.timeout = timeout;
    }

    this.set_nocache = function() {
        this.nocache = true;
    }

    this.unset_nocache = function() {
        this.nocache = false;
    }

    /**
     * Validates and submits multiple tasks to the web service backend.
     * * @param {Array<Object>} tasks - An array of task parameter objects.
     * @param {boolean} [return_objects=false] - If true, returns full objects {id, incache} instead of string IDs.
     * @returns {Promise<Array<string>|Array<Object>>} - A promise that resolves to an array of assigned task IDs or objects.
     */
    this.submit_many = async function (tasks, return_objects = false) {

        for (let task of tasks) {
            this.parameter_check(task);
        }
        
        if (this.UserEmail == ""){
            throw new Error("Please provide your email")
        }
        let url = this.ServiceBaseURL + "/submit";
        let data = {
            "tasks": JSON.stringify(tasks),
            "developer_email": this.UserEmail
        };
        if (this.nocache) {
            data["nocache"] = "true";
        }

        const response = await fetch(url, {
            method: 'POST',
            body: new URLSearchParams(data)
        });

        // Parse as text first to catch the plain text error message, otherwise parse as JSON
        const text = await response.text();
        if (text === "Please submit with actual tasks" || text === '"Please submit with actual tasks"') {
            throw "Empty parameter";
        }
        
        const d = JSON.parse(text);
        
        // Return full objects if requested, otherwise maintain backwards compatibility by returning just IDs
        return return_objects ? d : d.map(res => res.id);
    }

    /**
     * Validates and submits a single task to the web service backend.
     * * @param {Object} task - The task parameter object.
     * @param {boolean} [return_object=false] - If true, returns full object {id, incache} instead of a string ID.
     * @returns {Promise<string|Object>} - A promise that resolves to the assigned task ID or object.
     */
    this.submit = async function (task, return_object = false) {
        let results = await this.submit_many([task], return_object);
        return results[0];
    }

    /**
     * Retrieves the current processing status and results for multiple task IDs.
     * * @param {Array<string>} tids - An array of task IDs to check.
     * @param {number} [timeout] - Optional specific timeout for this retrieval.
     * @returns {Promise<Array<Object>>} - A promise resolving to an array of result objects.
     */
    this.retrieve_many = async function (tids, timeout) {
        let url = this.ServiceBaseURL + "/retrieve";

        let data = {
            "task_ids": JSON.stringify(tids),
        };
        timeout = (timeout !== undefined ? timeout : this.timeout)
        if (timeout > 0) {
            data.timeout = timeout
        }

        const response = await fetch(url, {
            method: 'POST',
            body: new URLSearchParams(data)
        });
        
        return await response.json();
    }

    /**
     * Retrieves the current processing status and results for a single task ID.
     * * @param {string} tid - The task ID to check.
     * @param {number} [timeout] - Optional specific timeout for this retrieval.
     * @returns {Promise<Object>} - A promise resolving to the result object.
     */
    this.retrieve = async function (tid, timeout) {
        let results = await this.retrieve_many([tid], timeout);
        return results[0];
    }

    /**
     * End-to-end execution flow for multiple tasks. Handles submission, continuous polling, 
     * and callbacks until all tasks are fully processed.
     * * @param {Array<Object>} tasks - An array of task parameter objects.
     * @param {Object} [options] - Optional configurations overrides (delay, timeout, callbacks, explicit task_ids).
     * @returns {Promise<Array<Object>>} - A promise resolving to an array of completed result objects.
     */
    this.request_many = async function (tasks, options = {}) {
        // Destructure the properties you want, leaving them undefined if not provided
        let { delay, timeout, submit_callback, retrieve_callback, task_ids, task_id } = options;

        let active_tids = [];
        let incache_flags = [];

        // If task_ids are provided in options, we bypass submission, but still get polling
        if (task_ids !== undefined && task_ids.length > 0) {
            active_tids = [...task_ids];
            // Since we are resuming existing tasks, we want to retrieve immediately,
            // so we pretend they are cached to bypass the initial delay.
            incache_flags = active_tids.map(() => true);
        } else {
            // Internally ask for full objects so we can read the `incache` property
            let submit_results = await this.submit_many(tasks, true);
            active_tids = submit_results.map(res => res.id);
            incache_flags = submit_results.map(res => !!res.incache);
            
            // Fire the submit callback before entering the retrieve loop
            if (submit_callback !== undefined) {
                submit_callback(active_tids, incache_flags);
            }
        }
        
        let original_tids = [...active_tids];
        let final_results = {};
        let start = Date.now();
        let attempts = 0;
        
        let actual_delay = delay !== undefined ? delay : this.delay;
        let actual_timeout = timeout !== undefined ? timeout : this.timeout;

        // Check if ALL tasks are in the cache.
        // If ANY task needs computation (i.e., not all cached), wait for the initial delay 
        // before making the first retrieve attempt to avoid a wasted API call.
        let all_cached = incache_flags.every(flag => flag);
        if (!all_cached && active_tids.length > 0 && actual_delay > 0) {
            await new Promise(resolve => setTimeout(resolve, 1000 * actual_delay));
        }

        while (active_tids.length > 0) {
            let results = await this.retrieve_many(active_tids, actual_timeout);
            attempts++;
            
            let next_active_tids = [];
            for (let i = 0; i < results.length; i++) {
                let res = results[i];
                let tid = res.id;
                final_results[tid] = res;
                
                if (!res.finished) {
                    next_active_tids.push(tid);
                }
            }
            active_tids = next_active_tids;

            if (active_tids.length === 0) {
                break;
            }
            
            if (retrieve_callback !== undefined) {
                let cb_result = retrieve_callback((Date.now() - start)/1000, attempts);
                if (cb_result === false) {
                    break;
                } else if (typeof cb_result === 'number') {
                    actual_delay = cb_result;
                } else if (typeof cb_result === 'object' && cb_result !== null) {
                    if (cb_result.delay !== undefined) actual_delay = cb_result.delay;
                    if (cb_result.timeout !== undefined) actual_timeout = cb_result.timeout;
                }
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000 * actual_delay));
        }

        return original_tids.map(tid => final_results[tid]);
    }

    /**
     * End-to-end execution flow for a single task. Handles submission and continuous polling 
     * until the task is complete.
     * * @param {Object} task - The task parameter object.
     * @param {Object} [options] - Optional configurations overrides (delay, timeout, callbacks).
     * @returns {Promise<Object>} - A promise resolving to the completed result object.
     */
    this.request = async function (task, options = {}) {
        let tasks = task ? [task] : [];
        if (options.task_id !== undefined) {
            options.task_ids = [ task_id ];
            delete options.task_id;
        }
        let results = await this.request_many(tasks, options);
        return results[0];
    }

    /**
     * Abstract method used by derived classes to validate tasks before submission.
     * * @param {Object} task - The task to validate.
     */
    this.parameter_check = function (task) {
        // check before sending it to service backend
    }
    
}

/**
 * Service wrapper for the Glylookup application.
 * * @param {Object} [options] - Framework configuration options.
 */
function Glylookup (options = {}) {
    this.ServicePublicURL = "https://glylookup.glyomics.org";
    APIFramework.call(this, options);

    /**
     * Validates that the necessary parameters for Glylookup exist.
     * * @param {Object} task - The task object.
     * @throws {Error} If 'seq' is missing.
     */
    this.parameter_check = function (task) {

        if ( !Object.keys(task).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

/**
 * Service wrapper for the MotifMatch application.
 * * @param {Object} [options] - Framework configuration options.
 */
function MotifMatch (options = {}) {
    this.ServicePublicURL = "https://motifmatch.glyomics.org";
    APIFramework.call(this, options);

    /**
     * Validates that the necessary parameters for MotifMatch exist.
     * * @param {Object} task - The task object.
     * @throws {Error} If 'seq' is missing.
     */
    this.parameter_check = function (task) {

        if ( !Object.keys(task).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

/**
 * Service wrapper for the Substructure application.
 * * @param {Object} [options] - Framework configuration options.
 */
function Substructure (options = {}) {
    this.ServicePublicURL = "https://substructure.glyomics.org";
    APIFramework.call(this, options);

    /**
     * Validates that the necessary parameters for Substructure exist.
     * * @param {Object} task - The task object.
     * @throws {Error} If 'seq' is missing.
     */
    this.parameter_check = function (task) {

        if ( !Object.keys(task).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

/**
 * Service wrapper for the Subsumption application.
 * * @param {Object} [options] - Framework configuration options.
 */
function Subsumption (options = {}) {
    this.ServicePublicURL = "https://subsumption.glyomics.org";
    APIFramework.call(this, options);

    /**
     * Validates that the necessary parameters for Subsumption exist.
     * * @param {Object} task - The task object.
     * @throws {Error} If 'seq' is missing.
     */
    this.parameter_check = function (task) {

        if ( !Object.keys(task).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}

/**
 * Service wrapper for the Converter application.
 * * @param {Object} [options] - Framework configuration options.
 */
function Converter (options = {}) {
    this.ServicePublicURL = "https://converter.glyomics.org";
    APIFramework.call(this, options);

    /**
     * Validates that the necessary parameters for Converter exist.
     * * @param {Object} task - The task object.
     * @throws {Error} If 'seq' or 'format' are missing.
     */
    this.parameter_check = function (task) {

        if ( !Object.keys(task).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

        if ( !Object.keys(task).includes("format") ){
            throw new Error("Please provide desired format")
        }

    }
}

/**
 * Service wrapper for the Glymage application (image generation).
 * * @param {Object} [options] - Framework configuration options.
 */
function Glymage (options = {}) {
    this.ServicePublicURL = "https://glymage.glyomics.org";
    APIFramework.call(this, options);

    /**
     * Validates that the necessary parameters for Glymage exist.
     * * @param {Object} task - The task object.
     * @throws {Error} If both 'seq' and 'acc' are missing.
     */
    this.parameter_check = function (task) {

        if ( !Object.keys(task).includes("seq") && !Object.keys(task).includes("acc") ){
            throw new Error("Please provide glycan sequence or accession")
        }

    };

    /**
     * Submits an image task and returns the endpoint URL for the generated image.
     * * @param {Object} task - The task object.
     * @returns {Promise<string>} - Resolves to the endpoint URL to retrieve the image.
     */
    this.get_image_url = async function (task) {
        let tid = await this.submit(task);
        return this.ServiceBaseURL + "/getimage?task_id=" + tid;
    };

    /**
     * Updates matching DOM elements to directly display precomputed images by accession ID.
     * * @param {string} selector - CSS selector for the target `<img>` element(s).
     * @param {Object} params - Image parameters (acc, display, image_format).
     */
    this.set_precomputed_image_url = async function(selector,params) {
        let imgelts = document.querySelectorAll(selector);
        for (let imgelt of imgelts) {
            imgelt.src = this.precomputed_image_url(params);
        }
    };

    this.precomputed_image_url = function(params) {
        let imgdis = params.display || "extended";
        let imgfmt = params.image_format || "png";
        return this.ServiceBaseURL + '/image/snfg/' + imgdis + '/' + params.acc + "." + imgfmt;
    };

    /**
     * Automatically triggers image generation and updates matching DOM elements once complete.
     * * @param {string} selector - CSS selector for the target `<img>` element(s).
     * @param {Object} params - The task configuration for the image to be generated.
     */
    this.set_on_demand_image_url = async function(selector,params) {
        this.get_image_url(params).then((url) => {
           let imgelts = document.querySelectorAll(selector);
           for (let imgelt of imgelts) {
               imgelt.src = url;
           }
        });
    };
}

/**
 * Service wrapper for the Register application.
 * * @param {Object} [options] - Framework configuration options.
 */
function Register (options = {}) {
    this.ServicePublicURL = "https://register.glyomics.org/";
    APIFramework.call(this, options);

    /**
     * Validates that the necessary parameters for the Register service exist.
     * * @param {Object} task - The task object.
     * @throws {Error} If 'seq' is missing.
     */
    this.parameter_check = function (task) {

        if ( !Object.keys(task).includes("seq") ){
            throw new Error("Please provide glycan sequence")
        }

    }
}
