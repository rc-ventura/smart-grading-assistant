import os
import sys
import warnings

# Ensure project root is on sys.path when running pytest inside capstone/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(PROJECT_ROOT)

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
