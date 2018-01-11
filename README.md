# OPCUA explorer API
This project was developed for internal use at Sight Machine.  It was developed to allow easier exploration of an OPCUA server.  It allows users to search, record, and list specific as well as all tags within a specified OPCUA server.

# How To Use
To clone and run this application, you’ll need Git and an API development environment such as Postman installed on your computer.  From your command line:

Add picture

After app.py is running, open your API development environment to begin viewing each endpoint.  Changing the parameters allows you to manipulate the watchlist database and view different tags found on the OPCUA server.

Add pictures

The endpoints include:  
/watchlist  
	GET, PUT, DELETE  
/tags/listvalue  
	GET  
/tags/listvalue  
	GET  
/tags/value  
	GET  
/taghistory  
	GET,DELETE  

# License
Copyright 2018 Corinne Fahlgren
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Acknowledgements
Sight Machine.

