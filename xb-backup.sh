#!/bin/bash

# Script to create full, partial and incremental backups (for all databases on server) using innobackupex from Percona.
# http://www.percona.com/doc/percona-xtrabackup/innobackupex/innobackupex_script.html

# You can use this script to create 3 kinds of backups.
# - FULL: A complete backup of the server instance.
# - PARTIAL: A backup containing only a specific set of tables.
# - INCREMENTAL: A backup containing the data that have changed or are new since the last backup.
# The script allows you to send it over the network to another host (Stream) or to store it on a 
# physical drive (Hard).

# Requirements
# - Percona Xtrabackup (innobackupex): this binary is available via the Percona repositories.
# See: http://www.percona.com/doc/percona-xtrabackup/2.1/installation/apt_repo.html
# - Netcat utility
# apt-get install netcat

# Configuration
# You may need to adjust the TMP_DIR variable to specify a temporary folder of your choice.
# Specify the username/password for the MySQL backup user, adjust the BACKUP_USER & BACKUP_PASSWORD variables.

# (C)2013 Anthony Lapenna @ Workit
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.


## Configuration variables
TMP_DIR=/backup
LOG_FILE=/log/system/xtrabackup-backup.log

INNOBACKUPEX_BIN=/usr/bin/innobackupex
NETCAT_BIN=/bin/nc

BACKUP_USER=USERNAME ## TODO: UPDATE THIS VALUE
BACKUP_PASSWORD=PASSWORD ## TODO: UPDATE THIS VALUE
BACKUP_DATE=$(date +%Y%m%d)
BACKUP_DATETIME=$(date +%Y%m%d_%H%M%S)
PARALLEL_THREADS=4
TAR_OPTIONS=cpvz
NETCAT_PORT=9999

## Script variables init.
STREAM_MODE=0
HARD_MODE=0
PARTIAL_MODE=0
INCREMENTAL=0
EXTRACT_LSN=0
TABLE_DEF_FILE=0
DESTINATION_HOST=0
LSN_NUMBER=0
BACKUP_REPOSITORY_ROOT=0

## Error display
error() {
    echo "$1" 1>&2
    exit 1
}

## Logging
log() {
    echo "$(date +%Y%m%d_%H%M%S) - $1" >> ${LOG_FILE}
}

## Usage display
usage() {

    cat <<EOF

This script can be used to take 2 differents kinds of backups: STREAMED and HARD backups.

A stream backup is a network based backup, this script will stream (compressed) the backup via the network to a specific host.
The destination host must be listening to the network before starting a streamed backup (I recommend the use of the xb-restore.sh script).

A hard backup is a drived stored backup, this script will backup the server on a local directory and then compress and send it on a specific repository.

Streamed backup: `basename $0` -s <HOST> [-e] [-i <LAST LSN>] [-p <TABLE FILE>]
   -s: Streamed backup, specify the destination host.

Hard backup: `basename $0` -h <BACKUP REPOSITORY> [-e] [-i <LAST LSN>] [-p <TABLE FILE>]
   -h: Hard backup, specify the path to the distant repository. Default backup type is FULL.

Common options:
   -i: Incremental backup, specify the last LSN number. The script will create an incremental backup based on the difference between the last LSN and the actual.

   -p: Partial backup, specify the file containing the list of tables to backup. 

   -e: Extract lsn, required if you want to use a full backup as a base backup for incremental backup or if you want to add a backup to the incremental cycle.
       Enabling this option will include 2 files in the backup : XTRABACKUP_LAST_LSN.txt containing the last registered LSN number at the end of the backup and
       XTRABACKUP_BACKUP_LIST.txt including a list of backups registered in a incremental backup cycle.

Peace

EOF
    exit 0
}

## Options parsing
if [[ $# -eq 0 ]]; then
    usage
fi

while getopts ":s:h:i:p:e" opt; do
    case $opt in
	s )
	    DESTINATION_HOST=$OPTARG
	    STREAM_MODE=1;;
	h )
	    BACKUP_REPOSITORY_ROOT=$OPTARG
	    HARD_MODE=1;;
	i )
	    LSN_NUMBER=$OPTARG
	    INCREMENTAL=1;;
	p )
	    TABLE_DEF_FILE=`readlink -fn $OPTARG`
	    PARTIAL_MODE=1;;
	e )
	    EXTRACT_LSN=1;;
	\?) 
	    echo "Invalid option: -$OPTARG"
	    usage;;
	: ) 
	    echo "Option -$OPTARG requires an argument"
	    usage;;
    esac
done

shift $(($OPTIND - 1))

## Checking for pre-requisites
if [[ $UID != 0 ]]; then
    echo "This script requires sudo privileges."
    echo "sudo $0 $*"
    exit 1
fi

if [[ ! -x ${INNOBACKUPEX_BIN} ]]; then
    error "${INNOBACKUPEX_BIN} does not exist. You must install Percona Xtrabackup."
fi

if [[ ${STREAM_MODE} == 1 && ! -x ${NETCAT_BIN} ]]; then
    error "${NETCAT_BIN} does not exist. You must install netcat."
fi

if [[ ${STREAM_MODE} == 1 ]] && ! ping -qc 1 -w 3 ${DESTINATION_HOST} > /dev/null; then
    error "${DESTINATION_HOST} is not reachable."
fi

if [[ ${HARD_MODE} == 1 && ${STREAM_MODE} == 1 ]]; then
    error "Cannot use this script with both -h and -s options."
fi

if [[ ${HARD_MODE} == 0 && ${STREAM_MODE} == 0 ]]; then
    error "You must specify either stream (-s) or hard (-h) mode."
fi

if [[ ${HARD_MODE} == 1 && ! -d ${BACKUP_REPOSITORY_ROOT} ]]; then
    error "Unable to access repository : ${BACKUP_REPOSITORY_ROOT}."
fi

if [[ ${PARTIAL_MODE} == 1 && ! -f ${TABLE_DEF_FILE} ]]; then
    error "File ${TABLE_DEF_FILE} does not exist."
fi

if [[ ! -d ${TMP_DIR} ]]; then
    mkdir -pv ${TMP_DIR}
fi

## MAIN
log "Backup - START"
XB_BACKUP_OPTS="--user=${BACKUP_USER} --password=${BACKUP_PASSWORD} --parallel=${PARALLEL_THREADS} --no-lock --no-timestamp"

## PARTIAL BACKUP OPTIONS
if [[ ${PARTIAL_MODE} == 1 ]]; then
    XB_BACKUP_OPTS="${XB_BACKUP_OPTS} --tables-file=${TABLE_DEF_FILE}"
fi

## INCREMENTAL BACKUP OPTIONS
if [[ ${INCREMENTAL} == 1 ]]; then
    XB_BACKUP_OPTS="${XB_BACKUP_OPTS} --incremental --incremental-lsn=${LSN_NUMBER}"
fi

if [[ ${HARD_MODE} == 1 ]]
then
    ## HARD BACKUP MODE
    BACKUP_REPOSITORY=${BACKUP_REPOSITORY_ROOT}/${BACKUP_DATE}

    ## ARCHIVE NAME AND BACKUP REPOSITORY
    if [[ ${PARTIAL_MODE} == 1 ]]
    then
	BACKUP_FOLDER="backup_PARTIAL"
    else
	BACKUP_FOLDER="backup_FULL"
    fi

    if [[ ${INCREMENTAL} == 1 ]]
    then
	BACKUP_REPOSITORY="${BACKUP_REPOSITORY}/INC"
	BACKUP_FOLDER="${BACKUP_FOLDER}-INC"
    fi
    
    BACKUP_FOLDER="${BACKUP_FOLDER}_${BACKUP_DATETIME}"
    BACKUP_ARCHIVE="${BACKUP_FOLDER}.tar.gz"

    ## BACKUP
    ${INNOBACKUPEX_BIN} ${XB_BACKUP_OPTS} ${TMP_DIR}/${BACKUP_FOLDER}
    log "Data backup: OK"

    if [[ ${PARTIAL_MODE} == 1 ]]; then
	cp ${TABLE_DEF_FILE} ${TMP_DIR}/${BACKUP_FOLDER}/
    fi
    
    ## RETRIEVE LAST LSN
    if [[ ${EXTRACT_LSN} == 1 ]]; then
	cat ${TMP_DIR}/${BACKUP_FOLDER}/xtrabackup_checkpoints | grep "to_lsn" | sed 's/.*= \([0-9]\+\)$/\1/' > ${TMP_DIR}/XTRABACKUP_LAST_LSN.txt
	if [[ ${INCREMENTAL} == 1 ]]
	then
	    echo "INC=${BACKUP_ARCHIVE}" >> ${TMP_DIR}/XTRABACKUP_BACKUP_LIST.txt
	else
	    echo "BASE=${BACKUP_ARCHIVE}" > ${TMP_DIR}/XTRABACKUP_BACKUP_LIST.txt
	fi
	cp ${TMP_DIR}/XTRABACKUP_BACKUP_LIST.txt ${TMP_DIR}/${BACKUP_FOLDER}
	cp ${TMP_DIR}/XTRABACKUP_LAST_LSN.txt ${TMP_DIR}/${BACKUP_FOLDER}
    fi

    ## BACKUP COMPRESSION
    tar ${TAR_OPTIONS} -f ${TMP_DIR}/${BACKUP_ARCHIVE} -C ${TMP_DIR} ${BACKUP_FOLDER}
    log "Backup compression: OK"

    if [[ ! -d ${BACKUP_REPOSITORY} ]]; then
	mkdir -pv ${BACKUP_REPOSITORY}
    fi

    ## SEND BACKUP TO REPOSITORY
    mv ${TMP_DIR}/${BACKUP_ARCHIVE} ${BACKUP_REPOSITORY}/
    rm -rf ${TMP_DIR}/${BACKUP_FOLDER}
    log "Backup uploaded to repository [${BACKUP_REPOSITORY}]."

else
    ## STREAMED BACKUP MODE
    XB_STREAM_BACKUP_OPTS="--compress --compress-threads=${PARALLEL_THREADS} --stream=xbstream"
    XB_BACKUP_OPTS="${XB_BACKUP_OPTS} ${XB_STREAM_BACKUP_OPTS}"
    ${INNOBACKUPEX_BIN} ${XB_BACKUP_OPTS} ./ | ${NETCAT_BIN} ${DESTINATION_HOST} ${NETCAT_PORT}
fi

log "Backup - END"

exit 0 
