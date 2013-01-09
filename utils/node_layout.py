import re
import yaml
from utils import commons
from utils.cloud import is_valid_cloud_type
from utils.commons import AppScaleToolsException

__author__ = 'hiranya'

ROLE_CONTROLLER = ':controller'
ROLE_SERVERS = ':servers'

ROLE_MASTER = ':master'
ROLE_SHADOW = ':shadow'
ROLE_LOAD_BALANCER = ':load_balancer'
ROLE_DATABASE = ':database'
ROLE_DATABASE_MASTER = ':db_master'
ROLE_DATABASE_SLAVE = ':db_slave'
ROLE_MEMCACHE = ':memcache'
ROLE_LOGIN = ':login'
ROLE_ZOOKEEPER = ':zookeeper'
ROLE_RABBITMQ = ':rabbitmq'
ROLE_RABBITMQ_MASTER = ':rabbitmq_master'
ROLE_RABBITMQ_SLAVE = ':rabbitmq_slave'
ROLE_APPENGINE = ':appengine'
ROLE_OPEN = ':open'

VALID_ROLES = frozenset([
  ROLE_MASTER, ROLE_SHADOW, ROLE_LOAD_BALANCER, ROLE_DATABASE,
  ROLE_DATABASE_MASTER, ROLE_DATABASE_SLAVE, ROLE_MEMCACHE, ROLE_LOGIN,
  ROLE_ZOOKEEPER, ROLE_RABBITMQ, ROLE_RABBITMQ_MASTER, ROLE_RABBITMQ_SLAVE,
  ROLE_APPENGINE, ROLE_OPEN
])

class NodeLayout:

  SIMPLE_FORMAT_KEYS = frozenset([ ':controller', ':servers' ])
  ADVANCED_FORMAT_KEYS = frozenset([
    ':master', ':database', ':appengine', ':open',
    ':login', ':zookeeper', ':memcache', ':rabbitmq'
  ])

  NODE_ID_REGEX = r'node-(\d+)'
  IP_REGEX = r'\d+\.\d+\.\d+\.\d+'

  INFRASTRUCTURE = 'infrastructure'
  DATABASE = 'database'
  MIN_IMAGES = 'min_images'
  MAX_IMAGES = 'max_images'
  REPLICATION = 'replication'
  READ_FACTOR = 'read_factor'
  WRITE_FACTOR = 'write_factor'

  def __init__(self, yaml_file_path, options=None, skip_replication=False):
    if yaml_file_path is not None:
      yaml_file = open(yaml_file_path, 'r')
      self.yaml = yaml.load(yaml_file)
      yaml_file.close()
    else:
      self.yaml = None

    if options is None: options = {}
    self.infrastructure = options.get(self.INFRASTRUCTURE)
    self.database_type = options.get(self.DATABASE)
    self.min_images = options.get(self.MIN_IMAGES)
    self.max_images = options.get(self.MAX_IMAGES)
    self.replication = options.get(self.REPLICATION)
    self.read_factor = options.get(self.READ_FACTOR)
    self.write_factor = options.get(self.WRITE_FACTOR)
    self.skip_replication = skip_replication
    self.nodes = []
    self.__populate_nodes()

  def get_head_node(self):
    for node in self.nodes:
      if node.has_role(ROLE_SHADOW):
        return node
    return None

  def get_nodes(self):
    return self.nodes

  def __populate_nodes(self):
    if self.__is_simple_format():
      self.__populate_simple_format()
    elif self.__is_advanced_format():
      pass
    else:
      raise AppScaleToolsException('Node layout does not conform to any '
                                   'of the supported specs.')

  def __populate_simple_format(self):
    cloud = is_valid_cloud_type(self.infrastructure)
    if self.yaml is None:
      if cloud:
        if self.min_images is None or self.max_images is None:
          raise AppScaleToolsException('Both min_images and max_images must'
                                       'be specified when no input yaml is'
                                       'provided')
      else:
        raise AppScaleToolsException('Input yaml must be provided for'
                                     'deployments on virtualized clusters')
    else:
      all_ips = commons.flatten(self.yaml.values())
      unique_ips = set(all_ips)
      if len(all_ips) != len(unique_ips):
        raise AppScaleToolsException('Duplicate IP addresses found in input yaml')

    nodes = []
    for role,ips in self.yaml.items():
      if ips is None:
        continue

      if isinstance(ips, str):
        ips = [ ips ]

      for ip in ips:
        node = SimpleAppScaleNode(ip, [role])
        if node.has_role(ROLE_SHADOW):
          node.add_role(ROLE_DATABASE_MASTER)
          node.add_role(ROLE_RABBITMQ_MASTER)
        else:
          node.add_role(ROLE_DATABASE_SLAVE)
          node.add_role(ROLE_RABBITMQ_SLAVE)
        node.validate()

        if cloud and not re.match(self.NODE_ID_REGEX, node.id):
          raise AppScaleToolsException('Invalid cloud node ID: %s. '
                                       'Cloud node IDs must be in the '
                                       'format node-{ID}.' % node.id)
        elif not cloud and not re.match(self.IP_REGEX, node.id):
          raise AppScaleToolsException('Invalid virtualized node ID: %s. '
                                       'Virtualized node IDs must be valid IP '
                                       'addresses.' % node.id)
        else:
          nodes.append(node)

    if len(nodes) == 1:
      nodes[0].add_role(ROLE_APPENGINE)
      nodes[0].add_role(ROLE_MEMCACHE)

    controllers = 0
    for node in nodes:
      if node.has_role(ROLE_SHADOW):
        controllers += 1

    if controllers > 1:
      raise AppScaleToolsException('Only one controller node is allowed')
    elif not controllers:
      raise AppScaleToolsException('No controller node has been assigned')

    if not self.skip_replication:
      self.__validate_data_replication(nodes)
    self.nodes = nodes

  def __validate_data_replication(self, nodes):
    db_nodes = 0
    for node in nodes:
      if node.has_role(ROLE_DATABASE) or node.has_role(ROLE_DATABASE_MASTER):
        db_nodes += 1

    if not db_nodes:
      raise AppScaleToolsException('At least 1 DB node must be available')

    if self.replication is None:
      if db_nodes > 3:
        self.replication = 3
      else:
        self.replication = db_nodes
    elif self.replication > db_nodes:
      raise AppScaleToolsException('Specified replication factor is too high'
                                   'to be satisfied by the available DB nodes')

    # TODO: DB specific checks
    pass

  def __is_simple_format(self):
    if self.yaml is None:
      return is_valid_cloud_type(self.infrastructure)
    else:
      return set(self.yaml.keys()).issubset(self.SIMPLE_FORMAT_KEYS)

  def __is_advanced_format(self):
    if self.yaml is None:
      return False
    else:
      return set(self.yaml.keys()).issubset(self.ADVANCED_FORMAT_KEYS)

class AppScaleNode:
  def __init__(self, id, roles=None):
    self.id = id
    if roles:
      self.roles = set(roles)
    else:
      self.roles = set([])
    self.expand_roles()

  def add_role(self, role):
    self.roles.add(role)
    self.expand_roles()

  def has_role(self, role):
    return role in self.roles

  def validate(self):
    invalid_roles = self.roles - VALID_ROLES
    if invalid_roles:
      raise AppScaleToolsException('Invalid roles: ' + ', '.join(invalid_roles))

  def expand_roles(self):
    raise NotImplemented

class SimpleAppScaleNode(AppScaleNode):
  def expand_roles(self):
    if ROLE_CONTROLLER in self.roles:
      self.roles.remove(ROLE_CONTROLLER)
      self.roles.add(ROLE_SHADOW)
      self.roles.add(ROLE_LOAD_BALANCER)
      self.roles.add(ROLE_DATABASE)
      self.roles.add(ROLE_MEMCACHE)
      self.roles.add(ROLE_LOGIN)
      self.roles.add(ROLE_ZOOKEEPER)
      self.roles.add(ROLE_RABBITMQ)

    if ROLE_SERVERS in self.roles:
      self.roles.remove(ROLE_SERVERS)
      self.roles.add(ROLE_APPENGINE)
      self.roles.add(ROLE_MEMCACHE)
      self.roles.add(ROLE_DATABASE)
      self.roles.add(ROLE_LOAD_BALANCER)
      self.roles.add(ROLE_RABBITMQ)

class AdvancedAppScaleNode(AppScaleNode):
  def expand_roles(self):
    if ROLE_MASTER in self.roles:
      self.roles.remove(ROLE_MASTER)
      self.roles.add(ROLE_SHADOW)
      self.roles.add(ROLE_LOAD_BALANCER)

    if ROLE_LOGIN in self.roles:
      self.roles.add(ROLE_LOAD_BALANCER)

    if ROLE_APPENGINE in self.roles:
      self.roles.add(ROLE_LOAD_BALANCER)

    if ROLE_DATABASE in self.roles:
      self.roles.add(ROLE_MEMCACHE)
