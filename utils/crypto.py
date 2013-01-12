import os
import shutil
import uuid
from utils import commons
from utils.commons import shell, AppScaleToolsException

__author__ = 'hiranya'

# When we try to ssh to other machines, we don't want to be asked
# for a password (since we always should have the right SSH key
# present), and we don't want to be asked to confirm the host's
# fingerprint, so set the options for that here.
SSH_OPTIONS = "-o NumberOfPasswordPrompts=0 -o StrictHostkeyChecking=no"

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
  status, output = commons.shell(command, status=True)
  return status is 0

def scp_file(source, destination, host, ssh_key):
  command = 'scp -i %s %s 2>&1 '\
            '%s root@%s:%s' % (ssh_key, SSH_OPTIONS, source, host, destination)
  shell(command, status=True)

def run_remote_command(command, host, ssh_key):
  remote_command = "ssh -i %s %s root@%s '%s > /dev/null " \
                   "2>&1 &' &" % (ssh_key, SSH_OPTIONS, host, command)
  shell(remote_command, status=True)

