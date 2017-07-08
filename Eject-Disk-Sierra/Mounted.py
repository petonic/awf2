#! /usr/bin/env python2

"""
[2017-07-08 SAT 11:58] Petonic
Modified from:
 https://www.alfredforum.com/topic/1756-eject-specific-drivesvolumesmounts/
Look for the tinyupload link there.

Goal is to modify the behavior to look at all disks, not the ones
in /Volumes.
"""

import os
import re
import glob
from Feedback import Feedback

import subprocess
import sys
from pprint import pformat

targetDisk = ""

class buff(str):
    def get_value(self, name):
        """
        Returns the string value of the named line. This buffer is populated
        by the output of the 'diskutil info -all' command.

        If no value is found, then returns None.
        """
        rstr = r'^\s+{}:\s+(.+)\s*'.format(name)
        m = re.search(rstr, self, re.M)
        # "DBG:********"; from pdb import set_trace as bp; bp();
        if m:
            return m.group(1)
        else:
            return None



def run():
    targetDisk = None

    disk_desc = {}
    disk_icon = {}

    # print >>sys.stderr, 'Got here at the top, argv=<{}>, len(argv1)={}'.format(
    #     pformat(sys.argv), len(sys.argv[1]))

    if len(sys.argv) == 2 and len(sys.argv[1]):
        targetDisk = sys.argv[1].strip()
    # print >>sys.stderr, 'targetdisk = <{}>'.format(targetDisk)


    # Get all mounts from diskutil
    proc = subprocess.Popen(['diskutil', 'info', '-all'], stdout=subprocess.PIPE)

    lines = ''
    for line in iter(proc.stdout.readline, ''):
        lines = lines + line

        # print >>sys.stderr, 'Line: {}'.format(line),

        if line.rstrip() != '**********':
            continue

        currBuff = buff(lines)
        lines = '' # Clear it for the next partition

        #
        # We've reached the end of the entry (*****), so start processing
        #

        # Check mount status -- only want mounted drives.
        if currBuff.get_value('Mounted') != 'Yes':
            continue

        # Check protocol status, only interested in 'USB' or 'Disk Image'
        partProt = currBuff.get_value('Protocol')
        if partProt != 'USB' and partProt != 'Disk Image':
            continue

        # OK, it's a valid unmountable filesystem
        # Get the base disk:
        #     Part of Whole:            disk4
        diskBase = currBuff.get_value('Part of Whole')


        # Get the size of the volume -- need to massage
        partSize = currBuff.get_value('Disk Size')
        # --> '209.7 MB (209715200 Bytes) (exactly 409600 512-Byte-Units)'
        m = re.search(r'([0-9.]+\s\S+)\s', partSize)
        assert(m)
        partSize = m.group(1)

        # Get the partNum of the volume -- need to massage
        partNum = currBuff.get_value('Device Identifier')
        # --> 'Device Identifier:        disk2s1'
        m = re.search(r'disk[0-9]+s([0-9]+)', partNum)
        if not m:           # doesn't have the 's' slice part in name
            continue
        partNum = m.group(1)

        # Get the partName:
        partName = currBuff.get_value('Volume Name')
        assert(m)

        # If the user specified a number as an arg, filter using that
        if targetDisk and (targetDisk != diskBase) and \
            (targetDisk != '') and (targetDisk not in partName):
            continue


        # print >>sys.stderr, 'Ejectable Part: {} {} = "{}"({})'.format( diskBase, partNum, partName, partProt)

        if diskBase in disk_desc:
            disk_desc[diskBase] += ', '
        else:
            disk_desc[diskBase] = ''
        disk_desc[diskBase] += '{}) "{}"({}) {}'.format(partNum, partName, partProt, partSize)
        # Overwrite the disk_icon to be last partition type found
        disk_icon[diskBase] = get_disk_icon(partProt)

    # print >>sys.stderr, 'len of descs is {}'.format(
    #         len(disk_desc))


    #Debug stopping point
    ### sys.exit(99)

    # Create the object to display mounts
    feedback = Feedback()

    # print >>sys.stderr, 'len of descs is {}'.format(
    #         len(disk_desc))
    # Add the mounted disks and descriptions
    for i in disk_desc.iterkeys():
        feedback.add_item(i, disk_desc[i], i, icon=disk_icon[i])

    if len(disk_desc) or (sys.argv[1] == ' ') or \
        (targetDisk == 'all'):
        feedback.add_item('All', 'Eject All Disks.', 'all')
    # If no disks are mounted...say so
    else:
        feedback.add_item('No Volumes Found...',
                          'Searched for mounted external drives with diskutil')

    # print >>sys.stderr, 'Feedback is {}'.format(pformat(feedback))
    return feedback


def get_disk_icon(diskinfo_parm):
    if 'USB' in diskinfo_parm:
        return 'USB.png'
    if 'Disk Image' in diskinfo_parm:
        return 'DMG.png'
    print >>sys.stderr, 'Error: invalid diskinfo_parm value: <%s>' % diskinfo_parm
    sys.exit(99)

if __name__ == '__main__':
    run()
