import sys, os
import tkMessageBox
from elementtree import ElementTree


#-------------------------------------------------------------------------------
# Extract annotations from all tiers .eaf file (which is an XML file)
# creates a dictionary where each key is a tier name mapped to a list of tuples
# that include each annotation
#-------------------------------------------------------------------------------

class annotation:
    """A single annotation that has a beginning, an ending, an annotation value, and a unit type (default is milliseconds"""
    def __init__(self, begin, end, value, units="ms"):
        self.begin = begin
        self.end = end
        self.value = value
        self.units = units
 
    def millisToFrames(self, fps = (60.*(1000./1001.))):
        """Converts a tuple (in milliseconds) into frames given a frame rate"""
        secsPerFrame = 1000./fps
        self.begin = int(float(self.begin)/secsPerFrame)
        self.end = int(float(self.end)/secsPerFrame)
        self.units = "frames"
        return
    
    def framesToMillis(self, fps = (60.*(1000./1001.))):
        """Converts a tuple (in frames) into milliseconds given a frame rate"""
        secsPerFrame = 1000./fps
        self.begin = int(float(self.begin)*secsPerFrame)
        self.end = int(float(self.end)*secsPerFrame+secsPerFrame)
        self.units = "ms"
        return

class tier:
    """A whole tier from ELAN consisting of a tier name as well as the annotations associated with it."""
    def __init__(self, tierName, annotations):
        self.tierName = tierName
        self.annotations = annotations

class tierSet:
    """A Tier set either from a file, or from media, tiers, and a pathELAN"""
    def __init__(self, file=None, media=None, tiers=None, pathELAN=None):
        if file:
            tiers,media = self.extractTiers(file)
            pathELAN = os.path.dirname(file)
        self.media = media
        self.tiers = tiers
        self.pathELAN = pathELAN

        ### If media exists, try in the same folder as the elan file.:
        if os.path.isfile(media) == False:
            sameDirPath = os.path.join(pathELAN,os.path.basename(media))
            if os.path.isfile(sameDirPath) == False:
                #error if there are no tiers selected.
                ## commented to prevent tk from launching, but should be changed, how to check if tk is running?
                ## tkMessageBox.showwarning(
                ##     "No media found",
                ##     "Could not find the media attached to the ELAN file. Please open the ELAN file, find the media, and then save it again.")
                self.media = []
                self.tiers = tier
                self.pathELAN = []
                
            else:    
                self.media = sameDirPath

    def extractTiers(self, file):
        """A function that extracts the tiers from a file and creates a tierSet that includes everything in the file."""
        verbose = False
        tree = ElementTree.parse(file)
        root = tree.getroot()
        rootLen = len(root)    
        pairs = [(X.attrib['TIME_SLOT_ID'],X.attrib['TIME_VALUE']) for X in root[1]]
        timeDict = dict(pairs)
        if verbose: print(timeDict)
        clipTiers = []
        for tierFound in root.findall('TIER'):
            if verbose: print( tierFound.attrib['TIER_ID'])
            annos = []
            for xx in tierFound:
                time1 = timeDict[xx[0].attrib['TIME_SLOT_REF1']]
                time2 = timeDict[xx[0].attrib['TIME_SLOT_REF2']]
                value = xx[0][0].text
                annos.append(annotation(int(time1), int(time2), value))
            clipTiers.append(tier(tierFound.attrib['TIER_ID'],annos))
        if clipTiers == []:
            print("No tier named 'Clips', please supply an eaf with one to segment on.")
            exit
        # Find the media file
        # check? <HEADER MEDIA_FILE="" TIME_UNITS="milliseconds">
        header = root.findall('HEADER')
        media = header[0].findall('MEDIA_DESCRIPTOR')
        mediaPath = media[0].attrib['MEDIA_URL']
        # remove "file://" from the path
        mediaPath = mediaPath[7:]
        return clipTiers,mediaPath

    def selectedTiers(tierObj, tierNames):
        """An unbound function that extracts the tiers given in the list tierNames"""
        media = tierObj.media
        tiers = tierObj.tiers
        pathELAN = tierObj.pathELAN
        newTiers = []        
        for tr in tiers:
            if tr.tierName in tierNames:
                newTiers.append(tr)
        tiers = newTiers    
        return tierSet(file=None, media=media, tiers=tiers, pathELAN=pathELAN)
    
    def miniTier(tierObj, begin, end):
        """An unbound function that extracts a subset of a tier"""
        media = tierObj.media
        tiers = tierObj.tiers
        pathELAN = tierObj.pathELAN
        newTiers = []        
        for tr in tiers:
            newAnnotations = []
            newTierName = tr.tierName
            for anno in tr.annotations:
                if anno.begin >= begin and anno.end <= end:
                    print("I added "+anno.value+": "+str(anno.begin)+"-"+str(anno.end))
                    newAnnotations.append(anno)
                ## else:
                ##     print("Skipping, out of bounds.")
            newTiers.append(tier(tierName=newTierName, annotations= newAnnotations))
        tiers = newTiers    
        return tierSet(file=None, media=media, tiers=tiers, pathELAN=pathELAN)
