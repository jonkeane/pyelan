import sys, os, re
import pyelan.pyelan as pyelan

# python realPathFix.py [search path] [files]
searchDir = sys.argv[1]

eafFiles = sys.argv[2:]
for eafFile in eafFiles:
    eafPath = os.path.dirname(eafFile)


    fl = pyelan.tierSet(file = eafFile)
    fl.fixLinks(searchDir = searchDir)

    for tsconf in filter(lambda s: re.match(".*tsconf.xml", s), fl.linkedFiles):
        ts = pyelan.timeSeries(file = tsconf)
        ts.fixLinks(searchDir = searchDir)
        tsOut = pyelan.timeSeries.timeSeriesOut(ts)
        tsOut[0].write(tsconf)

    eafOut = pyelan.tierSet.elanOut(fl, dest=eafPath)
    eafOut.write(eafFile)