import commands
import os
import shutil

__author__ = 'hiranya'

class AppScaleToolsException(Exception):
  def __init__(self, msg):
    Exception.__init__(self, msg)

def assert_required_commands_exist(commands):
  for command in commands:
    available = shell('which %s' % command)
    if not available:
      raise AppScaleToolsException('Required command %s not available '
                                   'in path' % command)

def check_and_create_appscale_directory():
  appscale_dir = os.path.expanduser("~/.appscale")
  if not os.path.exists(appscale_dir):
    os.mkdir(appscale_dir)

def shell(command, status=False):
  if status:
    return commands.getstatusoutput(command)
  else:
    return commands.getoutput(command)

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

def flatten(obj):
  if isinstance(obj, str):
    return [ obj ]
  elif isinstance(obj, list):
    output = []
    for item in obj:
      output += flatten(item)
    return output
  else:
    raise AppScaleToolsException('Object of type %s cannot be '
                                 'flattened' % type(obj))
