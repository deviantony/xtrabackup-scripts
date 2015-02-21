.. -*- restructuredtext -*-

============

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/deviantony/xtrabackup-scripts
   :target: https://gitter.im/deviantony/xtrabackup-scripts?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
pyxtrabackup
============

``pyxtrabackup`` is a Python wrapper for the Percona Xtrabackup utility, see `official homepage <http://www.percona.com/software/percona-xtrabackup>`_.

The tool allows you to take full and incremental backups using Xtrabackup.

Installation
============

Use ``pip`` to install it::

   $ pip install pyxtrabackup

Full backup and restoration
===========================

Backup
------

This tool can be used to create a backup of a local MySQL server. It will create a a compressed archive and move it into a timestamp named folder in the specified repository.

You will need a MySQL user with the appropriate permissions to create the backup, check the ``sql`` folder on the git repository for an example.

Example of use::

$ pyxtrabackup <PATH TO REPOSITORY> --user=<MYSQL USER> [ --password=<MYSQL PASSWORD> ]

Usage in a cron file::

@midnight    mysql    /usr/local/bin/pyxtrabackup /mnt/myrepo --user=backup-user --password=changeme

Additional options
^^^^^^^^^^^^^^^^^^

You can also specify the following options:

* --tmp-dir: Specify the temporary directory used by the script. (default: */tmp*).
* --log-file: Log file for the script (default: */var/log/mysql/pyxtrabackup.log*).
* --out-file: Log file for innobackupex output (default: */var/log/mysql/xtrabackup.out*).
* --backup-threads: You can specify more threads in order to backup quicker (default: 1).


Restoration
-----------

The archive is containing a binary backup of a MySQL server, all you need to do in order to restore the backup is to extract the content of the archive in your MySQL datadir, setup the permissions for the files and start your server:

::

$ sudo rm -rf /path/to/mysql/datadir/*
$ sudo tar xvpzf /path/to/backup_archive.tar.gz -C /path/to/mysql/datadir
$ sudo chown -R mysql:mysql /path/to/mysql/datadir
$ sudo service mysql start

Setup an incremental backup cycle
=================================

An incremental backup cycle is consisting of a full binary backup (the base backup) and one or more incremental backups containing only the data difference between it and the last backup.

See `Wikipedia incremental backup`_ for more information.

Backup
------

Use the *pyxtrabackup-inc* binary to create an incremental backup cycle.

First you'll need to take a full backup which will serve as the base backup: ::

$ pyxtrabackup-inc <PATH TO REPOSITORY> --user=<MYSQL USER> [ --password=<MYSQL PASSWORD> ]

Now, you can start to add incremental backups to the cycle by using the *--incremental* option: ::

$ pyxtrabackup-inc <PATH TO REPOSITORY> --incremental --user=<MYSQL USER> [ --password=<MYSQL PASSWORD> ]

NOTE: The cycle will be reset every time a base backup is created (without the *--incremental* option).

Additional options
^^^^^^^^^^^^^^^^^^

You can also specify the following options:

* --tmp-dir: Specify the temporary directory used by the script. (default: */tmp*).
* --log-file: Log file for the script (default: */var/log/mysql/pyxtrabackup-inc.log*).
* --out-file: Log file for innobackupex output (default: */var/log/mysql/xtrabackup.out*).
* --backup-threads: You can specify more threads in order to backup quicker (default: 1).


Restoration
-----------

*WARNING*: The folder structure and the file names created by the *pyxtrabackup-inc* binary needs to be respected in order to restore successfully:

 *  TIMESTAMP_FOLDER/INC/base_backup_DATETIME.tar.gz
 *  TIMESTAMP_FOLDER/INC/inc_1_backup_DATETIME.tar.gz
 *  TIMESTAMP_FOLDER/INC/inc_N_backup_DATETIME.tar.gzz

To restore an incremental backup, you'll need to use the *pyxtrabackup-restore* binary the following way: ::

$ pyxtrabackup-restore --base-archive=<PATH TO BASE BACKUP> --incremental-archive=<PATH TO INCREMENTAL BACKUP> --user=<MYSQL USER>

The binary will stop the MySQL service, remove all files present in MySQL datadir and import all the incremental backups up to the specified last incremental backup.

For example, using the following parameters: ::

$ pyxtrabackup-restore --base-archive=/tmp/repo/20140518/INC/base_backup_20140518_1700.tar.gz --incremental-archive=/tmp/repo/20140518/INC/inc_backup_5_20140518_2200.gz --user=backup-user

The script will restore the inc_N_backup_DATETIME.tar.gz from 1 to 5.

Additional options
^^^^^^^^^^^^^^^^^^

You can also specify the following options:

* --data-dir: MySQL datadir. (default: */var/lib/mysql*)
* --restart: Restart the MySQL service after restoration.
* --tmp-dir: Specify the temporary directory used by the script. (default: */tmp*).
* --log-file: Log file for the script (default: */var/log/mysql/pyxtrabackup-restore.log*).
* --out-file: Log file for innobackupex output (default: */var/log/mysql/xtrabackup.out*).
* --backup-threads: You can specify more threads in order to backup quicker (default: 1).

Limitations
===========

This tool supports the following versions of Percona Xtrabackup:

* 2.2.x

It has been tested on the following OSes:

* Ubuntu 12.04
* Ubuntu 14.04

It has been tested against the following MySQL versions:

* 5.5

It has been tested against the following Python versions:

* Python 3.4

.. _Wikipedia incremental backup: http://en.wikipedia.org/wiki/Incremental_backup