#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 USTC LUG
#		2011 Cheng Zhang
#
# Author: 	Cheng Zhang <StephenPCG@gmail.com>
# Maintainer: 	Cheng Zhang <StephenPCG@gmail.com>

import datetime
import glob
import os.path
import re
import time

LOG_BASE = os.path.join(os.getenv("HOME"), "log/")
ETC_BASE = os.path.join(os.getenv("HOME"), "etc/")
BIN_BASE = os.path.join(os.getenv("HOME"), "bin/")

SIZE_UNIT = {
    0: " B",
    1: "KB",
    2: "MB",
    3: "GB",
    4: "TB"
}

REAL_NAME = {
    "backports": '<a href="/debian-backports/">Debian Backports</a>',
    "cpan": '<a href="/CPAN/">CPAN</a>',
    "ctan": '<a href="/CTAN/">CTAN</a>',
    "cran": '<a href="/CRAN/">CRAN</a>',
    "xorg": '<a href="/Xorg/">Xorg</a>',
    "backtrack": '<a href="/backtrack/iso/">Back Track ISO</a>',
    "backtracp-packages": '<a href="/backtrack/">Back Track Packages</a>',
    "fedora-linux": '<a href="/fedora/linux/">Fedora Linux</a>',
    "dotdeb": '<a href="/dotdeb/packages/">Dotdeb Packages</a>',
    "dotdeb-php53": '<a href="/dotdeb/php53/">Dotdeb PHP53</a>',
    "apt-mirror": '<a href="/backtrack">Back Track Packages</a>',
    "cygwinports": '<a href="/sourceware.org/cygwinports/">Cygwin Ports Project</a>',
    "scientific": '<a href="/scientificlinux/">Scientific Linux</a>',
    "kde-application": '<a href="/kde-applicationdata/">KDE Application Data</a>',
    "bioc_2_11": '<a href="/bioc/2.11/">bioc 2.11</a>',
    "bioc_2_12": '<a href="/bioc/2.12/">bioc 2.12</a>',
}

HTML_TAGS = {
    "running": "<td class='td-archive-running syncstatus'></td>",
    "finished": "<td class='td-archive-finished syncstatus'></td>",
    "nodata": "<td class='td-nodata'></td>",
    "begin_archvie_name": "<td class='td-archive-name'>",
    "begin_archive_synctime": "<td class='td-archive-synctime'>",
    "begin_archive_size": "<td class='td-archive-size'>",
    "begin_archive_upstream": "<td class='td-archive-upstream'>",
    "success": "<td class='td-archive-succeed exitstatus'></td>",
    "fail": "<td class='td-archive-fail exitstatus'></td>",
    "exit-unknown": "<td class='td-archive-unknown exitstatus'></td>",
    "unknown": "<td class='td-archive-unknown'></td>",
    "end_td": "</td>",
    "begin_tr": "<tr>",
    "end_tr": "</tr>\n"
}


def toHumanReadableSize(size_in_byte):
    """ convert size in byte to human readable size, B/KB/MB/GB """
    new_size = size_in_byte
    new_unit = 0
    while new_size >= 1024.0:
        new_size /= 1024.0
        new_unit += 1

    return "%.2f %s" % (new_size, SIZE_UNIT[new_unit])


def getSyncScript(archive_name):
    """　get sync script used by archive_name """
    if archive_name == "debian-cd":
        return "cd-mirror"
    elif "debian" in archive_name or archive_name == "nexenta" or archive_name == "ubuntu":
        return "ftpsync"
    elif "progress" in archive_name:
        return "ftpsync"
    elif archive_name == "chromium-buildbot":
        return "chromium"
    elif archive_name == "apt-mirror":
        return "apt-mirror"
    else:
        return "ustcsync"


def getLogFileName(archive_name, script_type):
    """ get log filename for archive, without postfix '.0' """
    if script_type == "chromium":
        return LOG_BASE + archive_name + "/update-chromium.log"
    elif script_type == "apt-mirror":
        return LOG_BASE + archive_name + "/apt-mirror.log"
    elif script_type == "cd-mirror":
        return LOG_BASE + archive_name + "/rsync-debian-cd-mirror.log"
    elif archive_name == "debian":
        return LOG_BASE + archive_name + "/rsync-ftpsync.log"
    elif script_type == "ftpsync":
        return LOG_BASE + archive_name + "/rsync-" + script_type + "-" + archive_name + ".log"
    else:
        return LOG_BASE + archive_name + "/" + script_type + "-" + archive_name + ".log"


def getSyncStatus(log_file_name):
    """  get archive sync status, use archive_name and script_type to determine log file """
    if os.path.isfile(log_file_name):
        return "running"
    elif os.path.isfile(log_file_name + ".0"):
        return "finished"
    else:
        return "exit-unknown"


def getSyncErrorAndArchiveSize(log_file_name):
    """ parse log file, get ERROR status and archive size, returns a tuple (error, size) """
    log_file_name += ".0"
    if not os.path.isfile(log_file_name):
        return False, "nodata"
    error = False
    size = "nodata" 
    for line in open(log_file_name):
        if line.find("ERROR") != -1 or line.find("rsync error") != -1:
            error = True
        if line.find("total size is") != -1:
            size = toHumanReadableSize(int(re.search('total size is (\d+)', line).group(1)))
        elif line.find("/srv/ftp/chromium-buildbot") != -1:
            size = re.sub("^(\d+)([MG]) /srv/ftp/chromium-buildbot.*\n", "\g<1> \g<2>B", line)
    return error, size


def getArchiveUpstream(archive_name, sync_script):
    """ get archive upstream """
    if sync_script == "chromium":
        for line in open(BIN_BASE + "mirror-chromium"):
            if re.search("^FROM", line):
                return re.search('^FROM.+"(.+)"', line).group(1)
    if sync_script == "apt-mirror":
        return "http://backtrack-linux.org/"
    if archive_name == "tdf":
        return "Pushed, always update to date."
    if archive_name == "debian-volatile":
        return "Upstream freeze, no update any more."
    if sync_script == "cd-mirror":
        etc_file = ETC_BASE + "debian-cd-mirror.conf"
    else:
        etc_file = ETC_BASE + sync_script + "-" + archive_name + ".conf"
    upstream = ""
    path = ""
    for line in open(etc_file):
        if re.search("^RSYNC_HOST", line):
            upstream = re.search('^RSYNC_HOST.+"(.+)"', line).group(1)
        if re.search("^RSYNC_PATH", line):
            path = re.search('^RSYNC_PATH.+"(.+)"', line).group(1)
    return "rsync://" + upstream + "/" + path


def getArchiveSyncTime(log_file_name, sync_status):
    if sync_status == "running":
        if os.path.isfile(log_file_name):
            return datetime.datetime.fromtimestamp(int(os.path.getmtime(log_file_name)))
        else:
            return "unknown"
    else:
        if os.path.isfile(log_file_name + ".0"):
            return datetime.datetime.fromtimestamp(int(os.path.getmtime(log_file_name + ".0")))
        else:
            return "unknown"


def printTableHead():
    print "<p><span id='update-time'>", str(datetime.datetime.fromtimestamp(int(time.time()))), "</span></p>"
    print "<table class='tbl-status'><thead><tr>"
    print "<th class='th-archive-name'></th>"
    print "<th class='th-archive-syncstatus syncstatus'></th>"
    print "<th class='th-archive-synctime'></th>"
    print "<th class='th-archive-exitstatus exitstatus'></th>"
    print "<th class='th-archive-upstream'></th>"
    print "<th class='th-archive-size'></th>"
    print "</tr></thead><tbody>"


def printTableTail():
    print "</tbody></table>"

if __name__ == "__main__":
    printTableHead()

    for archive in os.listdir(LOG_BASE):
        if archive.startswith("."):
            continue
        #if archive == "freebsd" or archive == "olddebian":
        if archive == "olddebian":
            continue

        realname = REAL_NAME[archive] if archive in REAL_NAME else \
                '<a href="/{0}/">{1}</a>'.format(archive, archive)

        script = getSyncScript(archive)
        log_filename = getLogFileName(archive, script)

        status = getSyncStatus(log_filename)
        _has_error, size = getSyncErrorAndArchiveSize(log_filename)

        exit_status = "exit-unknown" if status == "running" else \
            "fail" if _has_error else "success"

        size = HTML_TAGS["nodata"] if size == "nodata" else \
            '{0}{1}{2}'.format(HTML_TAGS["begin_archive_size"], size, HTML_TAGS["end_td"])

        try:
            upstream = getArchiveUpstream(archive, script)
        except IOError:
            continue

        time = getArchiveSyncTime(log_filename, status)
        time = HTML_TAGS["unknown"] if time == "unknown" else \
            '{0}{1}{2}'.format(HTML_TAGS["begin_archive_synctime"], time, HTML_TAGS["end_td"])

        print HTML_TAGS["begin_tr"], \
            HTML_TAGS["begin_archvie_name"], realname, HTML_TAGS["end_td"], \
            HTML_TAGS[status], \
            time, \
            HTML_TAGS[exit_status], \
            HTML_TAGS["begin_archive_upstream"], upstream, HTML_TAGS["end_td"], \
            size, \
            HTML_TAGS["end_tr"]

    printTableTail()

