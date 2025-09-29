"""
Append PYTHONPATH to sys.path after site paths is appended
"""
import sys, os


__extra_py_path = os.environ.pop("_AGIO_POST_APPEND_PATH", None)
if __extra_py_path:
    sys.path.append(__extra_py_path)
# cleanup
this_path = os.path.dirname(os.path.abspath(__file__))
if this_path in sys.path:
    sys.path.remove(this_path)
