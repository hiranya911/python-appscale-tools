from getpass import getpass
from utils import commons
from utils.node_layout import NodeLayout

__author__ = 'hiranya'

def add_key_pair(ips, keyname, auto, root_password=None):
  node_layout = NodeLayout(ips)
  required_commands = [ 'ssh-keygen', 'ssh-copy-id' ]
  if auto:
    required_commands.append('expect')

  commons.assert_required_commands_exist(required_commands)
  commons.check_and_create_appscale_directory()
  path, public_key, backup_key = commons.generate_rsa_key(keyname)

  if auto and root_password is None:
    root_password = getpass('Enter SSH password of root: ')

  ips = node_layout.get_nodes()
  for ip in ips:
    commons.ssh_copy_id(ip, path, auto, 'sshcopyid', root_password)

  head_node = node_layout.get_head_node()
  commons.scp_ssh_key_to_ip(head_node.id, path, public_key)
  print "A new ssh key has been generated for you and placed at %s. " \
        "You can now use this key to log into any of the machines you " \
        "specified without providing a password via the following " \
        "command:\n    ssh root@%s -i %s" % (path, head_node.id, path)

