import psutil
import argparse
import sys

parser = argparse.ArgumentParser(description='Get error and warning thresholds')
parser.add_argument("-w","--warning",help="Percent total cpu host utilization above which a warning is generated (i.e. 90)",type=float)
parser.add_argument("-c","--critical",help="Percent total cpu host utilization above which a critical error is generated(i.e. 100)",type=float)

args = parser.parse_args()

#Compares system CPU times elapsed before and after interval. Should be at least .1
CPU_INTERVAL = 1

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