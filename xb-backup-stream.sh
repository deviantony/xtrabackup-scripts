#!/usr/bin/env bash

# (C)2013 Anthony Lapenna 
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.

HELP_VERSION=2.1

## ================================================
## CONSTANTS
## ================================================
_CHECKSUM_FILENAME=xb_stream_checksum

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
DEFINE_string 'tmp-dir' '/tmp/xb_backup_stream' 'Temporary directory'
DEFINE_string 'log-file' '/var/log/mysql/xb-backup-stream.log' 'Log file'
DEFINE_integer 'backup-threads' 1 'Number of threads used to backup'
DEFINE_integer 'compress-threads' 1 'Number of threads used to compress the backup'
DEFINE_integer 'netcat-port' 9999 'Port used by netcat on the client side'
DEFINE_string 'mysql-user' '' 'MySQL user account for the backup creation' 'u' 'required' 
DEFINE_string 'mysql-passwd' '' 'MySQL password for the backup creation' 'p' 
DEFINE_string 'destination-host' '' 'Hostname or IP address of the client' 'd' 'required'
DEFINE_boolean 'checksum' false 'Use a checksum to verify the backup integrity.'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

## BSFL variables
LOG_ENABLED=y
LOG_FILE=${FLAGS_log_file}

## ================================================
## GLOBAL VARIABLES
## ================================================
_innobackupex_bin=''
_netcat_bin=''
_sha1sum_bin=''
_xb_backup_opts=''

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
    _netcat_bin=$(command -v nc) || bail "Could not locate netcat binary. You must install netcat."
    if [ ${FLAGS_checksum} -eq ${FLAGS_TRUE} ]; then
	_sha1sum_bin=$(command -v sha1sum) || bail "Could not locate sha1sum binary. You must install sha1sum."
    fi
}

###################################################
# Check if the distant host is accessible via
# network.
#
# Args:
#     None
# Output:
#     An error message if the ping command failed.
# Returns:
#     None
xb_check_destination_client() {
    if ! ping -qc 1 -w 3 "${FLAGS_destination_host}" > /dev/null; then
	msg_fail "Unable to reach destination host: ${FLAGS_destination_host}."
	exit ${_EXEC_FAILURE}
    fi
}

###################################################
# Prepare the _xb_backup_opts variable with the required
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
    local xb_stream_backup_opts="--compress --compress-threads=${FLAGS_compress_threads} --stream=xbstream"
    _xb_backup_opts="${_xb_backup_opts} ${xb_stream_backup_opts}"
}

###################################################
# Start the innobackupex binary to stream a backup to 
# the destination host via netcat. Can stream a checksum
# if required.
#
# Args:
#     None
# Output:
#     Error message if an error occured with innobackupex.
# Returns:
#     None
xb_stream_backup() {
    if [[ ${FLAGS_checksum} -eq ${FLAGS_true} ]]; then
	${_innobackupex_bin} ${_xb_backup_opts} ./ |tee >(${_sha1sum_bin} > "${FLAGS_tmp_dir}/${_CHECKSUM_FILENAME}") |${_netcat_bin} "${FLAGS_destination_host}" "${FLAGS_netcat_port}"
	bail "Unable to stream backup to the destination client."
	msg_info "Streaming checksum."
	cat "${FLAGS_tmp_dir}/${_CHECKSUM_FILENAME}" |${_netcat_bin} "${FLAGS_destination_host}" "${FLAGS_netcat_port}"
    else
	${_innobackupex_bin} ${_xb_backup_opts} ./ |${_netcat_bin} "${FLAGS_destination_host}" "${FLAGS_netcat_port}"
	bail "Unable to stream backup to the destination client."
    fi
}

## ================================================
## MAIN
## ================================================
xb_start() {
    cbl_check_sudoers_permissions || bail "This script requires sudo permissions."
    xb_check_binaries
    xb_check_destination_client
    cbl_create_dir "${FLAGS_tmp_dir}"
    xb_prepare_bkp_opts
    msg_info "Starting stream backup." && start_watch
    xb_stream_backup
    msg_info "Backup streamed in $(stop_watch) seconds."
    rm -rf "${FLAGS_tmp_dir}"
    exit ${_EXEC_SUCCESS}
}

xb_start
