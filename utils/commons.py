import commands
import os
import shutil
import uuid

__author__ = 'hiranya'

# When we try to ssh to other machines, we don't want to be asked
# for a password (since we always should have the right SSH key
# present), and we don't want to be asked to confirm the host's
# fingerprint, so set the options for that here.
SSH_OPTIONS = "-o NumberOfPasswordPrompts=0 -o StrictHostkeyChecking=no -o ConnectTimeout=4"

class AppScaleToolsException(Exception):
  def __init__(self, msg, code=0):
    Exception.__init__(self, msg)
    self.code = code

def assert_commands_exist(commands):
  for command in commands:
    available = shell('which %s' % command)
    if not available:
      msg = 'Required command %s not available' % command
      raise AppScaleToolsException(msg)

def shell(command, status=False):
  if status:
    return commands.getstatusoutput(command)
  else:
    return commands.getoutput(command)

def diff(list1, list2):
  """
  Returns the list of entries that are present in list1 but not
  in list2.

  Args:
    list1 A list of elements
    list2 Another list of elements

  Returns:
    A list of elements unique to list1
  """
  return sorted(set(list1) - set(list2))

def flatten(obj):
  if isinstance(obj, str):
    return [ obj ]
  elif isinstance(obj, list):
    output = []
    for item in obj:
      output += flatten(item)
    return output
  else:
    msg = 'Object of type %s cannot be flattened' % type(obj)
    raise AppScaleToolsException(msg)

def generate_rsa_key(dir, keyname):
  private_key = os.path.join(dir, keyname)
  backup_key = os.path.join(dir, keyname + '.key')
  public_key = os.path.join(dir, keyname + '.pub')

  if not os.path.exists(private_key) and not os.path.exists(public_key):
    print shell("ssh-keygen -t rsa -N '' -f %s" % private_key)

  os.chmod(private_key, 0600)
  os.chmod(public_key, 0600)
  shutil.copyfile(private_key, backup_key)
  return private_key, public_key, backup_key

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
    msg = 'Error while executing ssh-copy-id on %s' % ip
    raise AppScaleToolsException(msg)

def generate_secret_key(path):
  secret_key = str(uuid.uuid4()).replace('-', '')
  full_path = os.path.expanduser(path)
  secret_file = open(full_path, 'w')
  secret_file.write(secret_key)
  secret_file.close()
  return secret_key

def is_ssh_key_valid(ssh_key, host):
  command = "ssh -i %s %s 2>&1 root@%s 'touch /tmp/foo'; "\
            "echo $? " % (ssh_key, SSH_OPTIONS, host)
  status, output = shell(command, status=True)
  return status is 0 and output == '0'

def scp_file(source, destination, host, ssh_key):
  command = 'scp -i %s %s 2>&1 '\
            '%s root@%s:%s' % (ssh_key, SSH_OPTIONS, source, host, destination)
  shell(command, status=True)

def run_remote_command(command, host, ssh_key):
  remote_command = "ssh -i %s %s root@%s '%s > /dev/null "\
                   "2>&1 &'" % (ssh_key, SSH_OPTIONS, host, command)
  shell(remote_command, status=True)

