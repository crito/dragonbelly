===========
Dragonbelly
===========

What is Dragonbelly
===================

Dragonbelly is:

#. A daemon that can be queried for an upload and download path to content
   stored on a storage backend
#. An API that can be queried from a client to retrieve information about
   files stored in the backend
#. A mechanism of replication that can guarentee certain aspects of files
   stored on the backend

Dragonbelly consists of several applications that together can perform the
problem of providing a replicated, distributed and stackable mass storage to a
high available web cluster. It tries so by reusing as many existing open source
application as possible.

At its core, dragonbelly provides a asynchronous, fast webserver that can
process a subset of the HTTP protocol. This daemon listens for incoming GET or
PUT(?) requests. If a GET request comes in, the daemon takes the requested
path and makes a lookup in its internal state database. It calculates a path to
a real existing webserver and returns a 302 redirect status. 

If a PUT request is received by the dragonbelly daemon, it creates a new record
in its internal database and returns a 302 to an existing webserver that can
handle a DAV upload or other means of a file storage. This file can have
several attributes attached. The state of this file and its attributes are
saved in no-sql db, eg: Redis_.

A replication process takes care that in the background that a file gets replicated
throughout the available storage backends. A file can be replicated X times
depending on its file type. Or a file can be marked with different per file
attributes that differ from the set defaults.

For the dragonbelly daemon to work it provides a REST_ API that can be used by
clients. The goal is that dragonbelly can be seamlessly integrated into
existing web application frameworks. For the web developer should be no
overhead involved to make use of this storage system. This can be reached by
using plugins, eg: a middleware for Django_. 

Dragonbelly Architecture
========================

.. _Redis: http://code.google.com/p/redis/
.. _REST: http://www.ics.uci.edu/~taylor/documents/2002-REST-TOIT.pdf
.. _Django: http://www.djangoproject.org
