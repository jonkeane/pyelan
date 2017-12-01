'''Unit tests for the distance methods.'''
from unittest import TestCase

import core as pyl
from pyelan.distance import *

class TestlevenshteinCalculations(TestCase):
    '''Test class for Levenshtein Distance Calculations
    '''
    def test_levenshtein(self):
        self.assertEqual(levenshtein("aaa", "bbb"), 3) # substitution
        self.assertEqual(levenshtein("aa", "aaa"), 1) # add
        self.assertEqual(levenshtein("aaa", "aa"), 1) # delete
        self.assertEqual(levenshtein("aaa", "aa"), 1) # delete
        self.assertEqual(levenshtein("ab", "ba"), 2) # swap
        
class TestOverlap(TestCase):
    '''Test class for overlap detection
    '''
    def test_overlap(self):
        anno_a = pyl.annotation(begin=1, end=10, value='a')
        anno_b = pyl.annotation(begin=4, end=6, value='b')
        anno_c = pyl.annotation(begin=1, end=5, value='c')
        anno_d = pyl.annotation(begin=5, end=7, value='d')
        anno_e = pyl.annotation(begin=7, end=10, value='e')
        anno_f = pyl.annotation(begin=1, end=2, value='f')

        self.assertTrue(overlap(anno_a, anno_b)) # 1 contains 2
        self.assertTrue(overlap(anno_b, anno_a)) # 2 contains 1
        self.assertTrue(overlap(anno_c, anno_b)) # 1 starts before 2, but overlaps
        self.assertTrue(overlap(anno_d, anno_b)) # 1 ends after 2, but overlaps
        
        self.assertFalse(overlap(anno_e, anno_b)) # does not overlap
        self.assertFalse(overlap(anno_f, anno_b)) # does not overlap
        
class TestTotalLevenshtein(TestCase):
    '''Test class for overlap detection
    '''    
    def test_total_levenshtein(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[pyl.annotation(begin=1, end=2, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[pyl.annotation(begin=1, end=2, value='bbb')])
        self.assertEqual(totalLevenshtein(tier_a, tier_b), 3/3.) 
        
    def test_total_levenshtein_multipleannos(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=2, value='aa'),
                pyl.annotation(begin=1, end=2, value='aa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[pyl.annotation(begin=1, end=2, value='aaa')])
        self.assertEqual(totalLevenshtein(tier_a, tier_b), 1/4.) 
        
class TestOverlappingLevenshtein(TestCase):
    '''Test class for overlapping levenshtein distnace calculations
    '''    
    def test_nooverlap(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[pyl.annotation(begin=1, end=2, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[pyl.annotation(begin=5, end=6, value='bbb')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), None) 
    
    def test_overlap(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[pyl.annotation(begin=1, end=5, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[pyl.annotation(begin=4, end=6, value='bbb')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), 3/3.) 
    
    def test_overlap_multiannos(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=5, value='aaa'),
                pyl.annotation(begin=6, end=10, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=4, end=6, value='bbb'),
                pyl.annotation(begin=6, end=10, value='bbb')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), 6/6.)
    
    def test_overlap_one_two(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=10, value='aaa bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=5, value='aaa'),
                pyl.annotation(begin=6, end=10, value='bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), 0/8.)

class TestoverlappingTimeDiff(TestCase):
    '''Test class for overlapping levenshtein distnace calculations
    '''    
    def test_nooverlap(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[pyl.annotation(begin=1, end=2, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[pyl.annotation(begin=5, end=6, value='bbb')])
        self.assertEqual(overlappingTimeDiff(tier_a, tier_b), None) 
    
    def test_overlap(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[pyl.annotation(begin=1, end=5, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[pyl.annotation(begin=4, end=6, value='bbb')])
        self.assertEqual(overlappingTimeDiff(tier_a, tier_b), 3+1) 
    
    def test_overlap_multiannos(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=5, value='aaa'),
                pyl.annotation(begin=6, end=10, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=4, end=6, value='bbb'),
                pyl.annotation(begin=6, end=10, value='bbb')])
        self.assertEqual(overlappingTimeDiff(tier_a, tier_b), 3+1)

    def test_overlap_multiannos_reverse(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=4, end=5, value='aaa'),
                pyl.annotation(begin=6, end=10, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=6, value='bbb'),
                pyl.annotation(begin=6, end=10, value='bbb')])
        self.assertEqual(overlappingTimeDiff(tier_a, tier_b), 3+1)
    
    def test_overlap_one_two(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=10, value='aaa bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=5, value='aaa'),
                pyl.annotation(begin=6, end=10, value='bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        self.assertEqual(overlappingTimeDiff(tier_a, tier_b), 0)

    def test_overlap_multiannos_frames(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=0, end=101, value='aaa'),
                pyl.annotation(begin=167, end=334, value='aaa')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=34, end=67, value='bbb'),
                pyl.annotation(begin=201, end=334, value='bbb')])
        self.assertEqual(overlappingTimeDiff(tier_a, tier_b, fps = 29.97), 2+1)


class TestAnnoMatching(TestCase):
    '''Test class for merging overlapping annotations
    '''    
    def test_matching(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=10, value='aaa'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=2, value='aaa'),
                pyl.annotation(begin=15, end=16, value='c')])
        matched = match_annos(tier_a, tier_b)
        expected = [(a, b) for a, b in zip(tier_a.annotations, tier_b.annotations)]
        self.assertEqual(matched, expected)
        
    def test_matching_with_two_to_one(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=10, value='aaa bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=2, value='aaa'),
                pyl.annotation(begin=8, end=10, value='bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        matched = match_annos(tier_a, tier_b)
        expected = [
            (tier_a.annotations[0], tier_b.annotations[0]),
            (tier_a.annotations[0], tier_b.annotations[1]),
            (tier_a.annotations[1], tier_b.annotations[2])
        ]
        self.assertEqual(matched, expected)        

    def test_matching_with_missing(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=10, value='aaa bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=2, value='aaa')])
        matched = match_annos(tier_a, tier_b, add_blank_for_mismatch = True)
        expected = [
            (tier_a.annotations[0], tier_b.annotations[0]),
            (tier_a.annotations[1], pyl.annotation(begin=15, end=16, value=''))
        ]
        for m, e in zip(matched, expected):
            self.assertEqual(m[0].begin, e[0].begin)
            self.assertEqual(m[0].end, e[0].end)
            self.assertEqual(m[0].value, e[0].value)
            
            self.assertEqual(m[1].begin, e[1].begin)
            self.assertEqual(m[1].end, e[1].end)
            self.assertEqual(m[1].value, e[1].value)

class TestAnnoMerging(TestCase):
    '''Test class for merging overlapping annotations
    '''    
    def test_overlap_one_two(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=10, value='aaa bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=2, value='aaa'),
                pyl.annotation(begin=8, end=10, value='bbb'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b_merged = pyl.tier(
                tierName='test_b',
                annotations=[
                    pyl.annotation(begin=1, end=10, value='aaa bbb'),
                    pyl.annotation(begin=15, end=16, value='c')])
        merged = merge_duplicate_annos(match_annos(tier_a, tier_b))
        expected = match_annos(tier_a, tier_b_merged)
        
        for m, e in zip(merged, expected):
            self.assertEqual(m[0].begin, e[0].begin)
            self.assertEqual(m[0].end, e[0].end)
            self.assertEqual(m[0].value, e[0].value)
            
            self.assertEqual(m[1].begin, e[1].begin)
            self.assertEqual(m[1].end, e[1].end)
            self.assertEqual(m[1].value, e[1].value)
            
            
    def test_overlap_three_annos(self):
        tier_a = pyl.tier(
            tierName='test_a',
            annotations=[
                pyl.annotation(begin=1, end=10, value='aaa bbb ddd'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b = pyl.tier(
            tierName='test_b',
            annotations=[
                pyl.annotation(begin=1, end=2, value='aaa'),
                pyl.annotation(begin=4, end=6, value='bbb'),
                pyl.annotation(begin=8, end=10, value='ddd'),
                pyl.annotation(begin=15, end=16, value='c')])
        tier_b_merged = pyl.tier(
                tierName='test_b',
                annotations=[
                    pyl.annotation(begin=1, end=10, value='aaa bbb ddd'),
                    pyl.annotation(begin=15, end=16, value='c')])
        merged = merge_duplicate_annos(match_annos(tier_a, tier_b))
        expected = match_annos(tier_a, tier_b_merged)
        
        for m, e in zip(merged, expected):
            self.assertEqual(m[0].begin, e[0].begin)
            self.assertEqual(m[0].end, e[0].end)
            self.assertEqual(m[0].value, e[0].value)
            
            self.assertEqual(m[1].begin, e[1].begin)
            self.assertEqual(m[1].end, e[1].end)
            self.assertEqual(m[1].value, e[1].value)
         
