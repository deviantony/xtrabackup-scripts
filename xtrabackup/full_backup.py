"""Xtrabackup script

Usage:
    pyxtrabackup <repository> --user=<user> [options]
    pyxtrabackup (-h | --help)
    pyxtrabackup --version


Options:
    -h --help                   \
    Show this screen.
    -d --debug                  \
    Enable verbose error
    --version                   \
    Show version.
    --user=<user>               \
    MySQL user.
    --password=<pwd>            \
    MySQL password.
    --tmp-dir=<tmp>             \
    Temporary directory [default: /tmp].
    --log-file=<log>            \
    Log file [default: /var/log/mysql/pyxtrabackup.log].
    --out-file=<log>            \
    Output file [default: /var/log/mysql/xtrabackup.out].
    --backup-threads=<threads>  \
    Threads count [default: 1].
    --no-compress               \
    Do not create a compressed archive of the backup.
    --webhook=<url>             \
    Webhook post backup. If enable will post backup information in JSON format.

"""
from docopt import docopt
import sys
import logging
from xtrabackup.backup_tools import BackupTool


def main():
    arguments = docopt(__doc__, version='3.1.6')
    try:
        backup_tool = BackupTool(
            arguments['--log-file'], arguments['--out-file'],
            arguments['--no-compress'], arguments['--debug'])

        backup_tool.start_full_backup(arguments['<repository>'],
                                      arguments['--tmp-dir'],
                                      arguments['--user'],
                                      arguments['--password'],
                                      arguments['--backup-threads'],
                                      arguments['--webhook'])
    except Exception:
        logger = logging.getLogger(__name__)
        logger.error("pyxtrabackup failed.", exc_info=arguments['--debug'])
        exit(1)
    exit(0)


if __name__ == '__main__':
    sys.exit(main())
