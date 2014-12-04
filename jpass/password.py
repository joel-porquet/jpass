# Copyright 2014, Joel Porquet

import base64
import hashlib
import string

class Generator_sha256_base64:

    @staticmethod
    def generate(input_str):
        sha = hashlib.sha256()
        sha.update(input_str.encode("utf-8"))
        b64 = base64.standard_b64encode(sha.digest())
        return (b64, sha.digest_size)

class PasswordGenerator:

    generators = {
            "sha256:base64" : Generator_sha256_base64,
            }

    @staticmethod
    def generate(input_str, method):
        if method in PasswordGenerator.generators:
            return PasswordGenerator.generators[method].generate(input_str)
        else:
            raise ValueError("Cannot find password generation method '{}'"
                    .format(method))

class PasswordReq:

    def __init__(self, char_dict, num, *pos):
        self.char_dict = char_dict
        self.num = int(num)
        self.pos = [int(p) for p in pos]

    def __str__(self):
        r = "char_dict:'{}', ".format(self.char_dict)
        r += "num:'{}'".format(self.num)
        for p in self.pos:
            r += ", pos:'{}'".format(p)
        return r

class PasswordTransformer:

    char_lower = [x for x in string.ascii_lowercase]
    char_upper = [x for x in string.ascii_uppercase]
    char_digit = [x for x in string.digits]
    char_punct = ['/', '+']

    char_dict = {
            'lower' : char_lower,
            'upper' : char_upper,
            'digit' : char_digit,
            'punct' : char_punct
            }

    char_dict_inv = {v: k for k, l in char_dict.items() for v in l}

    @staticmethod
    def __transform_char(old_c, out_dict):
        """ Transform a character into another character which belongs to a
        specified dictionary
        """
        # get the length of old character's dict
        in_dict = PasswordTransformer.char_dict_inv[old_c]
        in_len = len(PasswordTransformer.char_dict[in_dict])

        # get the length of new character's dict
        out_len = len(PasswordTransformer.char_dict[out_dict])

        # get the index of old character
        c_index = PasswordTransformer.char_dict[in_dict].index(old_c)
        # map this index in the new character's dict
        c_index = c_index % out_len

        # perform the transform
        new_c = PasswordTransformer.char_dict[out_dict][c_index]

        return new_c

    @staticmethod
    def __check_pauth(input_str, pauth):
        """ Check a input string against the specified list of pauth classes.
        Transform all the characters that don't comply.
        """
        # create a list of authorized characters
        list_auth = []
        for auth in pauth:
            list_auth += PasswordTransformer.char_dict[auth]

        # only pass: ensure everything character of the generated password is
        # compliant with the list of authorized characters
        s = list(input_str)
        for i in range(len(s)):
            c = s[i]
            if c not in list_auth:
                # if not authorized transform the character into the first
                # dict specidied by pauth
                c = PasswordTransformer.__transform_char(c, pauth[0])
            s[i] = c
        return ''.join(s)

    @staticmethod
    def __check_preq(input_str, preq):
        """ Make an input_str comply with a list of preq.
        """
        # create a list of requirements
        list_preq = []
        for p in preq:
            a = p.split(':')
            list_preq.append(PasswordReq(*a))

        s = list(input_str)

        # first pass: ensure position requirements
        for r in list_preq:
            for p in r.pos:
                c = s[p]
                c = PasswordTransformer.__transform_char(c, r.char_dict)
                s[p] = c

        # second pass: count the occurence of each char class
        occurences = {
                'lower' : [],
                'upper' : [],
                'digit' : [],
                'punct' : []}
        for i in range(len(s)):
            c = s[i]
            in_dict = PasswordTransformer.char_dict_inv[c]
            occurences[in_dict] += [i]

        # third pass: remove required chars from occurences
        for r in list_preq:
            for p in r.pos:
                # remove the item at the specified position
                occurences[r.char_dict].remove(p)
                r.num -= 1
            if r.num > 0 and occurences[r.char_dict]:
                while(r.num > 0 and len(occurences[r.char_dict]) > 0):
                    #remove the last item if possible
                    occurences[r.char_dict].pop()
                    r.num -= 1

        # compute the list of changeable indexes
        chg_indexes = []
        for k, v in occurences.items():
            chg_indexes += v
        chg_indexes.sort()

        # fourth pass: satisfy the requirements (in order of their appearance)
        for r in list_preq:
            while (r.num > len(occurences[r.char_dict])):
                # req is not satisfied
                # get and remove available index
                i = chg_indexes.pop(0)
                # transform the character
                c = s[i]
                c = PasswordTransformer.__transform_char(c, r.char_dict)
                s[i] = c
                # one requirement less
                r.num -= 1

        return ''.join(s)

    @staticmethod
    def __clip(input_str, length):
        return input_str[:int(length)]

    @staticmethod
    def generate(conf, input_str, method, length, pauth, preq):
        # first get the raw password
        digest, size = PasswordGenerator.generate(input_str, method)

        # now start working on the raw password
        if size < int(length):
            raise ValueError("Size of generated password is not sufficient: < {}"
                    .format(length))

        digest = digest.decode('utf-8')

        # clip to the right length
        digest = PasswordTransformer.__clip(digest, length)
        # solve pauth
        digest = PasswordTransformer.__check_pauth(digest, pauth)
        # solve preq
        if preq is not None:
            digest = PasswordTransformer.__check_preq(digest, preq)

        return digest

