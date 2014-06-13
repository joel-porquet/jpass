#!/usr/bin/env python

"""
JPass password manager
"""

import base64
import configparser
import copy
import getpass
import hashlib
import os
import readline
import rlcompleter
import string
import sys
import traceback

class PwdGenerator_sha256_base64:

    # password generator based on sha256:base64
    def generate(input_str):
        pwd = getpass.getpass("Enter master password : ")
        s = pwd + " " + input_str
        res_sha = hashlib.sha256()
        res_sha.update(s.encode('utf-8'))
        return (base64.standard_b64encode(res_sha.digest()),
                res_sha.digest_size)

class PwdReq:

    # requirement object
    def __init__(self, char, num, *pos):
        self.char = char
        self.num = int(num)
        self.pos = []

        for p in pos:
            self.pos.append(int(p))

    def __str__(self):
        r = "char:'%s', "%self.char
        r += "num:'%d'"%self.num
        for p in self.pos:
            r += ", pos:'%d'"%p
        return r

class PwdTransformer:

    char_lower = [x for x in string.ascii_lowercase]
    char_upper = [x for x in string.ascii_uppercase]
    char_digit = [x for x in string.digits]
    char_punct = ['/', '+']

    char_dict = { 'lower' : char_lower,
            'upper' : char_upper,
            'digit' : char_digit,
            'punct' : char_punct }

    char_dict_inv = { v:k for k,l in char_dict.items() for v in l }

    def __transform_char(old_c, out_dict):
        # get the length of old character's dict
        in_dict = PwdTransformer.char_dict_inv[old_c]
        in_len = len(PwdTransformer.char_dict[in_dict])

        # get the lenght of new character's dict
        out_len = len(PwdTransformer.char_dict[out_dict])

        # get the index of old character
        c_index = PwdTransformer.char_dict[in_dict].index(old_c)
        # map this index in the new character's dict
        c_index = c_index % out_len

        # perform the transform
        new_c = PwdTransformer.char_dict[out_dict][c_index]

        return new_c

    def __check_pauth(input_str, pauth):
        # create a list of authorized characters
        list_auth = []
        for auth in pauth:
            list_auth += PwdTransformer.char_dict[auth]

        # only pass: ensure everything character of the generated password is
        # compliant with the list of authorized characters
        s = list(input_str)
        for i in range(len(s)):
            c = s[i]
            if not c in list_auth:
                # if not authorized transform the character into the first
                # dict specidied by pauth
                c = PwdTransformer.__transform_char(c, pauth[0])
            s[i] = c
        return ''.join(s)

    def __check_preq(input_str, preq):
        # create a list of requirements
        list_preq = []
        for p in preq:
            a = p.split(':')
            list_preq.append(PwdReq(*a))

        s = list(input_str)

        # first pass: ensure position requirements
        for r in list_preq:
            for p in r.pos:
                c = s[p]
                c = PwdTransformer.__transform_char(c, r.char)
                s[p] = c

        # second pass: count the occurence of each char class
        occurences = { 'lower' : [],
                'upper' : [],
                'digit' : [],
                'punct' : []}
        for i in range(len(s)):
            c = s[i]
            in_dict = PwdTransformer.char_dict_inv[c]
            occurences[in_dict] += [i]

        # third pass: remove required chars from occurences
        for r in list_preq:
            for p in r.pos:
                # remove the item at the specified position
                occurences[r.char].remove(p)
                r.num -= 1
            if r.num > 0 and occurences[r.char]:
                while(r.num > 0 and len(occurences[r.char]) > 0):
                    #remove the last item if possible
                    occurences[r.char].pop()
                    r.num -= 1

        # compute the list of changeable indexes
        chg_indexes = []
        for k, v in occurences.items():
            chg_indexes += v
        chg_indexes.sort()

        # fourth pass: satisfy the requirements (in order of their
        # appearance )
        for r in list_preq:
            while (r.num > len(occurences[r.char])):
                # req is not satisfied
                # get and remove available index
                i = chg_indexes.pop(0)
                # transform the character
                c = s[i]
                c = PwdTransformer.__transform_char(c, r.char)
                s[i] = c
                # one requirement less
                r.num -= 1

        return ''.join(s)

    def __clip(input_str, length):
        return input_str[:int(length)]

    def generate(input_str, length, pauth, preq):
        digest, size = PwdGenerator_sha256_base64.generate(input_str)

        if size < int(length):
            raise ValueError("Size of generated password is not sufficient")

        digest = digest.decode('utf-8')

        # clip to the right length
        digest = PwdTransformer.__clip(digest, length)
        # solve pauth
        digest = PwdTransformer.__check_pauth(digest, pauth)
        # solve preq
        if preq is not None:
            digest = PwdTransformer.__check_preq(digest, preq)

        return digest

class PwdService:

    possible_args = [ 'method', 'length', 'pauth', 'preq', 'iden', 'extra',
            'comment', 'parent' ]
    required_args = [ 'method', 'length', 'pauth' ]

    possible_preq = [ 'lower', 'upper', 'digit', 'punct' ]
    possible_pauth = possible_preq + [ 'alnum', 'alpha' ]

    def __init__(self, name, service, parent = None):

        self.__name = name
        self.__parent = parent
        self.__args = {}

        # we only recognize a certain list of arguments
        for a in PwdService.possible_args:
            if a in service:
                self.__args[a] = service.get(a, None)

        # expand args into python lists
        self.__expand_arg('pauth')
        self.__expand_arg('preq')

        # check that the service has the minimum required args
        # and that pauth and preq are compliant
        self.__check_service_req()
        self.__check_service_pauth()
        self.__check_service_preq()

        # transform "alnum" and "alpha" into appropriate "lower", "upper" and
        # "digit" root character classes
        self.__solve_pauth()

    def __solve_pauth(self):
        list_pauth = self.__args['pauth']
        for i in range(len(list_pauth)):
            a = list_pauth[i]
            if a == 'alnum' or a == 'alpha':
                list_pauth.pop(i)
                list_pauth.append('lower')
                list_pauth.append('upper')
                if a == 'alnum':
                    list_pauth.append('digit')

    def __expand_arg(self, arg):
        # expand "char:num, char:num" string into a python list
        try:
            a = self.__args[arg]
        except:
            return
        a = a.split(',')
        self.__args[arg] = [v.strip() for v in a]

    def __check_service_req(self):
        # check the service has the required args
        for a in PwdService.required_args:
            if self.get(a) is None:
                raise ValueError("Service '%s'"%self.__name + " lacks a '%s' property"%a)

    def __check_service_pauth(self):
        # check pauth is compliant
        for a in self.__args['pauth']:
            if not a in PwdService.possible_pauth:
                raise ValueError("Unknown pauth class: '%s'"%a)

    def __check_service_preq(self):
        # check preq is compliant
        try:
            p = self.__args['preq']
        except:
            return
        length = int(self.__args['length'])
        count = 0
        for a in p:
            r = a.split(':')
            if len(r) < 2:
                raise ValueError("preq field has less than two values")
            if not r[0] in PwdService.possible_preq:
                raise ValueError("Unknown preq class: '%s'"%a)
            if not r[1].isdigit():
                raise ValueError("Num field is wrong for: '%s'"%r[0])
            if len(r) >= 3:
                for i in range(2, len(r)):
                    if not r[i].isdigit():
                        raise ValueError("Pos field is wrong for: '%s'"%r[0])
                    if int(r[i]) >= length:
                        raise ValueError("Pos field is out of bound for: '%s'"%r[0])
            count += int(r[1])
        if count > length:
            raise ValueError("Preq total num is superior to length")

    def __str__(self):
        r = "[%s]\n"%self.__name
        for a in self.__args.keys():
            r += "\t%s"%a
            r += ": %s\n"%self.__args[a]
        return r

    def get(self, arg):
        # get argument first from self, then from parent if any
        try:
            a = self.__args[arg]
        except:
            if self.__parent is not None:
                return self.__parent.get(arg)
            return None
        return a

    def get_name(self):
        # get name first from parent, then for self
        if self.__parent is not None:
            return self.__parent.__name
        return self.__name

    def print_pwd(self):
        # build the service passphrase
        basename = self.get_name()
        extra = self.get('extra')
        service_str = basename + " " + extra

        # get the constraints
        length = self.get('length')
        pauth = self.get('pauth')
        preq = self.get('preq')

        # generate the password
        pwd = PwdTransformer.generate(service_str,
                length, pauth, preq)

        # print everything about this service
        print("---")
        print("Service      : %s"%self.__name)
        print("Passphrase   : %s"%service_str)
        if self.get('iden') is not None:
            print("Identifier   : %s"%self.get('iden'))
        print("Password     : %s"%pwd)

class PwdCollection:

    def __init__(self, config):
        self.__services = {}

        # first add root sections
        # i.e. sections that do not have a parent node
        for s in config.sections():
            if not 'parent' in config[s]:
                self.__add_service(s, config[s])

        # then add child sections
        # i.e. sections that have a parent node
        for s in config.sections():
            if 'parent' in config[s]:
                p = config[s]['parent']
                if not p in self.__services:
                    raise ValueError("Parent '%s' does not exist..."%p)
                p = self.__services[p]
                self.__add_service(s, config[s], p)

    def __add_service(self, name, service, parent = None):
        self.__services[name] = PwdService(name, service, parent)

    def __get_service(self, name):
        a = self.__services[name]
        if a is None:
            raise ValueError("Service '%s'"%name + "does not exist")
        return a

    def __str__(self):
        r = ""
        for k, v in self.__services.items():
            r += str(v) + '\n'
        return r

    def complete_service(self, text, state):
        for k, v in self.__services.items():
            if k.startswith(text):
                if not state:
                    return k
                else:
                    state -= 1

    def print_pwd(self, name):
        service = self.__get_service(name)
        service.print_pwd()

def main():

    # determine configuration file
    if len(sys.argv) == 1:
        # no argument, then default file
        conf_file = os.path.expanduser("~/.jpass.conf")
    elif len(sys.argv) == 2:
        # one argument, then take it
        conf_file = os.path.abspath(str(sys.argv[1]))
    else:
        # more than one argument, impossible!
        raise ValueError("Usage: %s configuration_file"%str(sys.argv[0]))
        return 0

    if not os.path.exists(conf_file):
        raise ValueError("Configuration file not found: '%s'"%conf_file)
        return 0

    # open configuration file
    config = configparser.ConfigParser()
    try:
        config.read(conf_file)
    except configparser.Error as e:
        print("Error reading configuration file: ", e)
        return 0

    # start building a password collection
    # based on the configuration file
    try:
        pwd_collection = PwdCollection(config)
    except Exception as e:
        print("Error building password collection: ", e)
        return 0

    # get the service name wanted by the user
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    readline.set_completer_delims('')
    readline.set_completer(pwd_collection.complete_service)
    service_name = input("Enter service name    : ")

    # generate the password and display the corresponding information
    try:
        pwd_collection.print_pwd(service_name)
    except Exception as e:
        print("Error generating password: ", e)
        return 0

    return 1

if __name__ == '__main__':
    sys.exit(main())

__author__ = "Joel Porquet"
__copyright__ = "Copyright 2014, Joel Porquet"
__credits__ = "Joel Porquet, Julien Peeters"
__licence__ = "GPL"
__version__ = "3"
__maintainer__ = "Joel Porquet"
__email__ = "joel@porquet.org"
__status__ = "Prototype"
