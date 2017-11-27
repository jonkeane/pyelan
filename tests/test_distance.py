'''Unit tests for the distance methods.'''
from unittest import TestCase

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
        anno_a = pyelan.annotation(begin=1, end=10, value='a')
        anno_b = pyelan.annotation(begin=4, end=6, value='b')
        anno_c = pyelan.annotation(begin=1, end=5, value='c')
        anno_d = pyelan.annotation(begin=5, end=7, value='d')
        anno_e = pyelan.annotation(begin=7, end=10, value='e')
        anno_f = pyelan.annotation(begin=1, end=2, value='f')

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
        tier_a = pyelan.tier(
            tierName='test_a',
            annotations=[pyelan.annotation(begin=1, end=2, value='aaa')])
        tier_b = pyelan.tier(
            tierName='test_b',
            annotations=[pyelan.annotation(begin=1, end=2, value='bbb')])
        self.assertEqual(totalLevenshtein(tier_a, tier_b), 3) 
        
    def test_total_levenshtein_multipleannos(self):
        tier_a = pyelan.tier(
            tierName='test_a',
            annotations=[
                pyelan.annotation(begin=1, end=2, value='aa'),
                pyelan.annotation(begin=1, end=2, value='aa')])
        tier_b = pyelan.tier(
            tierName='test_b',
            annotations=[pyelan.annotation(begin=1, end=2, value='aaa')])
        self.assertEqual(totalLevenshtein(tier_a, tier_b), 1) 
        
class TestOverlappingLevenshtein(TestCase):
    '''Test class for overlapping levenshtein distnace calculations
    '''    
    def test_nooverlap(self):
        tier_a = pyelan.tier(
            tierName='test_a',
            annotations=[pyelan.annotation(begin=1, end=2, value='aaa')])
        tier_b = pyelan.tier(
            tierName='test_b',
            annotations=[pyelan.annotation(begin=5, end=6, value='bbb')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), None) 
    
    def test_overlap(self):
        tier_a = pyelan.tier(
            tierName='test_a',
            annotations=[pyelan.annotation(begin=1, end=5, value='aaa')])
        tier_b = pyelan.tier(
            tierName='test_b',
            annotations=[pyelan.annotation(begin=4, end=6, value='bbb')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), 3) 
    
    def test_overlap_multiannos(self):
        tier_a = pyelan.tier(
            tierName='test_a',
            annotations=[
                pyelan.annotation(begin=1, end=5, value='aaa'),
                pyelan.annotation(begin=6, end=10, value='aaa')])
        tier_b = pyelan.tier(
            tierName='test_b',
            annotations=[
                pyelan.annotation(begin=4, end=6, value='bbb'),
                pyelan.annotation(begin=6, end=10, value='bbb')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), 6)
    
    def test_overlap_one_two(self):
        tier_a = pyelan.tier(
            tierName='test_a',
            annotations=[
                pyelan.annotation(begin=1, end=10, value='aaa bbb'),
                pyelan.annotation(begin=15, end=16, value='c')])
        tier_b = pyelan.tier(
            tierName='test_b',
            annotations=[
                pyelan.annotation(begin=1, end=5, value='aaa'),
                pyelan.annotation(begin=6, end=10, value='bbb'),
                pyelan.annotation(begin=15, end=16, value='c')])
        self.assertEqual(overlappingAnnotationLevenshtein(tier_a, tier_b), 0)

