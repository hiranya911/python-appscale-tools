from getpass import getpass
from utils import commons, cli, crypto, cloud
from utils.cloud import validate_machine_image
from utils.node_layout import NodeLayout

__author__ = 'hiranya'

def add_key_pair(options, root_password=None):
  ips = options.get(cli.OPTION_IPS)
  auto = options.get(cli.OPTION_AUTO)
  keyname = options.get(cli.OPTION_KEYNAME)

  node_layout = NodeLayout(ips)
  required_commands = [ 'ssh-keygen', 'ssh-copy-id' ]
  if auto:
    required_commands.append('expect')

  commons.assert_required_commands_exist(required_commands)
  commons.check_and_create_appscale_directory()
  path, public_key, backup_key = crypto.generate_rsa_key(keyname)

  if auto and root_password is None:
    root_password = getpass('Enter SSH password of root: ')

  ips = node_layout.get_nodes()
  for ip in ips:
    crypto.ssh_copy_id(ip, path, auto, 'sshcopyid', root_password)

  head_node = node_layout.get_head_node()
  crypto.scp_ssh_key_to_ip(head_node.id, path, public_key)
  print "A new ssh key has been generated for you and placed at %s. " \
        "You can now use this key to log into any of the machines you " \
        "specified without providing a password via the following " \
        "command:\n    ssh root@%s -i %s" % (path, head_node.id, path)

def run_instances(options):
  infrastructure = options.get(cli.OPTION_INFRASTRUCTURE)
  instance_type = options.get(cli.OPTION_INSTANCE_TYPE)
  keyname = options.get(cli.OPTION_KEYNAME)
  machine = options.get(cli.OPTION_MACHINE)

  validate_machine_image(infrastructure, machine)

  commons.check_and_create_appscale_directory()
  if infrastructure:
    print 'Starting AppScale over %s with instance '
    'type %s' % (infrastructure, instance_type)
  else:
    print 'Starting AppScale over a non-cloud environment'

  node_layout = NodeLayout(options[cli.OPTION_IPS], options)
  secret_key, secret_key_path = crypto.generate_secret_key(keyname)

  if cloud.is_valid_cloud_type(infrastructure):
    instance_info = cloud.spawn_head_node(options)
  else:
    head_node = node_layout.get_head_node()
    instance_info = ([head_node.id], [head_node.id], [None])

  head_node_ip = instance_info[0][0]

  # TODO: Find real ssh key







