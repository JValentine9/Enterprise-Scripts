import psutil
import argparse
import sys
import re
import os, sys

parser = argparse.ArgumentParser(description='Get error and warning thresholds')
parser.add_argument("-w","--warning",help="Total percent of disk space free below which will generate a warning",type=float)
parser.add_argument("-c","--critical",help="Total percent of disk space free below which will generate a critical error",type=float)

args = parser.parse_args()

dirs_dict = {}

trace  = lambda *pargs, **kargs: None    # or print or report
error  = lambda *pargs, **kargs: print(*pargs, file=sys.stderr, **kargs)
report = lambda *pargs, **kargs: print(*pargs, file=reportfile, **kargs)
prompt = lambda text: input(text + ' ')
reportfile = sys.stdout   # reset in main or callers as needed

def treesize(root, alldirs, allfiles, counts):
    """
    sum and return all space taken up by root (all its files + subdirs);
    record sizes by pathname in-place in alldirs+allfiles: [(path, size)];
    also tally dir/folder counts in-place in counts: [numdirs, numfiles]; 
    """
    sizehere = 0
    try:
        allhere = os.listdir(root)
    except:
        allhere = []
        error('Error accessing dir (skipped):', root)   # e.g., recycle bin

    for name in allhere:
        path = os.path.join(root, name)

        if os.path.islink(path):
           trace('skipping link:', path)   # [1.1]

        elif os.path.isfile(path):
            trace('file:', path)
            counts[1] += 1
            filesize = os.path.getsize(path)
            allfiles.append((path, filesize))
            sizehere += filesize
            
        elif os.path.isdir(path):
            trace('subdir', path)
            counts[0] += 1
            subsize = treesize(path, alldirs, allfiles, counts)
            sizehere += subsize

        else:
            error('Unknown file type (skipped):', path)   # fifo, etc.

    alldirs.append((root, sizehere))
    return sizehere


crits = []
warns = []

disks = psutil.disk_partitions(all=False)

for disk in disks:
    ignoreDiskTypes = re.search('cdrom', disk.opts)
    ignoreMountPoints = re.search('(/var/lib/docker/containers|/snap.*)', disk.mountpoint)
    if not ignoreDiskTypes and not ignoreMountPoints:
        disk_usage = psutil.disk_usage(disk.mountpoint)
        disk_free_pct = 100 - disk_usage.percent
        if disk_free_pct <= args.warning and disk_free_pct > args.critical:
                warns.append("WARNING: Device {} at mount point {} has {}pct free space!".format(disk.device, disk.mountpoint, disk_free_pct))
        elif disk_free_pct <= args.critical:
                crits.append("CRITICAL: Device {} at mount point {} has {}pct free space!".format(disk.device, disk.mountpoint, disk_free_pct))
if crits and warns:
        for x in zip(crits,warns):
                print (x)
        sys.exit(2)
elif crits and not warns:
        print (crits)
        treesize()
        print(dirs_dict)
        sys.exit(2)
elif warns and not crits:
        print (warns)
        treesize()
        print(dirs_dict)
        sys.exit(1)
else:
        print ("OK")
        sys.exit(0)

print (disks)