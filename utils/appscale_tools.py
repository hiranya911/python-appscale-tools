import getpass
import os
from utils import commons, crypto
from utils.node_layout import NodeLayout

__author__ = 'hiranya'

APPSCALE_DIR = '~/.appscale'

def add_key_pair(ips, keyname, auto=False, root_password=None):
  node_layout = NodeLayout(ips)

  required_commands = [ 'ssh-keygen', 'ssh-copy-id' ]
  if auto:
    required_commands.append('expect')
  commons.assert_commands_exist(required_commands)

  appscale_dir = os.path.expanduser(APPSCALE_DIR)
  if not os.path.exists(appscale_dir):
    os.mkdir(appscale_dir)
  key_info = crypto.generate_rsa_key(appscale_dir, keyname)
  pvt_key = key_info[0]
  public_key = key_info[1]

  if auto and root_password is None:
    root_password = getpass.getpass('Enter SSH password of root: ')

  for node in node_layout.nodes:
    crypto.ssh_copy_id(node.id, pvt_key, auto, 'sshcopyid', root_password)

  head_node = node_layout.get_head_node()
  crypto.scp_file(pvt_key, '~/.ssh/id_dsa', head_node.ip, pvt_key)
  crypto.scp_file(public_key, '~/.ssh/id_rsa.pub', head_node.ip, pvt_key)

  print 'A new ssh key has been generated for you and placed at %s. ' \
        'You can now use this key to log into any of the machines you ' \
        'specified without providing a password via the following ' \
        'command:\n    ssh root@%s -i %s' % (pvt_key, head_node.id, pvt_key)

def run_instances():
  pass

