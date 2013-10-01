xtrabackup-scripts
==================

Repository hosting wrapper scripts for the Percona Xtrabackup utility.


The 2 scripts *xb-backup.sh* and *xb-restore.sh* are wrappers script of the Percona innobackupex utility.

The backup script allows to take backups of a MySQL server. There is 3 kinds of backup :

* Full backup : contains all the server data.
* Partial backup : contains all the data of a specific set of tables.
* Incremental backup : contains only the data of the files that have changed or are new since the last backup.

You can use this script to store the backup as a compressed archive into a specific repository on the filesystem (*HARD* backup) or to transfer it directly to another host on the network (*STREAMED* backup).

## Data backup

Use of the script *xb-backup.sh*

### Hard backup

In order to take a hard backup, you have to use the script in the following way :

```
sudo ./xb-backup.sh -h <DISTANT REPOSITORY>
```

This will take a backup of the database, compress it and move it into a specific folder in <DISTANT REPOSITORY> specified as parameter. The folder which will host the archive will be created in the <DISTANT REPOSITORY> using the day date as name (YYYmmDD format).


### Streamed backup

In order to backup a server and transfer its data to another host on the network, use the following command :

WARNING: The host must be listening to the network before you use the backup script. Check the use of the restoration script (*xb-restore.sh*) for more informations.

```
sudo ./xb-backup.sh -s <HOST_ADDRESS>
```

### Common options

A set of common options is available to HARD/STREAMED backup.

* -p : Partial backup option.

You can use this option and specify a file containing a list of tables to backup as parameter.

Hard backup:

```
sudo ./xb-backup.sh -h <DISTANT REPOSITORY> -p <TABLE_FILE>
```

Streamed backup:

```
sudo ./xb-backup.sh -s <HOST ADDRESS> -p <TABLE_FILE>
```

* -e : Extract LSN.

You can use this option to extract the last LSN value of the server into a temporary file. This file is called *XTRABACKUP_LAST_LSN.txt* and will be stored in the *TMP_DIR* variable folder.


* -i : Take an incremental backup.

You can use this option in order to take an incremental backup. You'll need to specify the last LSN value from which you want to take the incremental backup as a parameter.


For a hard backup:

```
sudo ./xb-backup.sh -h <DISTANT REPOSITORY> -i <LAST LSN VALUE>
```

## Data restoration

In order to restore a specific backup archive or to listen to the network for the backup reception, you can use a specific script *xb-restore.sh*.

Note: The restoration script will stop the MySQL service and clean the MYSQL_DATA_DIR (erasing all data in it).

### Hard backup restoration

You can use the script in the following way to restore a backup (FULL/PARTIAL) from a compressed archive:

```
sudo ./xb-restore.sh -h <PATH TO THE COMPRESSED BACKUP>
```

The script will retrieve the archive, uncompress it in the *TMP_DIR* variable folder (check that you've got enough space for it) and apply it onto the server.

In order to restore a server from an incremental backup archive, you must specify the *-i* option:

```
sudo ./xb-restore.sh -ih <PATH TO THE COMPRESSED BACKUP>
```

The script will use the extra data contained in the incremental backup archive in order to restore all the incremental cycle.

### Streamed backup restoration

You can use the script with the *-s* option to put the server into listening mode:

```
sudo ./xb-restore.sh -s
```

You can now start the streamed backup onto the server you want to backup using the *xb-backup.sh* script.

## Misc

Additional informations for the proper use of these scripts.

### Set up an incremental backup cycle

In order to set up a proper incremental backup cycle using these scripts, follow the following procedure:

First, you need to take a full/partial backup which will serve as BASE for the next incremental backups:

```
sudo ./xb-backup.sh -eh <DISTANT REPOSITORY>
```

This command will take a full backup of the server and extract the last LSN value into the file *XTRABACKUP_LAST_LSN.txt*, which will be stored in the *TMP_DIR* variable folder.

Next, you can take one or more incremental backup using the following command:

```
sudo ./xb-backup.sh -eh <DISTANT REPOSITORY> -i `cat TMP_DIR/XTRABACKUP_LAST_LSN.txt`
```

It will create an incremental backup based on the last LSN value (overwritten by every backup using the -e option) and store it into the <DISTANT REPOSITORY>/YYYYmmDD/INC folder. The INC folder is created in order to facilitate the backup restoration.

The archive will also contains to extra files: a copy of the XTRABACKUP_LAST_LSN.txt file and another file call XTRABACKUP_BACKUP_LIST.txt which contains the order of the incremental backup cycle (from base to last incremental).


### Replication

After the restoration phasis, a file *xtrabackup_binlog_pos_innodb* will appear in the *MYSQL_DATA_DIR*, it contains the last binlog file used by the server and its position. 
Use these as replication information if you want to set up the new server as a slave.
