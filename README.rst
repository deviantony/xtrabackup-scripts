xtrabackup-scripts
==================

Repository hosting wrapper Shell scripts for the Percona Xtrabackup 2.2.x utility.

These scripts allow to create binary backups of a MySQL server 5.5 (tested under Ubuntu 12.04). 

#### Workaround for Xtrabackup 2.2.x and MySQL server <= 5.6.8

There is an issue with the Percona Xtrabackup tool 2.2.x and MySQL server <= 5.6.8.

You'll need to ensure the setting *innodb_log_file_size* is set in your MySQL configuration file otherwise Xtrabackup will fail.

See the following issue for more information: https://github.com/deviantony/xtrabackup-scripts/issues/1

#### Scripts

There are 3 scripts dedicated to backup:

* Filesystem backup : xb-backup-fs.sh
* Incremental backup : xb-backup-incremental.sh
* Streamed backup : xb-backup-stream.sh

Each of these backup scripts will require a connection to the running database server using a username and a password (optional). You can check the file *sql/create_backup_user.sql* for an example of a user definitions with the required permissions. 

And 2 scripts dedicated to backup restoration: 

* Incremental backup restoration: xb-restore-incremental.sh
* Streamed backup restoration: xb-restore-stream.sh

#### Dependencies

These scripts use others libraries contained in the _/lib_ folder:

* Bash shell function library (*bsfl*) used for logging: https://github.com/deviantony/bsfl
* Common bash library (*cbl*) provides utility methods: https://github.com/deviantony/common-bash-library 
* shFlags used to handle script parameters: https://github.com/deviantony/shflags

## Create and restore a backup archive

### Backup

Use the xb-backup-fs.sh script to create a backup of a local MySQL server. It will create a compressed archive and move it into a timestamp named folder in the specified repository. 

Example of use:

```shell
$ sudo ./xb-backup-fs.sh -r <PATH TO REPOSITORY> -u <MYSQL USER> [-p <MYSQL PASSWORD>]
```

#### Additional options
You can also specify the following options:

* --tmp-dir: Specify the temporary directory used by the script (default: */tmp/xb_backup_fs*).
* --log-file: Log file for the script (default: _/var/log/mysql/xb-backup-fs.log_).
* --backup-threads: You can specify more threads in order to backup quicker (default: 1).

### Restoration

The archive is containing a binary backup of a MySQL server, all you need to do in order to restore the backup is to extract the content of the archive in your MySQL datadir, setup the permissions for the files and start your server:

```shell
$ sudo rm -rf /path/to/mysql/datadir/*
$ sudo tar xvpzf /path/to/backup_archive.tar.gz -C /path/to/mysql/datadir
$ sudo chown -R mysql:mysql /path/to/mysql/datadir
$ sudo service mysql start
```

## Setup an incremental backup cycle

An incremental backup cycle is consisting of a full binary backup (the *base* backup) and one or more incremental backups containing only the data difference between it and the last backup.

See [Wikipedia: incremental backup][1] for more information.

### Backup

Use the xb-backup-incremental.sh script to create an incremental backup cycle.

First you'll need to take a full backup which will serve as the base backup:

```shell
$ sudo ./xb-backup-incremental.sh -r <PATH TO REPOSITORY> -u <MYSQL USER> [-p <MYSQL PASSWORD>]
```

Once the base backup is finished, a data file */opt/xb-backup/xb_incremental_cycle_data.txt* will be created, containing the following key/values:

* BASEDIR = Path to the repository where the base backup is stored 
* INCREMENTAL_STEP = Current incremental backup count 
* LAST_LSN = Log Sequence Number, used by innobackupex to know from which point the next incremental backup will be created

Now, you can start to add incremental backups to the cycle by using the *--increment* option:

```shell
$ sudo ./xb-backup-incremental.sh -r <PATH TO REPOSITORY> -u <MYSQL USER> [-p <MYSQL PASSWORD>] --increment
```

The script will read from the data file, create the incremental backup in a subfolder *INC* in the BASEDIR directory and update the data file.

Note: The data file is reset every time a base backup is created (without the *--increment* option).

#### Additional options
You can also specify the following options:

* --data-dir: Data directory where the script will store the file containing incremental backup cycle related data (default: */opt/xb-backup/*).
* --tmp-dir: Specify the temporary directory used by the script (default: */tmp/xb_backup_inc*).
* --log-file: Log file for the script (default: _/var/log/mysql/xb-backup-incremental.log_).
* --backup-threads: You can specify more threads in order to backup quicker (default: 1).

### Restoration

**WARNING**: The folder structure and the file names created by the xb-backup-incremental.sh script needs to be respected in order to restore successfully:

* TIMESTAMP_FOLDER
 *  base_archive.tar.gz
 *  INC/incremental_archive_01.tar.gz
 *  INC/incremental_archive_N.tar.gz

To restore an incremental backup, you'll need to use the xb-restore-incremental.sh the following way:

```shell
$ sudo ./xb-restore-incremental.sh -b <PATH TO BASE BACKUP> -i <PATH TO INCREMENTAL BACKUP>
```

The script will stop the MySQL service, remove all files present in MySQL datadir and import all the incremental backups up to the specified last incremental backup. 

For example, using the following parameters:

```shell
$ sudo ./xb-restore-incremental.sh -b /tmp/repo/20140518_1100/base_archive.tar.gz -i /tmp/repo/20140518_1100/INC/incremental_archive_05.tar.gz
```
The script will restore the incremental_archive_N.tar.gz from 1 to 5.

#### Additional options
You can also specify the following options:

* --data-dir: Path to MySQL datadir (default: */var/lib/mysql/*).
* --restart: Restart the MySQL service after restoration (default: false).
* --tmp-dir: Specify the temporary directory used by the script (default: */tmp/xb_backup_inc*).
* --log-file: Log file for the script (default: _/var/log/mysql/xb-restore-incremental.log_).

## Stream a backup between 2 hosts

You can directly stream the state of a local server into another MySQL server on your network using the following scripts :

* xb-backup-stream.sh on the host to backup
* xb-restore-stream.sh on the host which will receive the backup

**NOTE**: You need to start the restoration phase first.

### Restoration

The xb-restore-incremental.sh script will shutdown the MySQL service, clean the MySQL datadir and put the server in listening mode:

```shell
$ sudo ./xb-restore-stream.sh
```

#### Additional options
You can also specify the following options:

* --checksum: Use sha1sum to create a checksum and verify backup integrity (default: false).
* --data-dir: Path to MySQL datadir (default: */var/lib/mysql/*).
* --restart: Restart the MySQL service after restoration (default: false).
* --tmp-dir: Specify the temporary directory used by the script (default: */tmp/xb_backup_inc*).
* --log-file: Log file for the script (default: _/var/log/mysql/xb-restore-incremental.log_).
* --threads: You can specify more threads in order to decompress quicker (default: 1).
* --netcat-port: Port used by netcat (default: 9999).

### Backup

When the destination host is in listening mode, you can start the backup script:

```shell
$ sudo ./xb-backup-stream.sh -d <DESTINATION HOST> -u <MYSQL USER> [-p <MYSQL PASSWORD>]
```

The transfer to the DESTINATION HOST will begin directly after the script is started.

#### Additional options
You can also specify the following options:

* --checksum: Use sha1sum to send a checksum of the backup (default: false).
* --restart: Restart the MySQL service after restoration (default: false).
* --tmp-dir: Specify the temporary directory used by the script (default: */tmp/xb_backup_inc*).
* --log-file: Log file for the script (default: _/var/log/mysql/xb-restore-incremental.log_).
* --backup-threads: You can specify more threads in order to restore quicker (default: 1).
* --compress-threads: You can specify more threads in order to compress quicker (default: 1).
* --netcat-port: Port used by netcat (default: 9999).


  [1]: http://en.wikipedia.org/wiki/Incremental_backup
