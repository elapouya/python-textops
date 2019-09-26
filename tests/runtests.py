import doctest
from textops import *
import os
import json
import sys

modules = [ 'textops.base',
            'textops.ops.cast',
            'textops.ops.fileops',
            'textops.ops.listops',
            'textops.ops.parse',
            'textops.ops.recode',
            'textops.ops.runops',
            'textops.ops.strops',
            'textops.ops.wrapops',
            ]
files = [ 'docs/intro.rst' ]

failed = 0
tested = 0

REPORT = doctest.REPORT_NDIFF
if len(sys.argv) > 1 and sys.argv[1] == '-c':
    # report where there 2 entire blocks with ! to see differences
    # useful to cut&paste wanted result
    REPORT = doctest.REPORT_CDIFF

print '=' * 60

for m in modules:
    print 'Testing %s ...' % m
    mod = __import__(m,fromlist=[''])
    fcount, tcount = doctest.testmod(mod,globs=globals(),optionflags=REPORT)
    failed += fcount
    tested += tcount

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in files:
    print 'Testing %s ...' % f
    path = os.path.join(base_dir,f)
    fcount, tcount = doctest.testfile(path,False,globs=globals(),optionflags=REPORT)
    failed += fcount
    tested += tcount

print '=' * 60
print 'Number of tests : %s' % tested
print 'Failed : %s' % failed