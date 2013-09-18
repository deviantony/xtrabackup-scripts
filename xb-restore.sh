#!/bin/bash

# Script to recover full, partial and incremental backups done using innobackupex from Percona.
# http://www.percona.com/doc/percona-xtrabackup/innobackupex/innobackupex_script.html

# You can use this script to restore a backup stored on a physical drive (compressed backup)
# or to prepare a host for a stream backup by listening to the network.

# Requirements
# - Percona Xtrabackup (innobackupex): this binary is available via the Percona repositories.
# See: http://www.percona.com/doc/percona-xtrabackup/2.1/installation/apt_repo.html
# - Netcat utility
# apt-get install netcat
# - QPress: this binary is available via the Percona repositories.

# Configuration
# You may need to adjust the TMP_DIR variable to specify a temporary folder of your choice.
# You may also need to adjust the MYSQL_DATA_DIR variable.

# (C)2013 Anthony Lapenna @ Workit
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.

## Configuration variables
TMP_DIR=/backup
MYSQL_DATA_DIR=/data/mysql
LOG_FILE=/log/system/xtrabackup-restore.log

INNOBACKUPEX_BIN=/usr/bin/innobackupex
NETCAT_BIN=/bin/nc
QPRESS_BIN=/usr/bin/qpress

BACKUP_DATE=$(date +%Y%m%d)
BACKUP_DATETIME=$(date +%Y%m%d_%H%M%S)
PARALLEL_THREADS=4
NETCAT_PORT=9999

## Script variables init.
STREAM_MODE=0
HARD_MODE=0
PARTIAL_MODE=0
INCREMENTAL=0
COMPRESSED_BACKUP_PATH=0

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

This script can be used to restore 2 differents kinds of backups: STREAMED and HARD backups.
A stream backup is a network based backup, this script will prepare to receive a streamed backup from another host.
A hard backup is a drived stored backup, this script will retrieve the backup in a local dir, uncompress it and install it.

Streamed backup: `basename $0` -s 
   -s: Streamed backup reception.

Hard backup: `basename $0` -h <COMPRESSED BACKUP PATH> [-i]
   -h: Restoration of a hard backup. You must specify the path to the compressed backup.
   -i: Specify the backup as incremental. It will read from the XTRABACKUP_BACKUP_LIST.txt in its root in order to restore the full backup.

Peace

EOF
    exit 0
}

## Options parsing
if [[ $# -eq 0 ]]; then
    usage
fi

while getopts ":h:si" opt; do
    case $opt in
	s )
	    STREAM_MODE=1;;
	h )
	    HARD_MODE=1
	    COMPRESSED_BACKUP_PATH=$OPTARG;;
	i )
	    INCREMENTAL=1;;
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

if [[ ${STREAM_MODE} == 1 && ! -x ${QPRESS_BIN} ]]; then
    error "${QPRESS_BIN} does not exist. You must install qpress."
fi

if [[ ${HARD_MODE} == 1 && ${STREAM_MODE} == 1 ]]; then
    error "Cannot use this script with both -h and -s options."
fi

if [[ ${HARD_MODE} == 0 && ${STREAM_MODE} == 0 ]]; then
    error "You must specify either stream (-s) or hard (-h) mode."
fi

if [[ ${HARD_MODE} == 1 && ! -f ${COMPRESSED_BACKUP_PATH} ]]; then
    error "Backup file does not exist: ${COMPRESSED_BACKUP_PATH}."
fi

if [[ ! -d ${TMP_DIR} ]]; then
    mkdir -pv ${TMP_DIR}
fi

## MAIN
log "Restoration - START"
service mysql stop
rm -rf ${MYSQL_DATA_DIR}/*

if [[ ${HARD_MODE} == 1 ]]
then
    ## HARD RESTORATION
    if [[ ${INCREMENTAL} == 1 ]]
    then
	# INCREMENTAL BACKUP RESTORATION
	BACKUP_ARCHIVE_NAME=$(basename "${COMPRESSED_BACKUP_PATH}")
	BACKUP_ARCHIVED_FOLDER="${BACKUP_ARCHIVE_NAME%%.*}"
	tar --strip-components=1 -xpvz -f ${COMPRESSED_BACKUP_PATH} -C ${TMP_DIR} ${BACKUP_ARCHIVED_FOLDER}/XTRABACKUP_BACKUP_LIST.txt

	REPOSITORY_ROOT=`echo "${COMPRESSED_BACKUP_PATH}" | sed 's/\(.*[0-9]\)\/.*$/\1/'`
	echo "ROOT IS: ${REPOSITORY_ROOT}"

	for BACKUP_ARCHIVE in `cat ${TMP_DIR}/XTRABACKUP_BACKUP_LIST.txt | sed 's/.*=\(.*\)$/\1/'`
	do
	    if [[ "${BACKUP_ARCHIVE}" == *_FULL_* || "${BACKUP_ARCHIVE}" == *_PARTIAL_* ]] 
	    then
		# BASE BACKUP
		if [[ ! -f ${REPOSITORY_ROOT}/${BACKUP_ARCHIVE} ]]; then
		    echo "Could not locate base backup ${REPOSITORY_ROOT}/${BACKUP_ARCHIVE} for incremental restoration. Aborting."
		    exit 1
		    
		fi
		tar --strip-components=1 -xpvz -f ${REPOSITORY_ROOT}/${BACKUP_ARCHIVE} -C ${MYSQL_DATA_DIR}
		log "Incremental - Base backup [${BACKUP_ARCHIVE}] - Decompression: OK."
		
		XB_PREPARE_OPTS="--apply-log --redo-only"
		${INNOBACKUPEX_BIN} ${XB_PREPARE_OPTS} ${MYSQL_DATA_DIR}
		log "Incremental - Base backup [${BACKUP_ARCHIVE}] - Preparation: OK."
	    else
		# INC BACKUP
		if [[ ! -f ${REPOSITORY_ROOT}/INC/${BACKUP_ARCHIVE} ]]; then
		    echo "Could not locate incremental backup ${REPOSITORY_ROOT}/INC/${BACKUP_ARCHIVE} for incremental restoration. Aborting."
		    exit 1
		fi
		tar -xpvz -f ${REPOSITORY_ROOT}/INC/${BACKUP_ARCHIVE} -C ${TMP_DIR}
		CURRENT_INC_BACKUP_PATH=`find ${TMP_DIR}/ -maxdepth 1 -type d | sort -nr | head -1`

		if [[ "${BACKUP_ARCHIVE}" == ${BACKUP_ARCHIVE_NAME} ]]
		then
		    ## LIMIT INC
		    XB_PREPARE_OPTS="--apply-log"
		    ${INNOBACKUPEX_BIN} ${XB_PREPARE_OPTS} ${MYSQL_DATA_DIR} --incremental-dir=${CURRENT_INC_BACKUP_PATH}
		    log "Incremental - Final incremental [${CURRENT_INC_BACKUP_PATH}] - Preparation: OK."
		    break
		else
		    ## INTERMED. INC
		    XB_PREPARE_OPTS="--apply-log --redo-only"
		    ${INNOBACKUPEX_BIN} ${XB_PREPARE_OPTS} ${MYSQL_DATA_DIR} --incremental-dir=${CURRENT_INC_BACKUP_PATH}
		    log "Incremental - Intermediate incremental backup [${CURRENT_INC_BACKUP_PATH}] - Preparation: OK."
		fi
	    fi
	done
    else
	# FULL/PARTIAL BACKUP DECOMPRESSION
	tar --strip-components=1 -xpvz -f ${COMPRESSED_BACKUP_PATH} -C ${MYSQL_DATA_DIR}
	log "Backup decompression: OK."
    fi
else
    ## STREAM RESTORATION
    echo "Network listening..."
    cd ${MYSQL_DATA_DIR}
    ${NETCAT_BIN} -l ${NETCAT_PORT} | xbstream -x -v

    XB_DECOMPRESS_OPTS="--decompress --parallel=${PARALLEL_THREADS}"
    ${INNOBACKUPEX_BIN} ${XB_DECOMPRESS_OPTS} ${MYSQL_DATA_DIR}
fi

# FINAL BACKUP PREPARATION
XB_PREPARE_OPTS="--apply-log"
${INNOBACKUPEX_BIN} ${XB_PREPARE_OPTS} ${MYSQL_DATA_DIR}
log "Final backup preparation: OK."

# MYSQL DATA DIR PERMISSIONS
chown -R mysql:mysql ${MYSQL_DATA_DIR}
chmod 700 ${MYSQL_DATA_DIR}

# Removing TEMPORARY CONTENT
rm -rf ${TMP_DIR}/*

exit 0
