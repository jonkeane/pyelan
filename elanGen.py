import sys, re, os, csv, json
import pyelan as pyelan

# python elanGen.py "./clippedData/GRI_006-SESSION_001-TRIAL_002.mov" "elanFiles" '[{"file" : "./savedData/GRI_006/GRI_006-SESSION_001-TRIAL_002.csv", "tracks" : [{"name": "clapper", "column": 36, "min":0, "max":200}, {"name": "grip", "column": 35, "min":0, "max":200}]}]'

media = sys.argv[1]
basename = os.path.splitext(os.path.basename(media))[0]
saveDir = sys.argv[2]
csvsToLink = json.loads(sys.argv[3])

filesToLink = []
for csv in csvsToLink:
    csvFile = csv["file"]
    filesToLink.append(csvFile)
    # generate a new:
    tracks = []
    for track in csv["tracks"]:
        tracks.append(pyelan.track(name=track["name"], column=track["column"], row=0, range=[track["min"],track["max"]], properties={"detect-range": "true"}))
    linkedfile = pyelan.timeSeries(source=csvFile, sampleType="Continuous Rate", timeCol=0, tracks=tracks)
    out, pfsx = pyelan.timeSeries.timeSeriesOut(linkedfile)    
    
    csvBasename = os.path.splitext(os.path.basename(csvFile))[0]
    
    xmlOut = os.path.join(saveDir,'.'.join(['_'.join([csvBasename,"tsconf"]),"xml"]))
    out.write(xmlOut)
    filesToLink.append(xmlOut)
    

    pfsxfile =  pyelan.pfsxOut([pfsx])
    pfsxOut = os.path.join(saveDir,'.'.join([basename,"pfsx"]))
    
    pfsxfile.write(pfsxOut)


allTiers = pyelan.tierSet(media=media, linkedFiles=filesToLink, tiers=[pyelan.tier("default", [pyelan.annotation(begin=1, end=2, value="foo")])])

elanOut = os.path.join(saveDir,'.'.join([basename,"eaf"]))

out = pyelan.tierSet.elanOut(allTiers, dest=elanOut)

out.write(elanOut)



