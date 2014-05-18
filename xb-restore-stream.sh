#!/usr/bin/env bash

# (C)2013 Anthony Lapenna
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.

HELP_VERSION=2.1

## ================================================
## CONSTANTS
## ================================================
_CHECKSUM_EMIT_FILENAME=xb_stream_emit_checksum
_CHECKSUM_RECV_FILENAME=xb_stream_recv_checksum
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
DEFINE_string 'tmp-dir' '/tmp/xb_stream_restore' 'Temporary directory'
DEFINE_string 'data-dir' '/var/lib/mysql' 'MySQL server data directory' 'd'
DEFINE_string 'log-file' '/var/log/mysql/xb-restore-stream.log' 'Log file'
DEFINE_integer 'threads' 1 'Number of threads used to decompress the streamed backup' 't'
DEFINE_integer 'netcat-port' 9999 'Port used by netcat on the client side'
DEFINE_boolean 'checksum' false 'Use a checksum to verify the backup integrity'
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
_xbstream_bin=''
_netcat_bin=''
_sha1sum_bin=''

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
    _xbstream_bin=$(command -v xbstream) || bail "Could not locate xbstream binary."
    _netcat_bin=$(command -v nc) || bail "Could not locate netcat binary. You must install netcat."
    if [ ${FLAGS_checksum} -eq ${FLAGS_TRUE} ]; then
	_sha1sum_bin=$(command -v sha1sum) || bail "Could not locate sha1sum binary. You must install sha1sum."
    fi
}

###################################################
# Use netcat to receive the streamed backup and
# uncompress it with xbstream in the current folder.
#
# Args:
#     None
# Output:
#     None
# Returns:
#     None
xb_stream_recv() {
    ${_netcat_bin} -l "${FLAGS_netcat_port}" |${_xbstream_bin} -x -v -C "${FLAGS_data_dir}"
}

###################################################
# Use netcat to receive the streamed backup and
# uncompress it with xbstream in the current folder.
# Retrieve the backup checksum via netcat after the
# backup reception.
#
# Args:
#     None
# Output:
#     Error message if the checksums don't match.
# Returns:
#     None
xb_stream_recv_with_checksum() {
    ${_netcat_bin} -l "${FLAGS_netcat_port}" |tee >(${_sha1sum_bin} > "${_CHECKSUM_RECV_FILENAME}") |${_xbstream_bin} -x -v -C "${FLAGS_data_dir}"
    ${_netcat_bin} -l ${FLAGS_netcat_port} > "${_CHECKSUM_EMIT_FILENAME}"
    if [[ $(cat "${_CHECKSUM_RECV_FILENAME}") != $(cat "${_CHECKSUM_EMIT_FILENAME}") ]]; then
	msg_fail "Backup checksum don't match restoration checksum."
	exit ${_EXEC_FAILURE}
    fi 
}

###################################################
# Start innobackupex to decompress and restore
# the backup in the MySQL datadir.
#
# Args:
#     None
# Output:
#     Error message if an error occured with innobackupex.
# Returns:
#     None
xb_restore_stream() {
    local decompress_opts="--decompress --parallel=${FLAGS_threads}"
    if [[ ${FLAGS_verbose} -ge 1 ]]; then
	${_innobackupex_bin} ${decompress_opts} "${FLAGS_data_dir}" || return ${_EXEC_FAILURE}
	${_innobackupex_bin} ${_PREPARE_APPLY_OPTS} "${FLAGS_data_dir}" || return ${_EXEC_FAILURE}
    else
	${_innobackupex_bin} ${decompress_opts} "${FLAGS_data_dir}" > /dev/null 2>&1 || return ${_EXEC_FAILURE}
	${_innobackupex_bin} ${_PREPARE_APPLY_OPTS} "${FLAGS_data_dir}" > /dev/null 2>&1 || return ${_EXEC_FAILURE}
    fi
}

###################################################
# Reassign proper rights and permissions on MySQL
# datadir.
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

## ================================================
## MAIN
## ================================================
xb_start() {
    cbl_check_sudoers_permissions || bail "This script requires sudo permissions."
    xb_check_binaries
    cbl_dir_exists "${FLAGS_data_dir}" || bail "Unable to locate MySQL datadir: ${FLAGS_data_dir}"
    cbl_create_dir "${FLAGS_tmp_dir}"
    service mysql stop
    cmd "rm -rf ${FLAGS_data_dir}/*"
    msg_info "Starting backup reception." && start_watch
    if [[ ${FLAGS_checksum} -eq ${FLAGS_true} ]]; then
	xb_stream_recv_with_checksum
    else
	xb_stream_recv
    fi
    msg_info "Backup received in $(stop_watch) seconds."
    msg_info "Starting backup restoration." && start_watch
    xb_restore_stream || bail "An exception occured while trying to use innobackupex."
    msg_info "Backup restored in $(stop_watch) seconds."
    xb_set_datadir_permissions
    if [[ ${FLAGS_restart} -eq ${FLAGS_true} ]]; then
	service mysql start
    fi
    rm -rf "${FLAGS_tmp_dir}"
    exit ${_EXEC_SUCCESS}
}

xb_start
