import psutil
import argparse
import sys, time, os, datetime, socket
import multiprocessing as mp

parser = argparse.ArgumentParser(description='Get error and warning thresholds')
parser.add_argument("-w","--warning",help="Percent total cpu host utilization above which a warning is generated (i.e. 90)",type=float, required=True)
parser.add_argument("-c","--critical",help="Percent total cpu host utilization above which a critical error is generated(i.e. 100)",type=float, required=True)

args = parser.parse_args()
now = datetime.datetime.now()

#Compares system CPU times elapsed before and after interval. Should be at least .1


def setSeverity(cpu_percent, pname, pID):
        '''
        Compares system CPU times elapsed before and after interval. Should be at least .1
        Pass in CPU_Percent to compare against and the Process's name to attach to summary.
        '''
        cpu_pct = cpu_percent


        if cpu_pct >= args.warning and cpu_pct < args.critical:
                return 'WARNING', 'CPU utilization at %s percent on %s %s'%(cpu_pct, pname, pID)
                #sys.exit(1)
        elif cpu_pct >= args.critical:
                return 'CRITICAL', 'CPU utilization at %s percent on %s %s'%(cpu_pct, pname, pID)
                #sys.exit(2)
        else:
                return 'OK', 'CPU utilization at %s percent on %s %s'%(cpu_pct, pname, pID)
                #sys.exit(0)

#proc = collections.OrderedDict()
def GetProcessInformation(p):
        '''
        Passes in a PID to then returns process information as dict.
        Information includes: PID, Component(name), User,
        CPU_Usage(interval=1), Severity, Summary, Timestamp,
        Source, Class, and Group
        '''
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
                #p.cpu_percent(interval=CPU_INTERVAL)

                # Does the second CPU check and records it to the dictionary
                proc['CPU_Usage'] = p.cpu_percent(interval=CPU_INTERVAL)
                
                # Checks and records the severity and summary with the setSeverity()
                proc['Severity'], proc['Summary'] = setSeverity(proc['CPU_Usage'], proc['Component'], proc['PID'])
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
        if (bool(proc) and proc['CPU_Usage'] > 0.0 ):
                return proc

if __name__ == '__main__':
        # splits up the lookup and check of each process.
        # mp is for multiprocessing - pool will split based on how many processors there are
        pool = mp.Pool(mp.cpu_count())
        # pool.map will run the function GetProcessInformation on every item in psutil.pids.
        # List(filter()) will remove anything that returns 
        pid_list = list(filter(None, pool.map(GetProcessInformation, psutil.pids())))
        # Sorts pid_list by CPU_usage
        pid_list = sorted(pid_list, key = lambda i: i['CPU_Usage'],reverse=True)

        # To avoid a potential index error run loop through a range of the pid_list length.
        # Breaks out of loop after 5 prints, i.e top five processes.
        for x in range(len(pid_list)):
                # Prints the summary, source, severity, timestamp, procname with PID, and Group(blank)
                print(pid_list[x]['Summary'], pid_list[x]['Source'], pid_list[x]['Severity'], pid_list[x]['Timestamp'], pid_list[x]['Class'], pid_list[x]['Component'] + ' - ' + str(pid_list[x]['PID']), pid_list[x]['Group'], sep='\t')
                if (x == 4): break
        # If statement occurs when pid_list does not have at least 5 entries, this allows for 
        # 
        if (len(pid_list) < 5):
                x = len(pid_list)
                while(x < 5):
                        print('Summary Placeholder', 'Source Placeholder', 'OK', 'Timestamp Placeholder', 'ProcName Placeholder', 'Group Placeholder',sep='\t')
                        x += 1
        