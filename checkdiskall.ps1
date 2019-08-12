.\WizTree64.exe "C:" /admin=1 /export="C:\temp\WizTreeExport.csv"
python check_disk_all.py -w 20 -c 15
Remove-Item -path "C:\Temp\WizTreeExport.csv"