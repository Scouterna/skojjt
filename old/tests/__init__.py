import unittest

def my_test_suite():
    testLoader = unittest.TestLoader()
    testSuite = testLoader.discover('.', pattern='*_test.py')
    return testSuite
