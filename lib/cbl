#!/usr/bin/env bash

# (C)2013 Anthony Lapenna
# This script is provided as-is; no liability can be accepted for use.
# You are free to modify and reproduce so long as this attribution is preserved.

## ================================================
## CONSTANTS
## ================================================
_EXEC_SUCCESS=0
_EXEC_FAILURE=1

## ================================================
## METHODS
## ================================================
###################################################
# Check if the current user is root (or sudoer).
#
# Args:
#     None
# Output:
#     None
# Returns:
#     _EXEC_SUCCESS if the user has sudoer permissions.
#     _EXEC_FAILURE if the user has no sudoer permissions.
cbl_check_sudoers_permissions() {
    if [[ $UID != 0 ]]; then
	return ${_EXEC_FAILURE}
    fi
    return ${_EXEC_SUCCESS}
}

###################################################
# Check if a folder exists.
#
# Args:
#     Path to a dir.
# Output:
#     None
# Returns:
#     _EXEC_SUCCESS if the directory exists else _EXEC_FAILURE. 
cbl_dir_exists() {
    if [[ -d "$1" ]]; then
        return ${_EXEC_SUCCESS}
    fi
    return ${_EXEC_FAILURE}
}

###################################################
# Check if a file exists.
#
# Args:
#     Path to a file.
# Output:
#     None
# Returns:
#     _EXEC_SUCCESS if the file exists else _EXEC_FAILURE. 
cbl_file_exists() {
    if [[ -f "$1" ]]; then
        return ${_EXEC_SUCCESS}
    fi
    return ${_EXEC_FAILURE}
}

###################################################
# Create a directory if required.
#
# Args:
#     Directory path.
# Output:
#     None
# Returns:
#     None
cbl_create_dir() {
    if ! cbl_dir_exists "$1"; then
	mkdir -pv "$1"
    fi
}
