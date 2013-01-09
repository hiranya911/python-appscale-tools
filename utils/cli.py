import optparse

__author__ = 'hiranya'

OPTION_AUTO = 'auto'
OPTION_IPS = 'ips'
OPTION_KEYNAME = 'keyname'

class CLIOption:
  def __init__(self, name, description, bool):
    self.name = name
    self.description = description
    self.bool = bool

class CLIOptionRepo:
  REPO = { }

  def __init__(self):
    self.put(OPTION_AUTO,
      'Automatically respond to all the prompts and warnings', bool=True)
    self.put(OPTION_IPS,
      'Path to the yaml file that contains the IP addresses of nodes')
    self.put(OPTION_KEYNAME,
      'Key name of the target AppScale deployment (defaults to "appscale")')

  def put(self, name, description, bool=False):
    self.REPO[name] = CLIOption(name, description, bool)

  def get(self, name):
    return self.REPO[name]

def get_parser(options):
  parser = optparse.OptionParser()
  repo = CLIOptionRepo()
  for option in options:
    cli_option = repo.get(option)
    if cli_option.bool:
      parser.add_option('--' + cli_option.name,
        action='store_true',
        dest=cli_option.name,
        help=cli_option.description)
    else:
      parser.add_option('--' + cli_option.name,
        action='store',
        type='string',
        dest=cli_option.name,
        help=cli_option.description)
  return parser

def print_usage_and_exit(msg, parser):
  print msg
  print
  parser.print_help()
  exit(1)


