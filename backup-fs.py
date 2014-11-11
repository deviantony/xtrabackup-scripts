"""Xtrabackup script

Usage:
  backup-fs.py <repository> --user=<user> [--password=<pwd>] [--tmp-dir=<tmp>] [--log-file=<log>] [--backup-threads=<threads>] 
  backup-fs.py (-h | --help)
  backup-fs.py --version


Options:
  -h --help                   Show this screen.
  --version                   Show version.
  --user=<user>               MySQL user.
  --password=<pwd>            MySQL password.
  --tmp-dir=<tmp>             Temp folder [default: /tmp].
  --log-file=<log>            Log file [default: /tmp/backup.log].
  --backup-threads=<threads>  Threads count [default: 1].

"""
from docopt import docopt
import shutil
import os
import datetime
import errno
import subprocess

def mkdir_p(path, mode):
  try:
    os.makedirs(path, mode)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise
  
if __name__ == '__main__':
  arguments = docopt(__doc__, version='Naval Fate 2.0')
  print(arguments)
  
  #if not shutil.which('innobackupex'):
  #  print('innobackupex binary missing')
  #  exit(1)
  #if not  shutil.which('tar'):
  #  print('tar binary missing')
  #  exit(1)  
    
  if not os.path.exists(arguments['<repository>']):
    print ('Unable to locate backup repo: ' + arguments['<repository>'])

  if not os.path.exists(arguments['--tmp-dir']):
    os.mkdir(arguments['--tmp-dir'], 0o755)

  date = datetime.datetime.now()
  ts = date.strftime("%Y%m%d_%H%M")
  date_fmt = date.strftime("%Y%m%d")
  archive_name = 'backup_' + ts + '.tar.gz'
  archive_repository = arguments['<repository>'] + '/' + date_fmt
  archive_path = archive_repository + '/' + archive_name
  if not os.path.exists(archive_repository):
    mkdir_p(archive_repository, 0o755)

  if arguments['--password']:
    subprocess.check_call(['innobackupex', '--user=' + arguments['--user'], 
      '--password=' + arguments['--password'],
      '--parallel=' + arguments['--backup-threads'], 
      '--no-lock', 
      '--no-timestamp', 
      arguments['--tmp-dir'] + '/backup'])
  else:
    subprocess.check_call(['innobackupex', '--user=' + arguments['--user'], 
      '--parallel=' + arguments['--backup-threads'], 
      '--no-lock', 
      '--no-timestamp', 
      arguments['--tmp-dir'] + '/backup'])
  
  subprocess.check_call(['tar', 'cpfvz', arguments['--tmp-dir'] + '/backup.tar.gz', '-C', arguments['--tmp-dir'] + '/backup', '.'])

  shutil.move(arguments['--tmp-dir'] + '/backup.tar.gz', archive_path)

  shutil.rmtree(arguments['--tmp-dir'] + '/backup')