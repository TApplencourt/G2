import sys
import os

try:
    import ConfigParser
    head = os.path.dirname(__file__)

    default_name = head + "/config.cfg.default"
    usr_name = head + "/../config.cfg"

    def overwrite():
        r = raw_input(
            "New default config file. If will overwrite youre. Continue? [Y/N]")

        if r.lower() == "y":
            os.system("cp {0} {1}".format(default_name, usr_name))
        elif r.lower() == "n":
            os.system("touch {0}".format(usr_name))
        else:
            overwrite()

    if not os.path.isfile(usr_name):
        os.system("cp {0} {1}".format(default_name, usr_name))
    else:
        default_time = os.path.getmtime(default_name)
        usr_time = os.path.getmtime(usr_name)

        if default_time > usr_time:
            overwrite()

    config = ConfigParser.ConfigParser()
    config.read(usr_name)

except:
    raise
    print "No config file or is corupted. Git reset may cure the diseases"
    sys.exit(1)
