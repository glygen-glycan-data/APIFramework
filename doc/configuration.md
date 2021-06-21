# Parameters

## Basic
Basic parameters are not application specific.
* host 
    * type: String
    * default value: localhost
    * usage: indicate the host for FLASK
    
* port:
    * type: Int
    * default value: 10980
    * usage: indicate the port for FLASK
    
* max_cpu_core:
    * type: Int
    * default value: 1
    * usage: Maximum amount of daemon processes
    
* app_name:
    * type: String
    * default value: Testing
    * usage: indicate the name for FLASK
    
* file_based_job:
    * type: Boolean
    * default value: False
    * usage: indicate the the type of application, is processing user-uploaded file part of the application?
    
* clean_start:
    * type: Boolean
    * default value: True
    * usage: initialize the instance with no prior knowledge of previous run
    
* status_saving_location:
    * type: String
    * default value: None
    * usage: indicate the path for where the status should be loaded and saved
    
* input_file_folder:
    * type: String
    * default value: None
    * usage: location for saving user-uploaded file 
    
* allowed_file_ext:
    * type: String
    * default value: txt, pdf, doc, docx
    * usage: allowed file extension of user-uploaded file
    
* template_folder:
    * type: String
    * default value: None
    * usage: indicate the template folder for FLASK
    
* home_page:
    * type: String
    * default value: None
    * usage: home page for your web-based API
    
* file_upload_finished_page:
    * type: String
    * default value: None
    * usage: the web page when user finished uploading the file for your web-based API
    



## App specific
Parameters here will be processed as key-value pairs and pass it to worker function as variable params.
The section name must be the same as basic.app_name

