import psutil
import argparse
import sys

parser = argparse.ArgumentParser(description='Get error and warning thresholds')
parser.add_argument("-w","--warning",help="Percent total cpu host utilization above which a warning is generated (i.e. 90)",type=float)
parser.add_argument("-c","--critical",help="Percent total cpu host utilization above which a critical error is generated(i.e. 100)",type=float)

args = parser.parse_args()

#Compares system CPU times elapsed before and after interval. Should be at least .1


def setSeverity(cpu_percent):
        '''
        Compares system CPU times elapsed before and after interval. Should be at least .1
        '''
        cpu_pct = cpu_percent


        if cpu_pct >= args.warning and cpu_pct < args.critical:
                return 'WARNING: CPU utilization at {} percent.'.format(cpu_pct)
                #sys.exit(1)
        elif cpu_pct >= args.critical:
                return 'CRITICAL: CPU utilization at {} percent.'.format(cpu_pct)
                #sys.exit(2)
        else:
                return 'OK'
                #sys.exit(0)

def getListOfProcessSortedByCPU():
    '''
    Get list of running process sorted by CPU Usage
    '''
    CPU_INTERVAL = 1
    listOfProcObjects = []

    # Iterate over the list
    for proc in psutil.process_iter():
       try:
           # Fetch process details as dict
           pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
           
           # Fetches PID and gets cpu percent by that PID
           pID = psutil.Process(pid=pinfo["pid"])
           pinfo['cpu'] = pID.cpu_percent(interval=CPU_INTERVAL)
           pinfo["severity"] = setSeverity(pinfo['cpu'])

           # Append dict to list
           listOfProcObjects.append(pinfo)
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass

    # Sort list of dict by key cpu
    listOfProcObjectsbyCPU = sorted(listOfProcObjects,key=lambda procObj: procObj['cpu'],reverse=True)

    return listOfProcObjectsbyCPU

# Sets pid_list to list of dictionary and limits it to the first five dictionaries (top five)
pid_list = getListOfProcessSortedByCPU()[1:6]

# Prints "headers" 
print("PID", "Name","CPU", "Severity")

# Prints PID, CPU and Name
for x in pid_list:
        print(x["pid"], x["name"], x["cpu"], x["severity"])