import psutil
import argparse
import sys, time, os, datetime, socket
import multiprocessing as mp

parser = argparse.ArgumentParser(description='Get error and warning thresholds')
parser.add_argument("-w","--warning",help="Percent total cpu host utilization above which a warning is generated (i.e. 90)",type=float)
parser.add_argument("-c","--critical",help="Percent total cpu host utilization above which a critical error is generated(i.e. 100)",type=float)

args = parser.parse_args()
now = datetime.datetime.now()

#Compares system CPU times elapsed before and after interval. Should be at least .1


def setSeverity(cpu_percent, pname):
        '''
        Compares system CPU times elapsed before and after interval. Should be at least .1
        '''
        cpu_pct = cpu_percent


        if cpu_pct >= args.warning and cpu_pct < args.critical:
                return 'WARNING', 'CPU utilization at %s percent on %s'%(cpu_pct, pname)
                #sys.exit(1)
        elif cpu_pct >= args.critical:
                return 'CRITICAL', 'CPU utilization at %s percent on %s'%(cpu_pct, pname)
                #sys.exit(2)
        else:
                return 'OK', 'CPU utilization at %s percent on %s'%(cpu_pct, pname)
                #sys.exit(0)

#proc = collections.OrderedDict()
def GetProcessInformation(p):
        # Will skip over the idle process which will always be PID 0
        if(p == 0): return
        CPU_INTERVAL = 1
        proc = {}#collections.OrderedDict()
        try:
                p = psutil.Process(p)
                # Sets the proc to a dictionary with the Process information
                # pid, name, & username are attributes that are attached to a process
                proc['PID'], proc['Component'], proc['User'] = p.pid, p.name(), p.username()

                # Creates a reference point for the process's CPU checks
                # p.cpu_percent(interval=CPU_INTERVAL)

                # Does the second CPU check and records it to the dictionary
                proc['CPU_Usage'] = p.cpu_percent(interval=CPU_INTERVAL)
                
                # Checks and records the severity and summary with the setSeverity()
                proc['Severity'], proc['Summary'] = setSeverity(proc['CPU_Usage'], proc['Component'])
                # Gets current timestamp, hostname & IP
                proc['Timestamp'] = now.strftime('%Y-%m-%d %H:%M')
                proc['Source'] = socket.gethostname() + ' - ' + socket.gethostbyname(socket.gethostname())
                # This is where you cna set the class and Group for PagerDuty integration
                proc['Class'] = 'Process by CPU'
                proc['Group'] = ''
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        # Ensures that proc is not returned unless CPU_Usage is over 0
        # Returning usable data 
        if (bool(proc) and proc['CPU_Usage'] > 0.0):
                return proc

if __name__ == "__main__":
        # splits up the lookup and check of each process.
        # mp is for multiprocessing - pool will split based on how many processors there are
        pool = mp.Pool(mp.cpu_count())
        # pool.map will run the function GetProcessInformation on every item in psutil.pids.
        # List(filter()) will remove anything that returns 
        pid_list = list(filter(None, pool.map(GetProcessInformation, psutil.pids())))
        # Sorts pid_list by CPU_usage
        pid_list = sorted(pid_list, key = lambda i: i['CPU_Usage'],reverse=True)

        # Attempts to loop through the top five, if there is an out of bounds error then it will iterate
        # through whatever is in the list.
        try:
                for x in pid_list[5]:
                        print(x['Summary'], x['Source'], x['Severity'], x['Timestamp'], x['Class'], x['Component'], x['Group'], sep='\t')
        except IndexError:
                for x in pid_list:
                        print(x['Summary'], x['Source'], x['Severity'], x['Timestamp'], x['Class'], x['Component'], x['Group'], sep='\t')