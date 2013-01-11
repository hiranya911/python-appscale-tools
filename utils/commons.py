import commands
import os

__author__ = 'hiranya'

class AppScaleToolsException(Exception):
  def __init__(self, msg, code=0):
    Exception.__init__(self, msg)
    self.code = code

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
    raise AppScaleToolsException('Object of type %s cannot be '
                                 'flattened' % type(obj))
