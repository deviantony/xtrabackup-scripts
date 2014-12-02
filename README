.. -*- restructuredtext -*-

============
pyxtrabackup
============

``pyxtrabackup`` is a Python wrapper for the Percona Xtrabackup utility, see `official homepage <http://www.percona.com/software/percona-xtrabackup>`_.


Installation
============

Use ``pip`` to install it::

   $ pip install pyxtrabackup

Usage
=====

Backup
------

This tool can be used to create a backuo of a local MySQL server. It will create a a compressed archive and move it into a timestamp named folder in the specified repository.

Example of use::

$ pyxtrabackup <PATH TO REPOSITORY> --user=<MYSQL USER> [ --password=<MYSQL PASSWORD> ]

Additional options
^^^^^^^^^^^^^^^^^^

You can also specify the following options:

* --tmp-dir: Specify the temporary directory used by the script. (default: */tmp*).
* --log-file: Log file for the script (default: */var/log/pyxtrabackup.log*).
* --backup-threads: You can specify more threads in order to backup quicker (default: 1).


Restoration
-----------

The archive is containing a binary backup of a MySQL server, all you need to do in order to restore the backup is to extract the content of the archive in your MySQL datadir, setup the permissions for the files and start your server:

::

$ sudo rm -rf /path/to/mysql/datadir/*
$ sudo tar xvpzf /path/to/backup_archive.tar.gz -C /path/to/mysql/datadir
$ sudo chown -R mysql:mysql /path/to/mysql/datadir
$ sudo service mysql start

Limitations
===========

This tool supports the following versions of Percona Xtrabackup:

* 2.2.x

It has been tested on the following OSes:

* Ubuntu 12.04
* Ubuntu 14.04

It has been tested against the following MySQL versions:

* 5.5
