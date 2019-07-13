## ApiToolbox

This package is a set of basic tools I find myself using over and over again
when writing RESTful APIs using Flask.  The BaseApi provides some basic 
input / output functionality, like request parsing and loading into a custom
model object, response creation, and default exception handling for unhandled
exceptions.  The ideal use of these tools allows the developer to focus on 
the actual request processing logic and by standardizing the I/O portions of
the RESTful interface.