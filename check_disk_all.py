import psutil
import argparse
import sys
import re
import os, sys
import csv

parser = argparse.ArgumentParser(description='Get error and warning thresholds')
parser.add_argument("-w","--warning",help="Total percent of disk space free below which will generate a warning",type=float)
parser.add_argument("-c","--critical",help="Total percent of disk space free below which will generate a critical error",type=float)

args = parser.parse_args()

FileContents=[]

def ProcessData():
        with open('C:\\temp\\WizTreeTest.csv', 'r') as f:
                FileContents = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
        FileContents = sorted(FileContents, key = lambda i: i['b'], reverse = True)
        #FileContents[:5]
        for x in FileContents[:5]:
                print("File: " + x['a'] + ", Size: " + x['b'])
        
        


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
        ProcessData()
        sys.exit(2)
elif warns and not crits:
        print (warns)
        ProcessData()
        sys.exit(1)
else:
        print ("OK")
        sys.exit(0)

print (disks)