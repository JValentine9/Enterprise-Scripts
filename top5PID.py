import psutil
import platform
import argparse
import sys, socket, math
import time
import multiprocessing as mp
from datetime import datetime
from influx_line_protocol import Metric, MetricCollection



args = argparse.ArgumentParser(description='Get error and warning thresholds and can set output to influx line protocol')
args.add_argument("-w","--warning",help="Percent total cpu host utilization above which a warning is generated (i.e. 90)",type=float, required=True)
args.add_argument("-c","--critical",help="Percent total cpu host utilization above which a critical error is generated(i.e. 100)",type=float, required=True)
args.add_argument('-i', '--influxout', help='Set output to be in influx line protocol', action='store_true')

args = args.parse_args()

def influxOutput(proc):
        now = datetime.now()
        metric = Metric("PID_CPU_usage")
        metric.with_timestamp(datetime.timestamp(now))
        metric.add_tag('host', socket.gethostname())
        metric.add_tag('platform', platform.platform())
        
        for k,v in zip(proc.keys(),proc.values()):
                if type(v) is float:
                        metric.add_value(k,v)
                if type(v) is str:
                        metric.add_tag(k,v)
        print(metric)



def setSeverity(cpu_percent, pname, pID):
        '''
        Compares system CPU times elapsed before and after interval. Should be at least .1
        Pass in CPU_Percent to compare against and the Process's name to attach to summary.
        '''


        if cpu_percent >= args.warning and cpu_percent < args.critical:
                return 'WARNING', 'CPU utilization at %s percent on %s %s'%(cpu_percent, pname, pID)
                #sys.exit(1)
        elif cpu_percent >= args.critical:
                return 'CRITICAL', 'CPU utilization at %s percent on %s %s'%(cpu_percent, pname, pID)
                #sys.exit(2)
        else:
                return 'OK', 'CPU utilization at %s percent on %s %s'%(cpu_percent, pname, pID)
                #sys.exit(0)


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
        proc = {}
        try:
                p = psutil.Process(p)
                # Sets the proc to a dictionary with the Process information
                # pid, name, & username are attributes that are attached to a process
                proc['PID'], proc['Process'], proc['User'] = p.pid, p.name(), p.username()

                # Creates a reference point for the process's CPU checks
                #p.cpu_percent(interval=CPU_INTERVAL)

                # Does the second CPU check and records it to the dictionary
                proc['CPU_Usage'] = p.cpu_percent(interval=CPU_INTERVAL)
                
                # Checks and records the severity and summary with the setSeverity()
                proc['Severity'], proc['Summary'] = setSeverity(proc['CPU_Usage'], proc['Process'], proc['PID'])
                
                # Gets current timestamp, hostname & IP
                proc['Timestamp'] = datetime.utcnow().isoformat() + 'Z'
                proc['Source'] = socket.gethostname()
                
                # This is where you cna set the class and Group for PagerDuty integration
                proc['Class'] = 'Process by CPU'
                proc['Group'] = ''
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Ensures that proc is not returned unless CPU_Usage is over 0
        # Returning usable data 
        if (bool(proc) and proc['CPU_Usage'] > 0.0 ):
                return proc

def main():
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
                if (args.influxout):
                        influxOutput(pid_list[x])
                else:
                        # Prints the summary, source, severity, timestamp, procname with PID, and Group(blank)
                        print(pid_list[x]['Summary'], pid_list[x]['Source'], pid_list[x]['Severity'], pid_list[x]['Timestamp'], pid_list[x]['Class'], pid_list[x]['Process'] + ' - ' + str(pid_list[x]['PID']), pid_list[x]['Group'], sep='\t')
                
                if (x == 4): break
        # If statement occurs when pid_list does not have at least 5 entries, this allows for 
        # 5 print outs to keep the top5 format
        if (len(pid_list) < 5):
                x = len(pid_list)
                while(x < 5):
                        print('-', '-', '-', '-', '-', '-', sep='\t')
                        x += 1
        sys.exit(0)

if __name__ == '__main__':
        main()