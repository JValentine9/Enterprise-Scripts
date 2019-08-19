import psutil
import platform
import argparse
import sys, socket
import time
from datetime import datetime
from influx_line_protocol import Metric, MetricCollection



args = argparse.ArgumentParser(description='Get error and warning thresholds and can set output to influx line protocol')
args.add_argument("-w","--warning",help="Percent total cpu host utilization above which a warning is generated (i.e. 90)",type=float, required=True)
args.add_argument("-c","--critical",help="Percent total cpu host utilization above which a critical error is generated(i.e. 100)",type=float, required=True)
args.add_argument('-i', '--influxout', help='Set output to be in influx line protocol', action='store_true')

args = args.parse_args()

def influxOutput(proc):
        now = datetime.now()
        metric = Metric("host_pid_cpu_usage")
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
        Compares system CPU times elapsed before and after interval.
        Pass in CPU_Percent to compare against and the Process's name to attach to summary.
        '''
        if cpu_percent >= args.warning and cpu_percent < args.critical:
                return 'WARNING', 'CPU\ utilization\ at\ %s\ percent\ on\ %s\ %s'%(cpu_percent, pname, pID)
                #sys.exit(1)
        elif cpu_percent >= args.critical:
                return 'CRITICAL', 'CPU\ utilization\ at\ %s\ percent\ on\ %s\ %s'%(cpu_percent, pname, pID)
                #sys.exit(2)
        else:
                return 'OK', 'CPU\ utilization\ at\ %s\ percent\ on\ %s \%s'%(cpu_percent, pname, pID)
                #sys.exit(0)

def hoglist(delay=5):
    '''Return a list of processes using a nonzero CPU percentage
       during the interval specified by delay (seconds),
       sorted so the biggest hog is first.
    '''
    proccesses = list(psutil.process_iter())
    for proc in proccesses:
        proc.cpu_percent(None)    # non-blocking; throw away first bogus value

    sys.stdout.flush()
    time.sleep(delay)

    procs = []
    for proc in proccesses:
        # Skip system idle process which is always pid 0.
        # System Idle process will always be the 'highest' cpu hog
        if (proc.pid == 0): continue
        # Skip python when running the program
        # if (proc.name() == 'python'): continue
        try:
                percent = proc.cpu_percent(None)
                #user = proc.username() == 'NT AUTHORITY SYSTEM' 
                severity, summary = setSeverity(percent, proc.name(), proc.pid)
                if percent:
                        procs.append({
                            'name': proc.name(),
                            'user': proc.username(),
                            'cpu_percent': percent,
                            'severity': severity,
                            'summary': summary,
                            'source': socket.gethostname(),
                            'class': 'Process\ by\ CPU',
                            # 'timestamp': datetime.utcnow().isoformat() + 'Z',          
                            # 'group': ''            
                            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    
    return procs

def main():
        pid_list = hoglist()
        pid_list.sort(key = lambda i: i['cpu_percent'], reverse=True)

        for x in range(len(pid_list)):
                influxOutput(pid_list[x]) if args.influxout else print(pid_list[x])
                if (x == 4): break
        if (len(pid_list) < 5):
                x = len(pid_list)
                while(x < 5):
                        print('-', '-', '-', '-', '-', '-', sep='\t')
                        x += 1
        sys.exit(0)

if __name__ == '__main__':
        main()