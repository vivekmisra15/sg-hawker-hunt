import sys
import os

# Allow `from tools.x import Y` and `from models.x import Y` in tests
sys.path.insert(0, os.path.dirname(__file__))
