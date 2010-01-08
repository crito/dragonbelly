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

Dragonbelly comes along as the glue to bind several open source technologies
into the result we want. It provides replication and failover capabilities.
It provides a thin layer of proxy software that translates http requests to a
load balanced webserver backend. Client requests can be either read (GET) or
(PUT) requests. In both cases the requests result in a redirect with a real
webserver address. Once a new file was created (PUT), this file is replicated
to other hosts of the webserver backend. The replication happens as a
background process.

At its core, dragonbelly provides a asynchronous, fast webserver that can
process a subset of the HTTP protocol. This daemon listens for incoming ``GET`` or
``PUT`` (?) requests. If a ``GET`` request comes in, the daemon takes the requested
path and makes a lookup in its internal state database. It calculates a path to
a real existing webserver and returns a 301 redirect status. 

If a ``PUT`` request is received by the dragonbelly daemon, it creates a new record
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

Dragonbelly implements Read and Write access to mass storage systems. The goal
of Dragonbelly is to enable certain attributes of a mass storage backends in a
webserver cluster. 

#. Implement stackable mass storage where storage units can be stacked
   to create a pool of storage backends. 
#. Controlled replication of files stored to the mass storage. This replication
   should not be limited to 2 storage units like DRBD_. Units can be added
   indefinitely in different configurations as needed. To provide simple
   fail-over and high-availability characteristics at least 2 units need to be
   implemented. 
#. The goal is to provide 0 downtime on the storage backends. The system
   administrator should be able to take whole units out, without interruption
   to the running operations. 

Dragonbelly Architecture
========================

Read
----

::

    +------+    (1) GET     +-------+   (2) Lookup   +--------+
    |Client| -------------> |Brokerd| <------------> |DomainDB|
    +------+                +-------+                +--------+
    +------+   (3) 301 Redirect |
    |Client| <------------------+
    +------+
        |     (4) GET       +---------+
        +-----------------> |Webserver|
                            +---------+

Read access to the mass storage is rather simple. A client application issues a
HTTP ``GET`` request to the Dragonbelly server. This request looks like that:

::

    GET /uploads/2009/10/17/article.jpg HTTP/1.1
    Host: www.domain.com

The ``GET`` request contains the absolute path of the file that the client wants to
request. In the HTTP header the ``Host`` field correlates with the name of the
domain that is managed by Dragonbelly.

The broker daemon (``brokerd``) does a internal lookup in its state database.
This domain database contains the whole filesystem layout where each object is
connected with meta information. In this meta attributes information about
real location of a file and several data regarding the replication and
distribution of a file is stored. 

Once the broker daemon retrieved the real locations of a file, it decides on
one location based on its load balancing algorithm and returns to the client a
HTTP 302 redirect containing the new URL.

::
    HTTP/1.1 302 Found
    Date: Fri, 08 Jan 2010 17:33:59 GMT
    Server: dragonbelly/0.1
    Content-Type: text/html; charset=UTF-8
    Content-Length: 185
    Location: http://static03.domain.com/
    Connection: close

The client follows the redirect and retrieves the file using the HTTP protocol.

Write
-----

::

    +------+    (1) PUT     +-------+   (2) Lookup   +--------+
    |Client| -------------> |Brokerd| <------------> |DomainDB|
    +------+                +-------+   (3) Ticket   +--------+
    +------+   (4) Upload Path  |                           ^
    |Client| <------------------+                           | (9) Update
    +------+                                                |
    ^ | |   (5) Upload      +---------+                     |
    | | +-----------------> |Davserver| <-+                 |
    | |                     +---------+   |                 |
    | | (6) Upload Complete   +-------+   |                 |
    | +---------------------> |Brokerd|---+ (8) Replicate --+
    +-- (8) ACK <------------ +-------+ ----> (7) Update Ticket

Write operations are due to its nature more complex than read access. 

Again a client sends a HTTP request to the Dragonbelly daemon. Probably this 
is a ``PUT`` request. For this operation the broker daemon creates a ticket in
its domain database. If its a new file or an existing file doesn't matter. The
ticket basically represents a Dragonbelly file object. Using its own load 
balancing algorithms Dragonbelly returns an upload path to the client. This 
upload path is represented using a URI. The upload ticket is included in the
HTTP response to the client.

Which upload protocol to use is variable. The primary protocol is WebDAV but a
lot of different protocols can be implemented as a plugin. The client uses the
upload ticket to perform the actual physical upload. Once the upload is
finished, a ``upload complete`` message is sent again to the broker daemon. 

Once the broker daemon updates the upload ticket, a ``ACK`` is sent to the
client and the client can finish the transaction. The broker daemon continues
with replicating the file object throughout its backends and continously
updating the domain database. 

Details regarding the replication is dependent on the configuration. Also the
role of the client is configurable.

Dragonbelly daemons can form groups and determine up-status from other hosts.
Membership and node messaging is implemented using spread. Each Dragonbelly
daemon at least joins one group. A group represents a domain and forms the
basis for the failover and replication mecahnisms.

One or more shares can be attached to each group. A share is defined as a
mapping of physical fs paths to a url. 

Simple md5 checksums are used to verify that the transfers are succesful.

Dragonbelly players
-------------------

Dragonbelly consists of several components. The following players are
identified:

#. Client
#. BrokerD
#. DomainDB
#. Webserver/Davserver

.. _Redis: http://code.google.com/p/redis/
.. _REST: http://www.ics.uci.edu/~taylor/documents/2002-REST-TOIT.pdf
.. _Django: http://www.djangoproject.org
.. _DRBD: http://www.drbd.org
