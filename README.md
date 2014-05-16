xtrabackup-scripts
==================

Repository hosting wrapper scripts for the Percona Xtrabackup utility.

These scripts allows to create binary backup of a MySQL server. 

There is 3 scripts dedicated to backup:

* Filesystem backup : xb-backup-fs.sh
* Incremental backup : xb-backup-incremental.sh
* Streamed backup : xb-backup-stream.sh

And 2 scripts dedicated to backup restoration: 

* Incremental backup restoration: xb-restore-incremental.sh
* Streamed backup restoration: xb-restore-stream.sh

## BACKUP-FS

This script is used to backup a MySQL server, it will create a compressed archive and move it into a specific repository. Use it the following way:

```
$ sudo ./xb-backup-fs.sh -r <PATH TO REPOSITORY> -u <MYSQL USER>
```

You can add the *-p* option to specify a password for the backup user if required. You can also specify the following options:

* --tmp-dir: Specify the temporary directory used by the script (default: /tmp/xb_backup_fs).
* --log-file: The file where the script will print messages (default: _/var/log/mysql/xb-backup-fs.log_).
* --backup-threads: You can specify more threads in order to backup quickly (default: 1).

## BACKUP-INCREMENTAL

Description coming soon...
