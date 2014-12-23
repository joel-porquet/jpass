# JPass password manager

For more information about why this software, you can read this
[article](https://joel.porquet.org/wiki/hacking/password_management_history/)

![Jpass demo](https://joel.porquet.org/cgit/cgit.cgi/jpass.git/plain/docs/demo.gif)

## Usage

`jpass` is to be used in a terminal. Without any arguments, it will read the
default configuration file, located in `~/.jpass.conf`. Otherwise you can
specify the path of the configuration file as argument: `jpass -c
[configuration_file]`

    $ jpass -h
    usage: jpass [-h] [-v] [-c CONF] [-s SERVICE] [-i]

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbosity       increase verbosity level
      -c CONF, --conf CONF  specify a configuration file (default is
                            '~/.jpass.conf')
      -s SERVICE, --service SERVICE
                            specify a service name
      -i, --information     only display information about a service


Note: if you want to use `jpass` without installing it, then you have to modify
your `PYTHONPATH` when lauching the application (in the source directory):

    $ PYTHONPATH=$PWD:$PYTHONPATH bin/jpass

## Configuration file

The configuration follows the syntax of the
[ConfigObj](http://configobj.readthedocs.org/en/latest/) module .

In the configuration file, you define named services, and parameters for each
service. An example is as follow:

    method = sha256:base64
    length = 8
    pauth = alnum

    [google.com]
        id = yourname
        extra = 1211

    [startssl]
        extra = 0114
        length = 10
        comment = my ssl free certificate

    [mybank.com]
        extra = 0414
        length = 6
        pauth = digit

    [common1]
        extra = 1211

        \[[amazon.com]]
            id = myemail

        \[[shittywebsite.com]]
            id = myemail
            length = 9
            preq = lower:1, upper:1, digit:1, punct:1:8

At the root of the configuration file, there should be the definition of
default parameters that all other sections will inherit from, although those
parameters can be overridden in each section. At least `method`, `length` and
`pauth` should be defined for every services.

Here is the list of possible parameters with explanations:

* **method**: method for generating the password. Should be everything that the
  `hashlib` python module can do (':' indicates piping). *So far, jpass only
  supports sha256:base64 method.*
* **length**: length of the password.
* **pauth**: set of authorized characters in the password.
 * *alnum* ('a-zA-Z0-9')
 * *alpha* ('a-zA-Z')
 * *lower* ('a-z')
 * *upper* ('A-Z')
 * *digit* ('0-9')
 * *punct* ('/+')
* **preq**: list of required characters in the password. You can specify the
  number of characters of a certain class. You can also specify what should be
  the position of the characters in the password. The format is:
  `lower|upper|digit|punct:number[:position1:position2:...], ...`
* **id**: identifier for that service
* **extra**: extra token to add to the section name to generate the passphrase.
* **comment**: optional user string

A section can inherit from another one, by specifying more square brackets. For
example, in the example above, sections `amazon.com` and `shittywebsite.com`
both inherit from section `common1`.

