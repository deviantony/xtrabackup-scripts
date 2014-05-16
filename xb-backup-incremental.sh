#!/usr/bin/env bash

# (C)2013 Anthony Lapenna 
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.

HELP_VERSION=2.1

## ================================================
## CONSTANTS
## ================================================
_ARCHIVE_EXTENSION="tar.gz"
_CYCLE_DATA_FILENAME="xb_incremental_cycle_data.txt"
_CYCLE_BASEDIR_KEY="BASEDIR"
_CYCLE_INC_STEP_KEY="INCREMENTAL_STEP"
_CYCLE_LAST_LSN_KEY="LAST_LSN"

## ================================================
## LIBRARIES
## ================================================
SHFLAGS_LIB_PATH=./lib/shflags
BSFL_LIB_PATH=./lib/bsfl
CBL_LIB_PATH=./lib/cbl

source ${CBL_LIB_PATH}
if [[ $? -ne 0 ]]; then   
    echo "Unable to source cbl library: ${CBL_LIB_PATH}"
    exit ${_EXEC_FAILURE}
fi

source ${BSFL_LIB_PATH}
if [[ $? -ne 0 ]]; then   
    echo "Unable to source bsfl library: ${BSFL_LIB_PATH}"
    exit ${_EXEC_FAILURE}
fi

source ${SHFLAGS_LIB_PATH}
if [[ $? -ne 0 ]]; then
    echo "Unable to source shFlags library: ${SHFLAGS_LIB_PATH}"
    exit ${_EXEC_FAILURE}
fi

## ================================================
## FLAGS
## ================================================
DEFINE_string 'cycle-repository' '' 'Repository to store the incremental backup cycle' 'r' 'required'
DEFINE_boolean 'increment' false 'Add an incremental backup in the backup cycle' 'i'
DEFINE_string 'mysql-user' '' 'MySQL user account for the backup creation' 'u' 'required' 
DEFINE_string 'mysql-passwd' '' 'MySQL password for the backup creation' 'p'
DEFINE_string 'tmp-dir' '/tmp/xb_backup_inc' 'Temporary directory'
DEFINE_string 'data-dir' '/opt/xb-backup/' 'Data directory to store the incremental backup cycle data' 'd'
DEFINE_string 'log-file' '/var/log/mysql/xb-backup-incremental.log' 'Log file'
DEFINE_integer 'backup-threads' 1 'Number of threads used to backup'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

## BSFL variables
LOG_ENABLED=y
LOG_FILE=${FLAGS_log_file}

## ================================================
## GLOBAL VARIABLES
## ================================================
_innobackupex_bin=''
_archiver_bin=''
_xb_backup_opts=''
_archive_path=''
_archive_base_dir=''
_cycle_last_lsn=''
_incremental_step=0

## ================================================
## METHODS
## ================================================
###################################################
# Check if the required binaries are installed.
#
# Args:
#     None
# Output:
#     Error messages for each missing binary.
# Returns:
#     None
xb_check_binaries() {
    _innobackupex_bin=$(command -v innobackupex) || bail "Could not locate innobackupex binary. You must install Percona Xtrabackup."
    _archiver_bin=$(command -v tar) || bail "Could not locate tar binary. You must install tar."
}

###################################################
# Create the data file required for the cycle.
#
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_create_data_file() {
    _cycle_last_lsn=$(grep "to_lsn" "${FLAGS_tmp_dir}/backup/xtrabackup_checkpoints" |cut -d'=' -f2 |sed 's/^ *//')
    if [[ ${_incremental_step} -eq 0 ]]; then
	_incremental_step=1
    else
	((_incremental_step++))
    fi
    local cycle_data_file="${FLAGS_data_dir}/${_CYCLE_DATA_FILENAME}"
    echo "${_CYCLE_BASEDIR_KEY}=${_archive_base_dir}" > "${cycle_data_file}"
    echo "${_CYCLE_LAST_LSN_KEY}=${_cycle_last_lsn}" >> "${cycle_data_file}"
    echo "${_CYCLE_INC_STEP_KEY}=${_incremental_step}" >> "${cycle_data_file}"
}

###################################################
# Retrieve the cycle data from DATADIR/_CYCLE_DATA_FILENAME.
#
# Args:
#     None
# Output:
#     Information message for directory cleaning.
# Returns:
#     None
xb_retrieve_cycle_data() {	    
    local cycle_data_file="${FLAGS_data_dir}/${_CYCLE_DATA_FILENAME}"
    if ! cbl_file_exists "${cycle_data_file}"; then
	msg_fail "Unable to locate the cycle data file: ${cycle_data_file}"
	exit ${_EXEC_FAILURE}
    fi
    _cycle_last_lsn=$(grep "${_CYCLE_LAST_LSN_KEY}" "${cycle_data_file}"| cut -d'=' -f2)
    _incremental_step=$(grep "${_CYCLE_INC_STEP_KEY}" "${cycle_data_file}"| cut -d'=' -f2)
    _archive_base_dir=$(grep "${_CYCLE_BASEDIR_KEY}" "${cycle_data_file}"| cut -d'=' -f2)
}

###################################################
# Prepare the _xb_backup_opts with the required 
# options for the backup.
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_prepare_bkp_opts() {
    _xb_backup_opts="--user=${FLAGS_mysql_user} --parallel=${FLAGS_backup_threads} --no-lock --no-timestamp"
    if [[ ${FLAGS_mysql_passwd} != "" ]]; then
	_xb_backup_opts="${_xb_backup_opts} --password=${FLAGS_mysql_passwd}"
    fi
    if [[ ${FLAGS_increment} -eq ${FLAGS_true} ]]; then
	_xb_backup_opts="${_xb_backup_opts} --incremental --incremental-lsn=${_cycle_last_lsn}"
    fi
}

###################################################
# Prepare the archive absolute path.
#
# Args:
#     None
# Output:
#     Information on repository sub directory creation.
# Returns:
#     None
xb_prepare_archive_path() {
    local timestamp=$(date +%Y%m%d_%H%M)    
    local archive_repository="${FLAGS_cycle_repository}/${timestamp}"
    if [[ ${FLAGS_increment} -eq ${FLAGS_true} ]]; then
	local archive_name="backup_inc_${_incremental_step}_${timestamp}.${_ARCHIVE_EXTENSION}"
	local archive_repository="${_archive_base_dir}/INC"
    else
	local archive_name="backup_base_${timestamp}.${_ARCHIVE_EXTENSION}"
	_archive_base_dir="${archive_repository}"
    fi
    if ! cbl_dir_exists ${archive_repository}; then
	cmd "mkdir -pv ${archive_repository}"
    fi
    _xb_archive_path="${archive_repository}/${archive_name}"
}

###################################################
# Create the backup.
#
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_incremental_backup() {	    
    if [[ ${FLAGS_verbose} -ge 1 ]]; then
	${_innobackupex_bin} ${_xb_backup_opts} "${FLAGS_tmp_dir}/backup" || return ${_EXEC_FAILURE}
    else
	${_innobackupex_bin} ${_xb_backup_opts} "${FLAGS_tmp_dir}/backup" > /dev/null 2>&1 || return ${_EXEC_FAILURE}
    fi
}


###################################################
# Create the compressed backup archive and send it
# to the backup repository.
#
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_archive_backup() {	    
    if [[ ${FLAGS_verbose} -ge 1 ]]; then
	${_archiver_bin} -cvpzf "${FLAGS_tmp_dir}/backup.tar.gz" -C "${FLAGS_tmp_dir}/backup" . || return ${_EXEC_FAILURE}
    else
	${_archiver_bin} -cpzf "${FLAGS_tmp_dir}/backup.tar.gz" -C "${FLAGS_tmp_dir}/backup" . || return ${_EXEC_FAILURE}
    fi
    mv "${FLAGS_tmp_dir}/backup.tar.gz" "${_xb_archive_path}"
}

## ================================================
## MAIN
## ================================================
xb_start() {
    cbl_check_sudoers_permissions || bail "This script requires sudo permissions."
    xb_check_binaries
    cbl_dir_exists "${FLAGS_cycle_repository}" || bail "Unable to locate cycle repository: ${FLAGS_cycle_repository}"
    if [[ ${FLAGS_increment} -eq ${FLAGS_true} ]]; then
	xb_retrieve_cycle_data
	cbl_dir_exists "${_archive_base_dir}" || bail "Unable to locate backup base directory: ${_archive_base_dir}"
    else
	cbl_create_dir "${FLAGS_data_dir}"
    fi
    cbl_create_dir "${FLAGS_tmp_dir}"
    xb_prepare_bkp_opts
    xb_prepare_archive_path
    if [[ ${FLAGS_increment} -eq ${FLAGS_true} ]]; then
	msg_info "Starting incremental backup." && start_watch
    else
	msg_info "Starting base backup." && start_watch
    fi
    xb_incremental_backup || bail "An exception occured while trying to use innobackupex."
    msg_info "Backup done in $(stop_watch) seconds."
    xb_create_data_file
    msg_info "Archiving backup." && start_watch
    xb_archive_backup || bail "An exception occured while trying to archive the backup."
    msg_info "Backup archived in $(stop_watch) seconds."
    rm -rf "${FLAGS_tmp_dir}"
    exit ${_EXEC_SUCCESS}
}

xb_start
