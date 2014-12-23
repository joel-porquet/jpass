# Copyright 2014, Joel Porquet

import argparse
import sys

from .config import Config
from .service import Service

def get_service(conf):
    if conf.service:
        return conf.service

    import readline
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    readline.set_completer_delims('')
    readline.set_completer(conf.complete_section)

    try:
        return input("Enter service name    : ")
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit


def get_master_password(conf):
    try:
        import getpass
        return getpass.getpass("Enter master password : ")
    except (EOFError, KeyboardInterrupt):
        print()
        return None

def get_args():
        parser = argparse.ArgumentParser()

        parser.add_argument("-v", "--verbosity", action="store_true",
                help="increase verbosity level")

        parser.add_argument("-c", "--conf",
                help="specify a configuration file (default is '%s')" %
                Config.conf_file)

        parser.add_argument("-s", "--service", help="specify a service name")

        parser.add_argument("-i", "--information", action="store_true",
                help="only display information about a service")

        return parser.parse_args()

def main():
    args = get_args()

    conf = Config(args.conf, args.service,
            args.verbosity, args.information)

    service_name = get_service(conf)
    serv = Service(service_name, conf)

    pwd = None
    if not conf.information:
        master_pwd = get_master_password(conf)
        pwd = serv.generate_password(master_pwd)

    serv.pretty_print(pwd)

