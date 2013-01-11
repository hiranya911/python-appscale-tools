import commands

__author__ = 'hiranya'

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

