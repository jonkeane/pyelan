import sys, os
import tkMessageBox
from elementtree import ElementTree


class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class noMediaError(Error):
    """Exception raised for errors dealing with the media file.

    Attributes:
        filename -- the filename that is a problem
    """

    def __init__(self, filename):
        self.filename = filename
        

class annotation:
    """A single annotation that has a beginning, an ending, an annotation value, and a unit type (default is milliseconds"""
    def __init__(self, begin, end, value, units="ms"):
        self.begin = begin
        self.end = end
        self.value = value.strip()
        self.units = units
 
    def millisToFrames(self, fps = (60.*(1000./1001.))):
        """Converts a tuple (in milliseconds) into frames given a frame rate"""
        secsPerFrame = 1000./fps
        self.begin = int(float(self.begin)/secsPerFrame)
        self.end = int(float(self.end)/secsPerFrame)
        self.units = "frames"
        return self
    
    def framesToMillis(self, fps = (60.*(1000./1001.))):
        """Converts a tuple (in frames) into milliseconds given a frame rate"""
        secsPerFrame = 1000./fps
        # +1 to align with the next frame, not the last one.
        self.begin = int(float(self.begin)*secsPerFrame+1) 
        self.end = int(float(self.end)*secsPerFrame+secsPerFrame)
        self.units = "ms"
        return self

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

        ### If media does not exist, try in the same folder as the elan file.:
        if os.path.isfile(media) == False:
            sameDirPath = os.path.join(pathELAN,os.path.basename(media))
            if os.path.isfile(sameDirPath) == False:
                self.media = []
                self.tiers = tier
                self.pathELAN = []
                raise noMediaError(media)
                
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
    
    def miniTier(tierObj, begin, end, retimed = True):
        """An unbound function that extracts a subset of a tier"""
        verbose = False
        media = tierObj.media
        tiers = tierObj.tiers
        pathELAN = tierObj.pathELAN
        newTiers = []
        if retimed:
            tZero = begin
        else:
            tZero = 0
        if verbose: print("Zero: ",str(tZero))
        for tr in tiers:
            newAnnotations = []
            newTierName = tr.tierName
            for anno in tr.annotations:
                if anno.begin >= begin and anno.end <= end:
                    newAnno = annotation(anno.begin-tZero, anno.end-tZero, anno.value, anno.units)
                    if verbose: print("I added "+newAnno.value+": "+str(newAnno.begin)+"-"+str(newAnno.end))
                    newAnnotations.append(newAnno)
                ## else:
                ##     print("Skipping, out of bounds.")
            newTiers.append(tier(tierName=newTierName, annotations= newAnnotations))
        tiers = newTiers    
        return tierSet(file=None, media=media, tiers=tiers, pathELAN=pathELAN)

    def elanOut(tierObj, headFootFile = os.path.join(os.path.dirname(__file__),"elanSkeleton.eaf")):
        """An unbound function that returns an elan file from a tier."""
        verbose = False
        tree = ElementTree.parse(headFootFile)
        root = tree.getroot()
        time_order = root[1]

        #----------------------------------------------------
        # build the tiers from the contents of nuTiers
        #----------------------------------------------------            
        knownTiers = {}
        tslt = 0
        anot = 0

        for tier in tierObj.tiers:
            if verbose: print(tier.tierName)
            workingTier = tier.tierName
            #----------------------------------------------------
            # Create a tier
            #----------------------------------------------------            
            tierNode = ElementTree.SubElement(root, "TIER")
            tierNode.attrib["ANNOTATOR"] = 'annoCompare'
            tierNode.attrib["DEFAUTL_LOCALE"] = "en"
            tierNode.attrib["LINGUISTIC_TYPE_REF"] = "default-lt"
            tierNode.attrib["TIER_ID"] = workingTier
            
            annotation = ElementTree.SubElement(tierNode, "ANNOTATION")
            #----------------------------------------------------  
            for anno in tier.annotations:
                if verbose: print "Working on time slot: "+str(tslt)+" and annotation: "+str(anot)
                tslt += 1 
                time_slot_id0 = 'ts' + workingTier + str(tslt)
                time_value0 = str(anno.begin)
                time_slot = ElementTree.SubElement(time_order, "TIME_SLOT")
                time_slot.attrib["TIME_SLOT_ID"] = time_slot_id0
                time_slot.attrib["TIME_VALUE"] = time_value0
                    
                tslt += 1
                time_slot_id1 = 'ts' + workingTier + str(tslt) 
                # nx = int(float(nx)*1000)
                time_value1 = str(anno.end)
                time_slot = ElementTree.SubElement(time_order, "TIME_SLOT")
                time_slot.attrib["TIME_SLOT_ID"] = time_slot_id1
                time_slot.attrib["TIME_VALUE"] = time_value1
                
                anot += 1
                annotation_id = 'a' + str(anot)
                alignable_annotation = ElementTree.SubElement(annotation, "ALIGNABLE_ANNOTATION")
                alignable_annotation.attrib["ANNOTATION_ID"] = annotation_id
                alignable_annotation.attrib["TIME_SLOT_REF1"] = time_slot_id0
                alignable_annotation.attrib["TIME_SLOT_REF2"] = time_slot_id1

                anno_value = ElementTree.SubElement(alignable_annotation, "ANNOTATION_VALUE")
                anno_value.text = anno.value
                    
                if verbose: print(anno.value+": "+str(anno.begin)+"-"+str(anno.end))
        
        return tree

