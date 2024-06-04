Penpoint Application

To run this program, make sure you have Python installed on your system.

1. Make sure the following dependencies are installed:
    pymongo
    couchbase.cluster
    couchbase.auth
    couchbase.options
    datetime
    tkinter
    base64
    uuid
    os
    requests
    traceback
    webbrowser
    math
    PIL
    io

    (you can run this in most cases to install what's needed: pip install pymongo couchbase datetime tkinter requests Pillow)

    When the program is launched correctly the terminal should say: 
	Successfully connected to MongoDB Atlas and obtained UserProfiles collection.
	C:\Users\lampc\Desktop\Penpoint Implementation\Penpoint.py:554: 
	CouchbaseDeprecationWarning: Importing ClusterOptions from couchbase.cluster is deprecated and will be removed in a future release.  
	Import ClusterOptions from couchbase.options instead.options = ClusterOptions(auth)
	Successfully connected to Couchbase.
  


   Couchbase's library malfunctions at times and when it does on launch it shows the following: 
	Successfully connected to MongoDB Atlas and obtained UserProfiles collection.
	Penpoint.py:554: CouchbaseDeprecationWarning: Importing ClusterOptions from couchbase.cluster is deprecated and will be removed in a future release.  Import ClusterOptions from 	couchbase.options instead.
  		options = ClusterOptions(auth)
	Traceback (most recent call last):
  	File "Penpoint.py", line 555, in connect_to_couchbase
    		cluster = Cluster(endpoint, options)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  	File "couchbase\cluster.py", line 101, in __init__
  	File "couchbase\logic\wrappers.py", line 98, in wrapped_fn
  	File "couchbase\logic\wrappers.py", line 82, in wrapped_fn
  	File "couchbase\cluster.py", line 107, in _connect
	couchbase.exceptions.CouchbaseException: <ec=995, category=asio.system, message=The I/O operation has been aborted because of either a thread exit or an application request., C 	Source=C:\Jenkins\workspace\python\sdk\python-packaging-pipeline\py-client\src\connection.cxx:202>
	Failed to connect to Couchbase: <ec=995, category=asio.system, message=The I/O operation has been aborted because of either a thread exit or an application request., C Source=C:	\Jenkins\workspace\python\sdk\python-packaging-pipeline\py-client\src\connection.cxx:202>


2. File Structure:
    Penpoint.py - This is the main Python script file. It's likely the entry point for your Penpoint application.
    Inside this file, you have all the code required for the Penpoint application to function. It connects to mongo and
    couchbase and runs the gui menus for the user login page and the file options.


3. How to run:
    There is an .exe file included for a click and run program, but if that malfuntions its best to move this folder to the python IDE of choice, and then run penpoint.py
    Thank you for your understanding if it malfunctions. Its hard doing everything in a team where I'm doing all the work, but because of the rules I have to make a gui which sometimes 
    doesnt work when the exe is sent elsewhere. 


