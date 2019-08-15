#run WizTree on all available disks

.\WizTree64.exe "C:" /admin=1 /export="C:\temp\WizTree\WizTreeExport.csv"

#run Python script against all reports
python check_disk_all.py -w 20 -c 15

#Remove WizTree report
Remove-Item -path "C:\Temp\WizTree" -Recurse