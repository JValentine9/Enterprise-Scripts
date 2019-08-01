#!/usr/bin/env python3
"""
=========================================================================
treesize.py - find large folders and files
Version 1.1, June 2017 (1.0, June 2015)
Author: M. Lutz (learning-python.com), © 2015-2017
License: Provided freely, but with no warranties of any kind.

Given a root folder path, report on the total size taken by each of
its folders (directories), subfolders, and files.  Walks folder tree
recursively to tally total size taken by each folder.

The report is grouped by directories and files (listing all of each
kind in a separate section), and each group is ordered by decreasing
sizes.  It's intended to help isolate items for removal to regain drive
space.  Items of unknown type or permission errors are skipped, and the
report file is saved to '.' - the folder from which the script is run.

Input arguments (in this order):
  - Root-Path -- path name of the tree's topmost directory (e.g., C:\)
  - Report-File-Suffix -- text added to end of the report file's name 
  - Display-At-End -- 'y' or 'yes' to echo report to standard output

These may be passed in on the command line or entered interactively;
the latter scheme is used automatically if no command-line arguments.
This script requires Python 3.X (but could support 2.X easily).

Usage Notes:

1) In the report file, search on "[Files]" to go to the files section,
and "[Directories]" to jump to the folders section.

2) Setting Display-At-End to 'y' (true) for large scans may print a
very large amount of text to the screen (a "C:\" scan on the author's
machine yields a 373K-line report file).  View the report file instead.

3) If Report-File-Suffix is an empty string (a "" in a Windows command
line, or an Enter press on interactive prompt), the suffix defaults to
the rightmost folder name in Root-Path, if any (else 'root' for "C:\").
For example: to use the folder name SPAM for the report suffix and not
echo the report, use a command (or equivalent inputs) of this form:

      py -3 treesize.py C:\WorkingFolder\SPAM "" n

4) Don't end the Root-Path with a slash or backslash, unless it is
required drive syntax (e.g., "C:\" requires "\" per the next note).

5) On Windows, a Root-Path "C:\" always means the whole C drive.  A
"C:" means just the script's folder in some run contexts (e.g., clicks).

6) If your file explorer's tallies differ from the results here, it's
likely due to different handling of symlinks and ".*" Unix hidden files;
treesize always skips the former and includes the latter.  treesize
results do agree exactly with Unix "find" tallies for "-type d" dirs 
and "-type f" files (e.g., "find somedir -type f | wc -l" for #files).

Caveats:

1) This could allow for long Windows paths the way that mergeall
and ziptools now do (see learning-python.com/programs.html).  In
short, a '\\?\' prefix lifts Windows' 260-ish character path limits;
add this to all paths sent to system calls on Windows only.

2) [Closed] This follows symlinks naively, which can inflate sizes 
on machines and folders that have these.  See mergeall and ziptools
of the prior paragraph for better approaches.  This may also need
to detect cycles on some platforms with links (see ziptools).

    UPDATE: as of 1.1 this now simply skips symlinks altogether, but
    does not trap cycles (see ziptools for a technique that does so). 
    Linkfile size is not in the tally, but it's normally trivial.

3) Python 3.5's new os.scandir() alternative to os.listdir() might
make this script run faster, albeit at the cost of some minor recoding,
and a major loss of portability (the script would run on 3.5+ only).
=========================================================================
"""
import os, sys

trace  = lambda *pargs, **kargs: None    # or print or report
error  = lambda *pargs, **kargs: print(*pargs, file=sys.stderr, **kargs)
report = lambda *pargs, **kargs: print(*pargs, file=reportfile, **kargs)
prompt = lambda text: input(text + ' ')
reportfile = sys.stdout   # reset in main or callers as needed


def treesize(root, alldirs, allfiles, counts):
    """
    sum and return all space taken up by root (all its files + subdirs);
    record sizes by pathname in-place in alldirs+allfiles: [(path, size)];
    also tally dir/folder counts in-place in counts: [numdirs, numfiles]; 
    """
    sizehere = 0
    try:
        allhere = os.listdir(root)
    except:
        allhere = []
        error('Error accessing dir (skipped):', root)   # e.g., recycle bin

    for name in allhere:
        path = os.path.join(root, name)

        if os.path.islink(path):
           trace('skipping link:', path)   # [1.1]

        elif os.path.isfile(path):
            trace('file:', path)
            counts[1] += 1
            filesize = os.path.getsize(path)
            allfiles.append((path, filesize))
            sizehere += filesize
            
        elif os.path.isdir(path):
            trace('subdir', path)
            counts[0] += 1
            subsize = treesize(path, alldirs, allfiles, counts)
            sizehere += subsize

        else:
            error('Unknown file type (skipped):', path)   # fifo, etc.

    alldirs.append((root, sizehere))
    return sizehere


def genreport(toproot, totsize, alldirs, allfiles, counts):
    """
    print report to file, using commas and uniform-widths for numbers;
    caller should first set reportfile global unless routing to stdout;
    """
    report('\nTotal size of {}: {:,}'.format(toproot, totsize))
    report('    in {:,} dirs and {:,} files'.format(*counts))

    for (title, allitems) in [('Directories', alldirs), ('Files', allfiles)]:
        report('\n%s\n[%s]\n%s\n' % ('-' * 80, title, '-' * 80))
        
        allitems.sort(key=lambda pair: pair[1])   # sort by ascend size
        allitems.reverse()                        # order largest first
        
        maxsize = max(len('{:,}'.format(size)) for (path, size) in allitems)
        for (path, size) in allitems:
            report('{:,}'.format(size).rjust(maxsize), '=>', path)

    report('\n[End]')
    reportfile.close()   # flush output now


if __name__ == '__main__':
    # configure run
    if len(sys.argv) == 4:
        toproot, reportsuffix, showreport = sys.argv[1:]
    else:
        toproot = prompt('Root directory path?')
        reportsuffix = prompt('Report filename suffix (empty=use folder name)?')
        showreport = prompt('Show report on stdout at end (true: y or yes)?')

    if not os.path.isdir(toproot):
        error('Error: root path does not name a valid directory; run cancelled.')
        if sys.platform.startswith('win'): prompt('Press Enter.')   # clicked?
        sys.exit(1)
        
    if not reportsuffix:                         
        # use input or dir name
        if toproot.endswith('/') and len(toproot) > 1:
            toproot = toproot[:-1]               # unix: ends in '/' but not only
        rightmost = os.path.split(toproot)[-1]   # but no dir name for C:\
        reportsuffix = rightmost or 'root'

    showreport = showreport.lower() in ['y', 'yes']
        
    # collect sizes
    alldirs, allfiles = [], []
    counts = [1, 0]
    totsize = treesize(toproot, alldirs, allfiles, counts)
    assert counts[0] == len(alldirs) and counts[1] == len(allfiles) 

    # report results
    reportname = 'treesize-report-%s.txt' % reportsuffix
    reportfile = open(reportname, mode='w', encoding='utf8')
    genreport(toproot, totsize, alldirs, allfiles, counts)

    # echo report file?
    if showreport:
        for line in open(reportname, encoding='utf8'):   # show file on stdout
            print(line, end='')                          # by line, else delay?
        if sys.platform.startswith('win'):
            prompt('Press Enter.')   # stay open if Windows click; or isatty()?