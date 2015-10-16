# Copyright 2014, Joel Porquet

from .password import PasswordTransformer

class Attribute:

    req_attrs = ["method", "length", "pauth"]
    all_attrs = req_attrs + ["preq", "id", "extra", "comment"]

    preq = ["lower", "upper", "digit", "punct"]
    pauth = preq + ["alnum", "alpha"]

    @staticmethod
    def __check_req_attrs(service):
        """ check the service has all the required attributes
        """
        for a in Attribute.req_attrs:
            if not service.get_attr(a):
                raise ValueError("Service '{}': lacks a '{}' property"
                        .format(service.name, a))

    @staticmethod
    def __check_pauth_attr(service):
        """ check the pauth attribute is compliant
        """
        for p in service.get_attr("pauth"):
            if p not in Attribute.pauth:
                raise ValueError("Service '{}': "
                        "unknown class in 'pauth' field: '{}'"
                        .format(service.name, p))

    @staticmethod
    def __check_preq_attr(service):
        """ check the preq attribute is compliant
        """
        p = service.get_attr("preq")
        if not p:
            return
        length = int(service.get_attr("length"))
        count = 0
        for a in p:
            r = a.split(':')
            if len(r) < 2:
                raise ValueError("Service '{}': "
                        "less than two values in 'preq' field: '{}'"
                        .format(service.name, a))
            if r[0] not in Attribute.preq:
                raise ValueError("Service '{}': "
                        "unknown class in 'preq' field: '{}'"
                        .format(service.name, a))
            if not r[1].isdigit():
                raise ValueError("Service '{}': "
                        "wrong format for 'num' subfield in 'preq' field: '{}'"
                        .format(service.name, a))
            if len(r) >= 3:
                for i in range(2, len(r)):
                    if not r[i].isdigit():
                        raise ValueError("Service '{}': "
                                "wrong format for 'pos' subfield in 'preq' field: '{}'"
                                .format(service.name, a))
                    if int(r[i]) >= length:
                        raise ValueError("Service '{}': "
                                "out of bound 'pos' subfield in 'preq' field: '{}'"
                                .format(service.name, a))
            count += int(r[1])
        if count > length:
            raise ValueError("Service '{}': "
                    "total number of 'preq' is superior to length: {}"
                    .format(service.name, p))

    @staticmethod
    def __solve_pauth_attr(service):
        """ expand "alnum" and "alpha" into appropriate "lower", "upper" and
        "digit" root character classes
        """
        list_pauth = service.get_attr("pauth")
        for i in range(len(list_pauth)):
            a = list_pauth[i]
            if a == "alnum" or a == "alpha":
                list_pauth.pop(i)
                list_pauth.append("lower")
                list_pauth.append("upper")
                if a == "alnum":
                    list_pauth.append("digit")

    @staticmethod
    def __expand_attr_list(service, key):
        a = service.get_attr(key)
        if not a or isinstance(a, list):
            return
        a = a.split(',')
        service.set_attr(key, [v.strip() for v in a])

    @staticmethod
    def check_service(service):
        Attribute.__check_req_attrs(service)

        Attribute.__expand_attr_list(service, "pauth")
        Attribute.__check_pauth_attr(service)

        Attribute.__expand_attr_list(service, "preq")
        Attribute.__check_preq_attr(service)

        Attribute.__solve_pauth_attr(service)

    @staticmethod
    def fill_service(service, conf):
        for a in Attribute.all_attrs:
            service.set_attr(a, conf.get_section_attr(service.name, a))

class Service:

    def __init__(self, name, conf):
        if not conf.is_section(name):
            raise ValueError("Service '{}': unknown service" .format(name))

        self.conf = conf
        self.name = name
        self.basename = conf.get_section_basename(name)
        self.__attrs = {}

        Attribute.fill_service(self, conf)
        Attribute.check_service(self)

    def get_attr(self, key):
        return self.__attrs[key]

    def set_attr(self, key, value):
        self.__attrs[key] = value

    def __str__(self):
        r = "[{}]\n".format(self.name)
        r = "\tbasename: {}\n".format(self.basename)
        for k, v in self.__attrs.items():
            if not v:
                continue
            r += "\t{}\t: {}\n".format(k, v)
        return r

    def pretty_print(self, pwd):

        print("---")
        print("Service\t\t: {}".format(self.name))
        if self.basename != self.name:
            print("Passphrase\t: {}".format(self.basename))
        if self.get_attr("id"):
            print("Identifier\t: {}".format(self.get_attr("id")))
        if pwd:
            print("Password\t: {}".format(pwd))
        print("---")

    def generate_password(self, master_pwd):
        if not master_pwd:
            return None

        input_str = master_pwd
        input_str += " " + self.basename
        extra_str = self.get_attr("extra")
        if extra_str:
            input_str += " " + extra_str

        length = self.get_attr("length")
        pauth = self.get_attr("pauth")
        preq = self.get_attr("preq")

        pwd = PasswordTransformer.generate(
                self.conf,
                input_str,
                self.get_attr("method"),
                length,
                pauth,
                preq)

        return pwd

