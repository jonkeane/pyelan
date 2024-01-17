import sys, os, re, datetime, warnings
from importlib import resources as impresources
from . import templates
from xml.etree import ElementTree

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


def getRecDirStruct(rootdir):
    """
    Creates a nested dictionary that represents the folder structure of rootdir
    based loosely on code from http://code.activestate.com/recipes/577879-create-a-nested-dictionary-from-oswalk/
    """
    dir = []
    rootdir = rootdir.rstrip(os.sep)
    for path, dirs, files in os.walk(rootdir):
        [dir.append(os.path.join(path,file)) for file in files]
    return dir

def lcs(string1, string2):
    # from http://stackoverflow.com/questions/5267610/comparing-strings
    m = len(string1)
    n = len(string2)

    C = [[0] * (n + 1)] * (m + 1)
    for i in range(m + 1)[1:]:
        for j in range(n + 1)[1:]:
            if string1[i - 1] == string2[j - 1]:
                C[i][j] = C[i - 1][j - 1] + 1
            else:
                C[i][j] = max(C[i][j - 1], C[i - 1][j])
    return C[m][n]

def findPathMatch(oldPath, searchDir = "./"):
    dirContents = getRecDirStruct(searchDir)
    # print(dirContents)
    if os.path.isfile(oldPath) == False:
        # if the current path is not a valid path
        basename = os.path.basename(oldPath)

        # filter all of the files in the current directory that match the filename
        newPaths = filter(lambda s: re.match(os.path.sep.join((".*",basename)), s), dirContents)
        if len(newPaths) == 1:
            # if only one is found, make that the new path
            newPath = newPaths[0]
        elif len(newPaths) > 1:
            # determine which path matches more of the directory structure. This uses common strings, but not common contiguous strings. This should work in nearly all conditions, but there migth be edge cases where this fails.
            scores = [lcs(oldPath,pt) for pt in newPaths]
            newPath = newPaths[scores.index(max(scores))]
        elif len(newPaths) == 0:
            warnings.warn("Could not find any linked files for " + basename)
            newPath = oldPath
    else:
        newPath = oldPath
    return newPath

class annotation:
    """A single annotation that has a beginning, an ending, an annotation value, and a unit type (default is milliseconds"""
    def __init__(self, begin, end, value, units="ms"):
        self.begin = begin
        self.end = end
        if value != None:
            self.value = value.strip()
        else:
            self.value = value
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
    def __init__(self, file=None, media=[None], linkedFiles=[None], relLinkedFiles=[None], tiers=None, pathELAN=None):
        if file:
            tiers,media,relMedia,linkedFiles,relLinkedFiles = self.extractTiers(file)
            pathELAN = os.path.dirname(file)
        self.media = media
        self.linkedFiles = linkedFiles
        self.relLinkedFiles = relLinkedFiles
        self.tiers = tiers
        self.pathELAN = pathELAN

        ### If media does not exist, try in the same folder as the elan file.:
        newMedia = []
        for mediaFile in media:
            if os.path.isfile(mediaFile) == False:
                sameDirPath = os.path.join(pathELAN,os.path.basename(mediaFile))
                if os.path.isfile(sameDirPath) == False:
                    # self.mediaFile = []
                    # self.tiers = tier
                    # self.pathELAN = []
                    warnings.warn("Could not find the media file: "+mediaFile)
                    newMedia.append(mediaFile)

                else:
                    newMedia.append(sameDirPath)

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
            if verbose: print(tierFound.attrib['TIER_ID'])
            annos = []
            for xx in tierFound:
                time1 = timeDict[xx[0].attrib['TIME_SLOT_REF1']]
                time2 = timeDict[xx[0].attrib['TIME_SLOT_REF2']]
                value = xx[0][0].text
                if verbose: print(value)
                annos.append(annotation(int(time1), int(time2), value))
            if verbose: print(annos)
            clipTiers.append(tier(tierFound.attrib['TIER_ID'],annos))
        if clipTiers == []:
            print("No tier named 'Clips', please supply an eaf with one to segment on.")
            exit
        # Find the media file
        # check? <HEADER MEDIA_FILE="" TIME_UNITS="milliseconds">
        header = root.findall('HEADER')

        # Find any media files
        media = header[0].findall('MEDIA_DESCRIPTOR')
        if len(media) > 0:
            mediaPaths = []
            relMediaFilePaths = []
            for mediaFile in media:
                mediaPaths.append(mediaFile.attrib['MEDIA_URL'][7:]) # [7:] removes the file://
                if 'RELATIVE_MEDIA_URL' in mediaFile.attrib:
                    relMediaFilePaths.append(mediaFile.attrib['RELATIVE_MEDIA_URL'])
        else:
            mediaPaths = None
            relMediaFilePaths = None

        # Find any linked files
        linkedFiles = header[0].findall('LINKED_FILE_DESCRIPTOR')
        if len(linkedFiles) > 0:
            linkedFilePaths = []
            relLinkedFilePaths = []
            for linkedFile in linkedFiles:
                linkedFilePaths.append(linkedFile.attrib['LINK_URL'][7:]) # [7:] removes the file://
                if 'RELATIVE_LINK_URL' in linkedFile.attrib:
                    relLinkedFilePaths.append(linkedFile.attrib['RELATIVE_LINK_URL'])
        else:
            linkedFilePaths = None
            relLinkedFilePaths = None


        return clipTiers,mediaPaths,relMediaFilePaths,linkedFilePaths,relLinkedFilePaths

    def fixLinks(self, searchDir="./"):
        """A function that fixes links in an elan file by searching recursively through the search directory, and then links the best matches for each file."""
        self.media = [os.path.abspath(findPathMatch(path, searchDir=searchDir)) for path in self.media]
        self.linkedFiles = [os.path.abspath(findPathMatch(path, searchDir=searchDir)) for path in self.linkedFiles]



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

    def elanOut(tierObj, headFootFile = (impresources.files(templates) / "elanSkeleton.eaf"), dest = "./out.eaf"):
        """An unbound function that returns an elan file from a tier."""
        verbose = False
        tree = ElementTree.parse(headFootFile)
        root = tree.getroot()
        destDir = os.path.dirname(os.path.abspath(dest))

        # Set media for the elan file
        mediaFiles = tierObj.media
        tree = ElementTree.ElementTree(root)
        header = root.findall('HEADER')

        for mediaFile in mediaFiles:
            media = ElementTree.SubElement(header[0], 'MEDIA_DESCRIPTOR')
            media.set('MEDIA_URL', ''.join(["file://",os.path.abspath(mediaFile)]))
            if os.path.splitext(mediaFile)[1] == ".wav":
                media.set('MIME_TYPE', 'audio/*')
            else:
                media.set('MIME_TYPE', 'video/*')
            media.set('RELATIVE_MEDIA_URL', ''.join(["./",os.path.relpath(os.path.abspath(mediaFile), destDir)]))

        # Set the link
        linkedFiles = tierObj.linkedFiles
        if linkedFiles is not None and linkedFiles != [None]:
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

                #----------------------------------------------------
                for anno in tier.annotations:
                    if verbose: print("Working on time slot: "+str(tslt)+" and annotation: "+str(anot))
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
                    annotation = ElementTree.SubElement(tierNode, "ANNOTATION")
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
        root = indent(root)

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
    # this should be seperated to allow for multiple tracksources in a single timeseries (conf) file.
    def __init__(self, file=None, source=None, timeOrigin=None, sampleType="Continuos Rate", timeCol=0, tracks=None):
        if file:
            source, sampleType, tracks, timeCol, timeOrigin = self.extractTimeSeries(file)
            pathELAN = os.path.dirname(file)
        self.source = source
        self.sampleType = sampleType
        self.tracks = tracks
        self.timeCol = timeCol
        self.timeOrigin = timeOrigin

    def extractTimeSeries(self, file):
        """A function that extracts information from an already existing TS file. To do"""
        verbose = False
        tree = ElementTree.parse(file)
        root = tree.getroot()
        rootLen = len(root)
        # get track source
        tracksource = root.findall("tracksource")[0] # maybe check how many there are. There should only ever be one.
        source = tracksource.attrib['source-url'][7:] # the [7:] removes the file://
        sampleType = tracksource.attrib['sample-type']
        timeCol = int(tracksource.attrib['time-column'])
        try:
            timeOrigin = float(tracksource.attrib['time-origin'])
        except KeyError:
            timeOrigin = None

        # get individual tracks
        tracks = tracksource.findall("track")
        trackList = []
        for trk in tracks:
            deriv = trk.attrib['derivative']
            name = trk.attrib['name']
            props = trk.findall("property")
            properties = {}
            for prop in props:
                properties[prop.attrib['key']] = prop.attrib['value']
            samplePos = trk.findall("sample-position")[0] # should be only one
            pos = samplePos.findall('pos')[0] # should be only one
            column = pos.attrib['col']
            row = pos.attrib['row']
            range = trk.findall("range")[0] # should be only one
            max = range.attrib['max']
            min = range.attrib['min']
            color = trk.findall("color")[0] # should be only one
            color = [int(i) for i in color.text.split(',')]
            range = [min,max]
            trackList.append(track(name, column, row, range, color, properties, deriv))
        return source, sampleType, trackList, timeCol, timeOrigin

    def fixLinks(self, searchDir="./"):
        """A function that fixes links in a tsconf file by searching recursively through the search directory, and then links the best matches for each file."""
        self.source = os.path.abspath(findPathMatch(self.source, searchDir=searchDir))

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
        if tsObj.timeOrigin:
            tracksource.set('time-origin', str(tsObj.timeOrigin))


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
        root = indent(root)

        return tree,pfsxPrefs
