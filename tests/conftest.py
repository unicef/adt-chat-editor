import os
import sys

# Ensure repository root is on sys.path so 'src' package imports work consistently
repo_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
