#run WizTree on all available disks
choco install wiztree
.\WizTree.exe "C:" /admin=1 /export="C:\temp\WizTree\WizTreeExport.csv"

#run Python script against all reports
python check_disk_all.py -w 20 -c 15 -f "C:\temp\WizTree\WizTreeExport.csv" -n 5

#Remove WizTree report
Remove-Item -path "C:\TempWizTree" -Recurse