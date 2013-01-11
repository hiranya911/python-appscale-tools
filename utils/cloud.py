from datetime import datetime
import os
import boto
import time
from utils import cli, commons
from utils.commons import AppScaleToolsException

__author__ = 'hiranya'

class CloudAgent:
  def spawn_vms(self, count, options):
    raise NotImplemented

  def describe_instances(self, keyname):
    raise NotImplemented

  def validate_machine_image(self, machine):
    raise NotImplemented

class EC2Agent(CloudAgent):
  def __init__(self):
    self.image_id_prefix = 'ami-'

  def spawn_vms(self, count, options):
    key_name = options[cli.OPTION_KEYNAME]
    group_name = options[cli.OPTION_GROUP]
    image_id = options[cli.OPTION_MACHINE]
    instance_type = options[cli.OPTION_INSTANCE_TYPE]

    conn = self.open_connection()

    groups = conn.get_all_security_groups()
    group_exists = False
    for group in groups:
      if group.name == group_name:
        group_exists = True
        break
    if not group_exists:
      conn.create_security_group(group_name,
        'AppScale security group')
      conn.authorize_security_group(group_name, from_port=1,
        to_port=65535, ip_protocol='udp')
      conn.authorize_security_group(group_name, from_port=1,
        to_port=65535, ip_protocol='tcp')
      conn.authorize_security_group(group_name, ip_protocol='icmp',
        cidr_ip='0.0.0.0/0')

    instance_info = self.describe_instances(key_name)
    conn.run_instances(image_id, count, count, key_name=key_name,
      security_groups=[group_name], instance_type=instance_type)

    end_time = datetime.datetime.now() + datetime.timedelta(0, 1800)
    now = datetime.datetime.now()

    while now < end_time:
      time_left = (end_time - now).seconds
      print('[{0}] {1} seconds left...'.format(now, time_left))
      latest_instance_info = self.describe_instances(key_name)
      public_ips = commons.diff(latest_instance_info[0], instance_info[0])
      if count == len(public_ips):
        private_ips = []
        instance_ids = []
        for public_ip in public_ips:
          index = latest_instance_info[0].index(public_ip)
          private_ips.append(latest_instance_info[1][index])
          instance_ids.append(latest_instance_info[2][index])
        return public_ips, private_ips, instance_ids
      time.sleep(20)
      now = datetime.datetime.now()

    raise AppScaleToolsException('Failed to spawn the required VMs')

  def describe_instances(self, keyname):
    instance_ids = []
    public_ips = []
    private_ips = []

    conn = self.open_connection()
    reservations = conn.get_all_instances()
    instances = [i for r in reservations for i in r.instances]
    for i in instances:
      if i.state == 'running' and i.key_name == keyname:
        instance_ids.append(i.id)
        public_ips.append(i.public_dns_name)
        private_ips.append(i.private_dns_name)
    return public_ips, private_ips, instance_ids

  def validate_machine_image(self, machine):
    if not machine.startswith(self.image_id_prefix):
      raise AppScaleToolsException('Invalid machine image ID: ' + machine)

    conn = self.open_connection()
    image = conn.get_image(machine)
    if image is None:
      raise AppScaleToolsException('Machine image %s does not exist' % machine)

  def open_connection(self):
    try:
      access_key = os.environ['EC2_ACCESS_KEY']
    except KeyError:
      raise AppScaleToolsException('EC2_ACCESS_KEY not set')

    try:
      secret_key = os.environ['EC2_SECRET_KEY']
    except KeyError:
      raise AppScaleToolsException('EC2_SECRET_KEY not set')

    return boto.connect_ec2(access_key, secret_key)

class EucaAgent(EC2Agent):
  pass

CLOUD_AGENTS = {
  'ec2' : EC2Agent(),
  'euca' : EucaAgent()
}

def validate_machine_image(infrastructure, machine):
  cloud_agent = CLOUD_AGENTS.get(infrastructure)
  cloud_agent.validate_machine_image(machine)

def spawn_head_node(options):
  cloud_agent = CLOUD_AGENTS.get(options[cli.OPTION_INFRASTRUCTURE])
  return cloud_agent.spawn_vms(1, options)

def is_valid_cloud_type(type):
  return CLOUD_AGENTS.has_key(type)