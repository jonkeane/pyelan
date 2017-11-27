import sys, re, os, itertools, collections
import pyelan as pyelan

# python distance.py path/to/file.eaf path/to/file.eaf

def levenshtein(s1, s2):
    """Total Levenshtein distance between two strings
    
    Keyword arguments:
    s1 -- the first string
    s2 -- the second string
    """
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def totalLevenshtein(tier1, tier2):
    """Total Levenshtein distance between two tiers
    
    Keyword arguments:
    tier1 -- the first tier (of type pyelan.tier)
    tier2 -- the second tier (of type pyelan.tier)
    """
    
    tier1_string = "".join([anno.value for anno in tier1.annotations])
    tier2_string = "".join([anno.value for anno in tier2.annotations])
    return(levenshtein(tier1_string, tier2_string))

def overlappingAnnotationLevenshtein(tier1, tier2):
    """Levenshtein distance between two tiers for only those annotations which 
    overlap
    
    Keyword arguments:
    tier1 -- the first tier (of type pyelan.tier)
    tier2 -- the second tier (of type pyelan.tier)
    """
    
    # iterate over annotations and mark overlaps.
    matching_annos = []
    for anno1, anno2 in itertools.product(tier1.annotations, tier2.annotations):
        if overlap(anno1, anno2):
            matching_annos.append((anno1, anno2))
        
    if len(matching_annos) == 0:
        # return None if there are no overlaps
        return(None)

    # get strings from annotations
    strings = get_strings(merge_duplicate_annos(matching_annos))
    return(sum([levenshtein(a1, a2) for a1, a2 in strings]))

def overlap(anno1, anno2):
    # TODO: ensure these are integers?
    anno1_range = range(anno1.begin, anno1.end)
    anno2_range = range(anno2.begin, anno2.end)
    overlap = list(set(anno1_range) & set(anno2_range))
    if len(overlap) > 0:
        return(True)
    else:
        return(False)

def merge_duplicate_annos(values):
    # if there are duplicate gc or comp annotations, then collapse the other 
    # kind and concatenate. In other words, if one annotatator label 'one two'
    # but another annotator broke that into two annotations ('one' and 'two') 
    # that both overlap the first, then collapse those two into one string.
    
    mergeddict_gc = collections.defaultdict(list)
    for group in values:
        mergeddict_gc[group[1]].append(group[0])    
    gcs = tuple(tuple(mergeddict_gc[k]) for k in [anno[1] for anno in values])
    
    mergeddict_comps = collections.defaultdict(list)
    for group in values:
        mergeddict_comps[group[0]].append(group[1])
    comps = tuple(tuple(mergeddict_comps[k]) for k in [anno[0] for anno in values])
    
    combined_annos = tuple(set(tuple((a, b) for a, b in zip(gcs, comps))))
    return(combined_annos)
    
def get_strings(values):
    strings_out = []
    for match in values:
        gc = " ".join([anno.value for anno in match[0]])
        comp = " ".join([anno.value for anno in match[1]])
        strings_out.append((gc, comp))
            
    return(strings_out)

if __name__ == '__main__':
    elanFiles = sys.argv[1:]
    file_tiers = []
    for fl in elanFiles:
        # TOOD: suppress warnings about media?
        file_tiers.append(pyelan.tierSet(file = fl))
    print("Processing {0} files".format(len(file_tiers)))

    tiers = []
    for ft in file_tiers:
        tiers.extend(ft.tiers)
    print("Found a total of {0} tiers across all files".format(len(tiers)))

    # Use the first tier as the ostensible gold standard
    gs_tier = tiers[0]
    comp_tiers = tiers[1] # TODO: make this be a list
    print("The gold-standard tier has {0} annotations".format(len(gs_tier.annotations)))
    print("The comparison tier has {0} annotations".format(len(comp_tiers.annotations)))
    
    # straight levenshtein distance
    # TODO: calculate GS total characters
    total_lev = totalLevenshtein(gs_tier, comp_tiers)
    print("There was a total Levenshtein distance for all annotations of: {0}".format(total_lev))
    
    overlap_lev = overlappingAnnotationLevenshtein(gs_tier, comp_tiers)
    print("There was a Levenshtein distance for overlapping annotations of: {0}".format(overlap_lev))


