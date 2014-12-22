"""Xtrabackup script

Usage:
    pyxtrabackup <repository> --user=<user> [--password=<pwd>] [--tmp-dir=<tmp>] [--log-file=<log>] [--err-file=<log>] [--backup-threads=<threads>] 
    pyxtrabackup (-h | --help)
    pyxtrabackup --version


Options:
    -h --help                   Show this screen.
    --version                   Show version.
    --user=<user>               MySQL user.
    --password=<pwd>            MySQL password.
    --tmp-dir=<tmp>             Temporary directory [default: /tmp].
    --log-file=<log>            Log file [default: /var/log/pyxtrabackup.log].
    --err-file=<log>            Error file [default: /var/log/pyxtrabackup.err].    
    --backup-threads=<threads>  Threads count [default: 1].

"""
from docopt import docopt
import sys
import logging
from xtrabackup.backup_tools import BackupTool


def main():
    arguments = docopt(__doc__, version='1.0')
    backup_tool = BackupTool(arguments['--log-file'], arguments['--err-file'])
    try:
        backup_tool.start_full_backup(arguments['<repository>'],
                                      arguments['--tmp-dir'],
                                      arguments['--user'],
                                      arguments['--password'],
                                      arguments['--backup-threads'])
    except Exception:
        logger = logging.getLogger(__name__)
        logger.error("pyxtrabackup failed.")
        exit(1)
    exit(0)


if __name__ == '__main__':
    sys.exit(main())
