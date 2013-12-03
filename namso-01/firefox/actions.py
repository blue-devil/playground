#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Licensed under the GNU General Public License, version 3.
# See the file http://www.gnu.org/licenses/gpl.txt

from pisi.actionsapi import autotools
from pisi.actionsapi import pisitools
from pisi.actionsapi import shelltools
from pisi.actionsapi import get

shelltools.export("JAVAC","/opt/sun-jdk/bin/javac")
shelltools.export("JAVA_HOME","/opt/sun-jdk")

WorkDir = "mozilla-beta"

# Set object directory name correctly. This directory is specific to the build host, and its name is generated by
# value returned by config.guess script.
# config.guess returns 'x86_64-unknown-linux-gnu' on x86_64 machines, and 'i686-pc-linux-gnu' on x86 machines
ObjDir = "obj-%s-unknown-linux-gnu" % get.ARCH() if get.ARCH() == "x86_64" else "obj-%s-pc-linux-gnu" % get.ARCH()

locales = "be  ca  da  de  el  en-US  es-AR  es-CL  es-ES  fi  fr  hr  hu  it  lt nl  pl  pt-BR  pt-PT  ro  ru  sr  sv-SE  tr  uk".split()
xpidir = "%s/xpi" % get.workDIR()
arch = get.ARCH()
ver = get.srcVERSION().replace("_", "") if "b" in get.srcVERSION() else ".".join(get.srcVERSION().split(".")[:3])

def setup():
    # LOCALE
    shelltools.system("rm -rf langpack-ff/*/browser/defaults")
    if not shelltools.isDirectory(xpidir): shelltools.makedirs(xpidir)
    for locale in locales:
        shelltools.system("wget -c -P %s ftp://ftp.mozilla.org/pub/mozilla.org/firefox/releases/%s/linux-%s/xpi/%s.xpi" % (xpidir, ver, arch, locale))
        shelltools.makedirs("langpack-ff/langpack-%s@firefox.mozilla.org" % locale)
        shelltools.system("unzip -uo %s/%s.xpi -d langpack-ff/langpack-%s@firefox.mozilla.org" % (xpidir, locale, locale))
        # replace browserconfig.properties
        print "Replacing browser.properties for %s locale" % locale
        shelltools.copy("browserconfig.properties", "langpack-ff/langpack-%s@firefox.mozilla.org/browser/chrome/%s/locale/branding/" % (locale, locale))
        shelltools.copy("browserconfig.properties", "browser/branding/official/locales/")

    # Mozilla sticks on with autoconf-213
    shelltools.chmod("autoconf-213/autoconf-2.13", 0755)

    # Set job count for make
    pisitools.dosed(".mozconfig", "%%JOBS%%", get.makeJOBS())

    shelltools.system("/bin/bash ./autoconf-213/autoconf-2.13 --macro-dir=autoconf-213/m4")
    shelltools.cd("js/src")
    shelltools.system("/bin/bash ../../autoconf-213/autoconf-2.13 --macro-dir=../../autoconf-213/m4")
    shelltools.cd("../..")

    shelltools.makedirs(ObjDir)
    shelltools.cd(ObjDir)

    shelltools.system("../configure --prefix=/usr --libdir=/usr/lib --disable-strip --disable-install-strip")

def build():
    # FIXME: Change library path and version with variables
    shelltools.export("LDFLAGS", "%s -Wl,-rpath,/usr/lib/%s-%s" % (get.LDFLAGS(), get.srcNAME(), get.srcVERSION()))

    shelltools.cd(ObjDir)
    autotools.make("-f ../client.mk build")

    autotools.make("-f ../client.mk configure")

def install():
    autotools.rawInstall("-f client.mk DESTDIR=%s" % get.installDIR())

    pisitools.remove("/usr/bin/firefox") # new Additional File  will replace that

    # Install language packs
    pisitools.insinto("/usr/lib/firefox/browser/extensions", "./langpack-ff/*")

    pisitools.dodir("/usr/lib/firefox/dictionaries")
    shelltools.touch("%s%s/dictionaries/tr-TR.aff" % (get.installDIR(), "/usr/lib/firefox"))
    shelltools.touch("%s%s/dictionaries/tr-TR.dic" % (get.installDIR(), "/usr/lib/firefox"))

    # Create profile dir, we'll copy bookmarks.html in post-install script
    pisitools.dodir("/usr/lib/firefox/browser/defaults/profile")

    # Install branding icon
    pisitools.insinto("/usr/share/pixmaps", "browser/branding/official/default256.png", "firefox.png")

    # Install docs
    pisitools.dodoc("LEGAL", "LICENSE")