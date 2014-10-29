from distutils.core import setup

setup(
        name = "jpass",
        version = "0.1",
        description = "JPass password manager",
        url = "https://joel.porquet.org/wiki/hacking/jpass/",
        author = "Joël Porquet",
        author_email = "joel@porquet.org",
        license = "GPL3",
        install_requires = ["ConfigObj"],
        packages = ["jpass"],
        scripts = ["bin/jpass"],
        )
