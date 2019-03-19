#!/usr/bin/env python

""" Marcos Moyano - marcos@gnu.org.ar

 PACMAN/YAOURT search/install engine with colors and some more info.
 Based on the Gentoo eix package.

 Copyright (c) 2007 Marcos Moyano

 This program is free software; you can REDistribute it and/or modify it
 under the terms of the GNU General Public License version 2 as published by
 the Free Software Foundation.
"""

import os
import sys
import getopt
from re import match
import urllib2

try:
    import pexpect
except:
    print "eix requires pexpect Python module. Install it from your default repository."
    sys.exit(1)

PRINT_VERSION = "0.1-r5"



####################
# Manage arguments #
####################
def parse(pmanager = None):
    """
    Manage the command line options.
    """
    package = None
    if len(sys.argv[1:]) == 0:
        print ("To few arguments: %d recieved. At least one is necessary.\n\
                \rTry 'eix -h' or 'eix --help' for more information." % \
                len(sys.argv[1:]))
        sys.exit(1)
    else:
        try:
            optlist, args = getopt.getopt(sys.argv[1:], \
            'hvV:iuap', \
            ['exact', 'deep', 'installed', 'help', 'version', 'clean', 'update', 'upgrade', 'purge'])
        except getopt.GetoptError, error:
            print ("eix: Invalid argument.%s\n\
            \rTry 'eix -h' or 'eix --help' for more information." % error)
            sys.exit(1)
        package = " ".join(args)
        cmd_ln_work(pmanager, package, optlist)

#####################################
# Work through the cmd line options #
#####################################
def cmd_ln_work(pmanager, package, optlist):
    """
    Work through the command line options.
    """
    pdeep = 0
    puniq = 0
    inst = 0
    for arg in optlist:
        if arg[0] == "-i":
            ecode = os.system("%s -S %s" % (pmanager, package))
            sys.exit(ecode)
        elif arg[0] == "-u":
            ecode = os.system("%s -R %s" % (pmanager,package))
            sys.exit(ecode)
        elif arg[0] == "-a":
            ecode = os.system("apropos %s" % package)
            sys.exit(ecode)
        #elif arg[0] == "-s":
        #    ecode = os.system("apt-get source %s" % package)
        #    sys.exit(ecode)
        elif arg[0] == "--exact":
            puniq = 1
        elif arg[0] == "--deep":
            pdeep = 1
        elif arg[0] == "--installed":
            inst = 1
        elif arg[0] == "--update":
            ecode = os.system("%s -Sy" % pmanager)
            sys.exit(ecode)
        elif arg[0] == "--upgrade":
            ecode = os.system("%s -Syu" % pmanager)
            sys.exit(ecode)
        elif arg[0] == "--clean":
            ecode = os.system("%s -Sc" % pmanager)
            sys.exit(ecode)
        elif arg[0] in ("-h", "--help"):
            printhelp()
            sys.exit(0)
        elif arg[0] in ("-p", "--purge"):
            ecode = os.system("%s -Rn %s" % (pmanager,package))
            sys.exit(ecode)
        elif arg[0] in ("-v", "-V", "--version"):
            print ("eix version is: %s \n" % PRINT_VERSION)
            sys.exit(0)
    search(pmanager, pdeep, puniq, inst, package)

####################
# Print help info  #
####################
def printhelp():
    """
    Print help information and exit.
    """
    print """Pacman/Yaourt search/install engine with colors and a little more.

Usage: eix [OPTIONS] EXPRESSION

Options:
   --deep                   Print package dependencies, recommended and suggested packages.
   --exact                  Print the exact match for EXPRESSION.
   --installed              Print installed packates that matches the search EXPRESSION.
   --clean                  Remove packages that are no longer installed from the cache.
   --update                 Update Pacman repository.
   --upgrade                Upgrade Pacman repository.
   -i                       Install the selected packages.
   -u                       Uninstall the selected packages.
   -a                       Search the manual page names and descriptions (apropos)
   -p, --purge              Remove packages and their configuration files.
   -V, -v, --version        Print version information and exit.
   -h, --help               Print this help and exit.

Report bugs to <marcos@gnu.org.ar>."""
    return

##################
#   Installed?   #
##################
def installed(pmanager, pname):
    """
    Look if the package is installed and return the version installed if it is.
    """
    try:
        if pmanager == 'yaourt':
            cache = os.popen("yaourt -Q %s 2>/dev/null | grep %s | awk -F/ '{print $2}'" % (pname,pname), "r")
        else:
            cache = os.popen("pacman -Q %s 2>/dev/null" % pname, "r")
        version = None
        for line in cache.readlines():
            line = line.strip().split()
            if line[0] == pname:
                version = line[1]
                break
        return(version)
    except:
        print "Signal Caught. Stop!"
        sys.exit(1)

##################
#   APT search   #
##################
def search(pmanager, flag, puniq, inst, package):
    """
    Pacman search for package.
    """
    result = os.popen("%s -Ss %s" % (pmanager,package), "r")
    results = result.readlines()
    for line in results:
        if not match("^ ",line) and line != "\x1b(B\x1b[m":
            myname = line.strip().split()[0]
            name = myname.split("/")[1]
            section = myname.split("/")[0]
            version = line.strip().split()[1]
            if puniq == 1:
                if name == package:
                    mysearch(pmanager, name, section, inst, flag)
                    break
            else:
                mysearch(pmanager, name, section, inst, flag)


####################
# APT SHOW search  #
####################
def mysearch(pmanager, pname, section, inst, printinfo):
    """
    EIX specified search through apt-cache show package.
    """
    resul = {"Section" : "", "Homepage" : "", "Description": "",
             "Version": "", "Deps": "", "Provides": "", "Build": ""}
    if pmanager == "yaourt" and section == "aur":
        cache = urllib2.urlopen("http://aur.archlinux.org/packages/%s/%s/PKGBUILD" % (pname,pname)).readlines()
        try:
            resul["Section"] = "AUR Unsupported"
            pkver = ''
            pkrel = ''
            for line in cache:
                line = line.strip()
                if match("^pkgdesc", line):
                   resul["Description"] = line.split("=")[1].strip().replace('"','').replace("'","")
                if printinfo == 1:
                    if match("^depends", line):
                        resul["Deps"] = line.split("=(")[1].strip().replace(')','').replace("'","")
                    if match("^provides", line):
                        resul["Provides"] = line.split("=(")[1].strip().replace(')','').replace("'","")
                    if match("^Build", line):
                        resul["Build"] = line.split(": ")[1].strip()
                if match("^pkgver", line):
                   pkver = line.split("=")[1]
                if match("^pkgrel", line):
                   pkrel = line.split("=")[1]
                if match("^url", line.lower()):
                   resul["Homepage"] = line.split("=")[1].strip().replace('"','').replace("'","")
            resul['Version'] = "%s-%s" % (pkver, pkrel)
            myprint(pmanager, pname, resul, inst, printinfo) 
        except Exception, e:
            print "se pudrio todo"
            sys.exit(1)
    else:
        out = os.popen("%s -Si %s" % (pmanager,pname), "r")
        cache = out.readlines()
        try:
            for line in cache:
                line = line.strip()
                if match("^Repository", line):
                    resul["Section"] = line.split(": ")[1].strip()
                if match("^Description", line):
                    resul["Description"] = line.split(": ")[1].strip()
                if printinfo == 1:
                    if match("^Depends", line):
                        resul["Deps"] = line.split(": ")[1].strip()
                    if match("^Provides", line):
                        resul["Provides"] = line.split(": ")[1].strip()
                    if match("^Build", line):
                        resul["Build"] = line.split(": ")[1].strip()
                if match("^Version", line):
                    resul["Version"] =line.split(": ")[1].strip()
                if match("^url", line.lower()):
                    resul["Homepage"] = line.split(": ")[1].strip()
            myprint(pmanager, pname, resul, inst, printinfo)
        except:
            print "se pudrio todo"
            sys.exit(1)

######################
# EIX personal print #
######################
def myprint(pmanager, pname, resul, inst, printinfo):
    """
    EIX specified print.
    """
    # Colors #
    RED = "\033[1;31m"
    BLUE = "\033[1;34m"
    GREEN = "\033[32;02m"
    WHITE = "\033[1;00m"
    YELLOW = "\033[1;33m"
    res = installed(pmanager, pname)
    if res == None and inst == 1:
        return
    if res == None and inst == 0:
        print ("%sPackage: %s%s %s" % (BLUE, RED, pname, WHITE))
    else:
        print ("%sPackage: %s%s %s[%s %s %s]" % \
            (BLUE, RED, pname, WHITE, YELLOW, res, WHITE))
    print ("\t%sDescription:\t%s%s\n\t%sSection:\t%s%s" % \
            (GREEN, WHITE, resul["Description"], GREEN, WHITE, resul["Section"]))
    if len(resul["Homepage"]) != 0:
        print ("\t%sHomepage:\t%s%s" % \
            (GREEN, WHITE, resul["Homepage"]))
    print ("\t%sVersion(s):\t%s%s" % \
            (GREEN, WHITE, resul["Version"]))
    if printinfo == 1:
        #for extra in resul["Version"]:
            if len(resul["Deps"]) != 0:
                print ("\t%sDepends:\t%s%s" % \
                    (GREEN, WHITE, resul["Deps"]))
            if len(resul["Build"]) != 0:
                print ("\t%sBuild on:\t%s%s" % \
                    (GREEN, WHITE, resul["Build"]))
            if len(resul["Provides"]) != 0:
                print ("\t%sProvides:\t%s%s" % \
                    (GREEN, WHITE, resul["Provides"]))
    print

def configure():
    """
    Configure weather to use pacman o yaourt
    """
    buffer = os.popen("whereis yaourt | awk '{print $2}'","r")
    if not buffer.readline().strip():
        pmanager = "pacman"
    else:
        pmanager = "yaourt"
        config = os.popen("grep -v \"#\" /etc/yaourtrc | grep \"TextOnly\"","r")
        if not config.readline().strip():
            print """In order for eix to work with yaourt please edit /etc/yaourtrc
to use text only color mod. Look for and uncomment the line:
#   ColorMod TextOnly
to look like this:
    ColorMod TextOnly

Sorry for the incovenience. Have fun :-)
            """
            sys.exit(1)
    return(pmanager)

if __name__ == "__main__":
    pmanager = configure()
    parse(pmanager)

