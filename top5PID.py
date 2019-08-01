import psutil
import argparse
import sys

parser = argparse.ArgumentParser(description='Get error and warning thresholds')
parser.add_argument("-w","--warning",help="Percent total cpu host utilization above which a warning is generated (i.e. 90)",type=float)
parser.add_argument("-c","--critical",help="Percent total cpu host utilization above which a critical error is generated(i.e. 100)",type=float)

args = parser.parse_args()

#Compares system CPU times elapsed before and after interval. Should be at least .1
CPU_INTERVAL = 1


def getListOfProcessSortedByMemory():
    '''
    Get list of running process sorted by Memory Usage
    '''
    listOfProcObjects = []
    # Iterate over the list
    for proc in psutil.process_iter():
       try:
           # Fetch process details as dict
           pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
           pinfo['vms'] = proc.cpu_percent()
           # Append dict to list
           listOfProcObjects.append(pinfo)
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass

    # Sort list of dict by key vms i.e. memory usage
    listOfProcObjects = sorted(listOfProcObjects,key=lambda procObj: procObj['pid'],reverse=True)
    return listOfProcObjects

pid_list = getListOfProcessSortedByMemory()[:5]

for i in range(5):
	print(pid_list)

#Compares system CPU times elapsed before and after interval. Should be at least .1

cpu_pct = psutil.cpu_percent(interval=CPU_INTERVAL)

if cpu_pct >= args.warning and cpu_pct < args.critical:
        print ('WARNING: CPU utilization at {} percent.'.format(cpu_pct))
        sys.exit(1)
elif cpu_pct >= args.critical:
        print ('CRITICAL: CPU utilization at {} percent.'.format(cpu_pct))
        sys.exit(2)
else:
        print ('OK')
        sys.exit(0)