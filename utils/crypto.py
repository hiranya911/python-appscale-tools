import os
import shutil
import uuid
from utils.commons import shell, AppScaleToolsException

__author__ = 'hiranya'

def generate_rsa_key(keyname):
  path = os.path.expanduser('~/.appscale/%s' % keyname)
  backup_key = os.path.expanduser('~/.appscale/%s.key' % keyname)
  public_key = os.path.expanduser('~/.appscale/%s.pub' % keyname)

  if not os.path.exists(path) and not os.path.exists(public_key):
    print shell("ssh-keygen -t rsa -N '' -f %s" % path)

  os.chmod(path, 0600)
  os.chmod(public_key, 0600)
  shutil.copyfile(path, backup_key)
  return path, public_key, backup_key

def ssh_copy_id(ip, path, auto, expect_script, password):
  heading = '\nExecuting ssh-copy-id for host : ' + ip
  print heading
  print '=' * len(heading)

  if auto:
    command = '{%s} root@{%s} {%s} {%s}' % (expect_script, ip, path, password)
  else:
    command = 'ssh-copy-id -i {%s} root@{%s}' % (path, ip)

  status, output = shell(command, status=True)
  print output
  if not status:
    raise AppScaleToolsException('Error while executing '
                                 'ssh-copy-id on {%s}' % ip)

def scp_ssh_key_to_ip(ip, ssh_key, pub_key):
  print shell("scp -i {%s} {%s} root@{%s}:.ssh/id_dsa" % (ssh_key, ssh_key, ip))
  print shell("scp -i {%s} {%s} root@{%s}:.ssh/id_rsa.pub" % (ssh_key, pub_key, ip))

def generate_secret_key(keyname):
  path = '~/.appscale/%s.secret' % keyname
  secret_key = str(uuid.uuid4()).replace('-', '')
  full_path = os.path.expanduser(path)
  secret_file = open(full_path, 'w')
  secret_file.write(secret_key)
  secret_file.close()
  return secret_key, path
