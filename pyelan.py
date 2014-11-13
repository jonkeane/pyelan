import sys, os, datetime
from elementtree import ElementTree

#import tk if it exists. This import might not actually be necesary in pyelan anymore (it might be legacy from fflipper)
try:
    import tkMessageBox
except ImportError:
    pass

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

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
        

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
    def __init__(self, file=None, media=None, linkedFiles=[None], tiers=None, pathELAN=None):
        if file:
            tiers,media,linkedFiles = self.extractTiers(file)
            pathELAN = os.path.dirname(file)
        self.media = media
        self.linkedFiles = linkedFiles
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
        
        # Find any linked files
        linkedFiles = header[0].findall('LINKED_FILE_DESCRIPTOR')
        if len(linkedFiles) > 0:
            linkedFilePaths = []
            for linkedFile in linkedFiles:
                linkedFilePaths.append(linkedFile.attrib['LINK_URL'])
        else:
            linkedFilePaths = None
        
        # remove "file://" from the path
        mediaPath = mediaPath[7:]
        return clipTiers,mediaPath,linkedFilePaths

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

    def elanOut(tierObj, headFootFile = os.path.join(os.path.dirname(__file__),"elanSkeleton.eaf"), dest = "./out.eaf"):
        """An unbound function that returns an elan file from a tier."""
        verbose = False
        tree = ElementTree.parse(headFootFile)
        root = tree.getroot()
        destDir = os.path.dirname(os.path.abspath(dest))
        
        # Set media for the elan file
        newMedia = tierObj.media
        tree = ElementTree.ElementTree(root)
        header = root.findall('HEADER')
        media = ElementTree.SubElement(header[0], 'MEDIA_DESCRIPTOR')
        media.set('MEDIA_URL', ''.join(["file://",os.path.abspath(newMedia)]))
        media.set('MIME_TYPE', 'video/*')
        media.set('RELATIVE_MEDIA_URL', ''.join(["./",os.path.relpath(os.path.abspath(newMedia), destDir)]))
        
        # Set the link
        linkedFiles = tierObj.linkedFiles
        for fl in linkedFiles:
            media = ElementTree.SubElement(header[0], 'LINKED_FILE_DESCRIPTOR')
            media.set('LINK_URL', ''.join(["file://",os.path.abspath(fl)]))
            media.set('MIME_TYPE', 'unknown') # change to read file extension?
            media.set('RELATIVE_LINK_URL', ''.join(["./",os.path.relpath(os.path.abspath(fl), destDir)]))
        
        time_order = root[1]

        #----------------------------------------------------
        # build the tiers from the contents of nuTiers
        #----------------------------------------------------            
        knownTiers = {}
        tslt = 0
        anot = 0
        
        if tierObj.tiers != None:
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
        
def pfsxOut(tsConfigs):
        """An unbound function that returns the pfsx file for the list of TS configs given"""
        verbose = False

        
        # Set media for the elan file
        tree = ElementTree.ElementTree()
        root = ElementTree.Element("preferences")
        root.set('version', "1.1")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:noNamespaceSchemaLocation", "http://www.mpi.nl/tools/elan/Prefs_v1.1.xsd")
        nTSes = 0
        for trackSet in tsConfigs:
            for track in trackSet:
                nTSes += 1
                trackPrefList = ElementTree.SubElement(root, 'prefList')
                # get rid of the number in the track number, and assign a new (global) one instead
                trackPrefList.set('key', '-'.join([track.split("-")[0], str(nTSes)]))
                val = ElementTree.SubElement(trackPrefList, 'String')
                val.text = trackSet[track]
                
        pref = ElementTree.SubElement(root, 'pref')
        pref.set('key', "TimeSeriesViewer.NumberOfPanels")
        int = ElementTree.SubElement(pref, 'Int')
        int.text = str(nTSes)
        
        tree = ElementTree.ElementTree(root)
        # for pretty printing
        indent(root)
                
        return tree        
        
        
        
        
class track:
    """A track"""
    def __init__(self, name, column, row=0, range=[None, None], color=[0,0,0], properties=None, derivative=0):
        self.name = name
        self.column = column
        self.row = row    
        self.range = range
        self.color = color
        self.properties = properties
        self.derivative = derivative
        
        
        
class timeSeries:
    """A time series either from a file, or from individual specification"""
    def __init__(self, file=None, source=None, sampleType="Continuos Rate", timeCol=0, tracks=None):
        if file:
            # this needs to be updated
            source, sampleType, tracks = self.extractTimeSeries(file)
            pathELAN = os.path.dirname(file)
        self.source = source
        self.sampleType = sampleType
        self.tracks = tracks
        self.timeCol = timeCol

    def extractTimeSeries(self, file):
        """A function that extracts information from an already existing TS file. To do"""
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
        
        # Find any linked files
        linkedFiles = header[0].findall('LINKED_FILE_DESCRIPTOR')
        if len(linkedFiles) > 0:
            linkedFilePaths = []
            for linkedFile in linkedFiles:
                linkedFilePaths.append(linkedFile.attrib['LINK_URL'])
        else:
            linkedFilePaths = None
        
        # remove "file://" from the path
        mediaPath = mediaPath[7:]
        return clipTiers,mediaPath,linkedFilePaths 
        
    def timeSeriesOut(tsObj):
        """An unbound function that returns the time series configuration file for the ts object"""
        verbose = False

        
        # Set media for the elan file
        tree = ElementTree.ElementTree()
        root = ElementTree.Element("timeseries")
        dt = str(datetime.datetime.now()).replace(" ","T")
        root.set('date', dt)
        root.set('version', "1.0")
        tracksource = ElementTree.SubElement(root, 'tracksource')
        tracksource.set('sample-type', tsObj.sampleType)
        tracksource.set('source-url', ''.join(["file://",os.path.abspath(tsObj.source)]))
        tracksource.set('time-column', str(tsObj.timeCol))
        
        prop = ElementTree.SubElement(tracksource, 'property')
        prop.set('key', "provider")
        prop.set('value', "mpi.eudico.client.annotator.timeseries.csv.CSVServiceProvider")
 
        # Set the link
        tracks = tsObj.tracks
        pfsxPrefs = {}
        pfsxn = 1
        for track in tracks:
            trck = ElementTree.SubElement(tracksource, 'track')
            trck.set('derivative', str(track.derivative))
            trck.set('name', track.name)
            
            pfsxPrefs['-'.join(['TimeSeriesViewer.Panel',str(pfsxn)])] = track.name
            pfsxn += 1
            
            for propert in track.properties:
                prop = ElementTree.SubElement(trck, 'property')
                prop.set('key', propert)
                prop.set('value', track.properties[propert])
                
            samplePosition = ElementTree.SubElement(trck, 'sample-position')
            pos = ElementTree.SubElement(samplePosition, 'pos')
            pos.set('col', str(track.column))
            pos.set('row', str(track.row))
            
            desc = ElementTree.SubElement(trck, 'description')
            units = ElementTree.SubElement(trck, 'units')

            range = ElementTree.SubElement(trck, 'range')
            range.set('max', str(track.range[1]))
            range.set('min', str(track.range[0]))  
                      
            color = ElementTree.SubElement(trck, 'color')
            color.text = ','.join([str(i) for i in track.color])
        
        tree = ElementTree.ElementTree(root)
        # for pretty printing
        indent(root)
                
        return tree,pfsxPrefs         

 

