#!/usr/bin/env bash

# (C)2013 Anthony Lapenna 
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.

HELP_VERSION=2.1

## ================================================
## CONSTANTS
## ================================================
_PREPARE_REDO_OPTS="--redo-only"
_PREPARE_APPLY_OPTS="--apply-log"

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
DEFINE_string 'base-backup' '' 'Base backup' 'b' 'required'
DEFINE_string 'incremental-archive' '' 'Incremental archive target' 'i' 'required'
DEFINE_string 'tmp-dir' '/tmp/xb_restore_inc' 'Temporary directory'
DEFINE_string 'data-dir' '/var/lib/mysql' 'MySQL server data directory' 'd'
DEFINE_string 'log-file' '/var/log/mysql/xb-restore-incremental.log' 'Log file'
DEFINE_boolean 'restart' false 'Restart MySQL server after backup restoration' 'r'

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
# Reassign proper rights and permissions on MySQL datadir.
#
# Args:
#     None
# Output:
#     Information messages.
# Returns:
#     None
xb_set_datadir_permissions() {
    cmd "chown -R mysql:mysql ${FLAGS_data_dir}"
    cmd "chmod 700 ${FLAGS_data_dir}"
}

###################################################
# Unarchive and prepare the base backup.
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_restore_base_backup() {
    if [[ ${FLAGS_verbose} -ge 1 ]]; then
	${_archiver_bin} -xvpzf ${FLAGS_base_backup} -C ${FLAGS_data_dir}
       	${_innobackupex_bin} ${_PREPARE_APPLY_OPTS} ${_PREPARE_REDO_OPTS} ${FLAGS_data_dir} || return ${_EXEC_FAILURE}
    else
	${_archiver_bin} -xpzf ${FLAGS_base_backup} -C ${FLAGS_data_dir}
	${_innobackupex_bin} ${_PREPARE_APPLY_OPTS} ${_PREPARE_REDO_OPTS} ${FLAGS_data_dir} > /dev/null 2>&1 || return ${_EXEC_FAILURE}
    fi
}

###################################################
# Extract and prepare an incremental archive.
# Args:
#     Path to the incremental archive.
#     Options to apply via innobackupex.
#     Path to a temporary directory.
# Output:
#     None
# Returns:
#     None
xb_restore_incremental_archive() {
    mkdir "$3"
    if [[ ${FLAGS_verbose} -ge 1 ]]; then
	${_archiver_bin} -xvpzf "$1" -C "$3"
	${_innobackupex_bin} $2 "${FLAGS_data_dir}" --incremental-dir="$3" || return ${_EXEC_FAILURE}
    else
	${_archiver_bin} -xpzf "$1" -C "$3"
	${_innobackupex_bin} $2 "${FLAGS_data_dir}" --incremental-dir="$3" > /dev/null 2>&1 || return ${_EXEC_FAILURE}
    fi
}

###################################################
# Uncompress and prepare all the incremental backups.
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_restore_incremental_archives() {
    local incremental_dir=$(dirname ${FLAGS_incremental_archive})
    local incremental_archive_name=$(basename ${FLAGS_incremental_archive})
    local incremental_step=$(echo ${incremental_archive_name} |cut -f 3 -d'_')
    local idx=1
    while [ ${idx} -le $((${incremental_step} -1)) ]
    do 
	local temp_archive_dir="${FLAGS_tmp_dir}/inc_archive_${idx}"
	xb_restore_incremental_archive "${incremental_dir}"/backup_inc_${idx}_* "${_PREPARE_APPLY_OPTS} ${_PREPARE_REDO_OPTS}" "${temp_archive_dir}" || bail "An exception occured while trying to use innobackupex."
        ((idx++))
    done
    local temp_archive_dir="${FLAGS_tmp_dir}/inc_archive_${incremental_step}"
    xb_restore_incremental_archive "${FLAGS_incremental_archive}" "${_PREPARE_APPLY_OPTS}" "${temp_archive_dir}" || bail "An exception occured while trying to use innobackupex."
}

###################################################
# Prepare the finalized backup.
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_prepare_datadir() {
    if [[ ${FLAGS_verbose} -ge 1 ]]; then
	${_innobackupex_bin} ${_PREPARE_APPLY_OPTS} ${FLAGS_data_dir}
    else
	${_innobackupex_bin} ${_PREPARE_APPLY_OPTS} ${FLAGS_data_dir} > /dev/null 2>&1
    fi
}

## ================================================
## MAIN
## ================================================
xb_start() {
    cbl_check_sudoers_permissions || bail "This script requires sudo permissions."
    xb_check_binaries
    cbl_dir_exists "${FLAGS_data_dir}" || bail "Unable to locate MySQL datadir: ${FLAGS_data_dir}"
    cbl_create_dir "${FLAGS_tmp_dir}"
    cmd "service mysql stop"
    cmd "rm -rf ${FLAGS_data_dir}/*"
    xb_restore_base_backup || bail "An exception occured while trying to use innobackupex."
    msg_ok "Base backup uncompressed and prepared."
    xb_restore_incremental_archives
    msg_ok "Incremental archives uncompressed and prepared."
    xb_prepare_datadir || bail "An exception occured while trying to use innobackupex."
    msg_ok "Datadir prepared."
    xb_set_datadir_permissions
    if [[ ${FLAGS_restart} -eq ${FLAGS_true} ]]; then
	cmd "service mysql start"
    fi
    rm -rf "${FLAGS_tmp_dir}"
    exit ${_EXEC_SUCCESS}
}

xb_start
