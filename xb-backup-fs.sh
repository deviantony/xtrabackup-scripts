#!/usr/bin/env bash

# (C)2013 Anthony Lapenna
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.

HELP_VERSION=2.1

## ================================================
## CONSTANTS
## ================================================
_ARCHIVE_EXTENSION="tar.gz"

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
DEFINE_string 'backup-repository' '' 'Repository to store the backup archive' 'r' 'required'
DEFINE_string 'mysql-user' '' 'MySQL user account for the backup creation' 'u' 'required' 
DEFINE_string 'mysql-passwd' '' 'MySQL password for the backup creation' 'p'
DEFINE_string 'tmp-dir' '/tmp/xb_backup_fs' 'Temporary directory'
DEFINE_string 'log-file' '/var/log/mysql/xb-backup-fs.log' 'Log file'
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
_xb_prepare_opts=''
_archive_path=''

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
# Prepare the _xb_backup_opts & xb_prepare_opts variable 
# with the required options for the backup.
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
    _xb_prepare_opts="--apply-log"
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
    local datestamp=$(date +%Y%m%d)
    local timestamp=$(date +%Y%m%d_%H%M)
    local archive_name="backup_${timestamp}.${_ARCHIVE_EXTENSION}"
    local archive_repository="${FLAGS_backup_repository}/${datestamp}"
    if ! cbl_dir_exists "${archive_repository}"; then
	cmd "mkdir -pv ${archive_repository}"
    fi
    _xb_archive_path="${archive_repository}/${archive_name}"
}

###################################################
# Create the backup and prepare it.
#
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_fs_backup() {	    
    if [[ ${FLAGS_verbose} -ge 1 ]]; then
	${_innobackupex_bin} ${_xb_backup_opts} "${FLAGS_tmp_dir}/backup" || return ${_EXEC_FAILURE}
	${_innobackupex_bin} ${_xb_prepare_opts} "${FLAGS_tmp_dir}/backup" || return ${_EXEC_FAILURE}
    else
	${_innobackupex_bin} ${_xb_backup_opts} "${FLAGS_tmp_dir}/backup" > /dev/null 2>&1 || return ${_EXEC_FAILURE}
	${_innobackupex_bin} ${_xb_prepare_opts} "${FLAGS_tmp_dir}/backup" > /dev/null 2>&1 || return ${_EXEC_FAILURE}
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
	${_archiver_bin} -cpvzf "${FLAGS_tmp_dir}/backup.tar.gz" -C "${FLAGS_tmp_dir}/backup" . || return ${_EXEC_FAILURE}
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
    cbl_dir_exists "${FLAGS_backup_repository}" || bail "Unable to locate backup repository: ${FLAGS_backup_repository}"
    cbl_create_dir "${FLAGS_tmp_dir}"
    xb_prepare_bkp_opts
    xb_prepare_archive_path
    msg_info "Starting fs backup." && start_watch
    xb_fs_backup || bail "An exception occured while trying to use innobackupex."
    msg_info "Backup done in $(stop_watch) seconds."
    msg_info "Starting backup compression." && start_watch
    xb_archive_backup || bail "An exception occured while trying to archive the backup."
    msg_info "Backup archived in $(stop_watch) seconds."
    rm -rf "${FLAGS_tmp_dir}"
    exit ${_EXEC_SUCCESS}
}

xb_start
