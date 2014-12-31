# Copyright 2014, Joel Porquet

import configobj
import os
import sys

class Config:

    conf_file = os.path.expanduser("~/.jpass.conf")
    __config = None

    def __init__(self, conf = None, service = None, verbosity = None,
            information = None):
        self.verbose = verbosity
        self.service = service
        self.information = information

        if conf:
            self.conf_file = conf

        self.__parse_conf()
        self.__build_linear_dict()

    def __parse_conf(self):
        if self.verbose:
            print("Using configuration file '{!s}'".format(self.conf_file))

        self.__config = configobj.ConfigObj(self.conf_file, file_error=True)

    def __add_section_dict(self, root):
        for s in root.sections:
            self.linear_dict[s] = root.get(s)
            self.__add_section_dict(root.get(s))

    def __build_linear_dict(self):
        self.linear_dict = {}
        self.__add_section_dict(self.__config)

    def is_section(self, section):
        for k in self.linear_dict:
            if k == section:
                return True
        return False

    def complete_section(self, text, state):
        for k in self.linear_dict:
            if k.startswith(text):
                if not state:
                    return k
                else:
                    state -= 1

    def __get_section_attr(self, section, attr):
        if attr in section.scalars:
            return section.get(attr)
        elif section.parent is not section:
            return self.__get_section_attr(section.parent, attr)
        else:
            return None

    def get_section_attr(self, section_name, attr):
        s = self.linear_dict[section_name]
        return self.__get_section_attr(s, attr)

    def __get_section_basename(self, section):
        if section.depth == 1:
            return section.name
        elif section.depth > 1:
            return self.__get_section_basename(section.parent)
        else:
            return None

    def get_section_basename(self, section_name):
        s = self.linear_dict[section_name]
        basename = self.__get_section_basename(s)
        if not basename:
            raise ValueError("Service '{}': cannot find basename!?"
                    .format(section_name))
        return basename

