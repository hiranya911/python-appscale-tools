import getpass
import os
from utils import commons, crypto, cli, cloud
from utils.commons import AppScaleToolsException
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

def run_instances(infrastructure, machine, instance_type, ips, database, min,
                  max, keyname, group, scp, replication, read_q, write_q):
  appscale_dir = os.path.expanduser(APPSCALE_DIR)
  if not os.path.exists(appscale_dir):
    os.mkdir(appscale_dir)

  if infrastructure:
    print 'Starting AppScale over', infrastructure
  else:
    print 'Starting AppScale in a non-cloud environment'

  options = {
    cli.OPTION_INFRASTRUCTURE : infrastructure,
    cli.OPTION_DATABASE : database,
    cli.OPTION_MIN_IMAGES : min,
    cli.OPTION_MAX_IMAGES : max,
    cli.OPTION_REPLICATION : replication,
    cli.OPTION_READ_FACTOR : read_q,
    cli.OPTION_WRITE_FACTOR : write_q
  }
  node_layout = NodeLayout(ips, options)

  secret_key_file = os.path.join(APPSCALE_DIR, keyname + '.secret')
  secret_key = crypto.generate_secret_key(secret_key_file)

  if cloud.is_valid_cloud_type(infrastructure):
    cloud.configure_security(infrastructure, keyname, group, appscale_dir)
    instance_info = cloud.spawn_head_node(infrastructure, keyname,
      group, machine, instance_type)
    head_node = instance_info[0][0]
  else:
    head_node = node_layout.get_head_node()

  named_key_loc = os.path.join(appscale_dir, keyname + '.key')
  named_backup_key_loc = os.path.join(appscale_dir, keyname + '.private')
  ssh_key = None
  for key in (named_key_loc, named_backup_key_loc):
    if crypto.is_ssh_key_valid(key, head_node.id):
      ssh_key = key
      break
  if ssh_key is None:
    raise AppScaleToolsException('Unable to find a SSH key to login to AppScale nodes')

  # TODO: Ensure image is AppScale

  if scp is not None:
    print 'Copying over local copy of AppScale from', scp
    # TODO: scp code

  crypto.scp_file(ssh_key, '/root/.appscale/%s.key' % keyname,
    head_node.id, ssh_key)

  # TODO: generate AppScale credentials

  print 'Head node successfully initialized at', head_node.id

  # TODO: copy keys

  crypto.scp_file('resources/controller.god', '/tmp/controller.god',
    head_node.id, ssh_key)
  crypto.run_remote_command('god load /tmp/controller.god', head_node.id, ssh_key)
  crypto.run_remote_command('god start controller', head_node.id, ssh_key)

  # TODO: Create AppController client

