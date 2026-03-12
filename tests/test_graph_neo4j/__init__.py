from pyzx import *




if __name__ == '__main__':
    import unittest
    import sys
    sys.path.append('..')
    sys.path.append('.')
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner()
    runner.run(suite)