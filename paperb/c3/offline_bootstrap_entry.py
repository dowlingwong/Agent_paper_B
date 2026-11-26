"""Script exec'd by the M3 clone3 launcher as ``python -I -S -B <this file>``.

``-I -S`` ignore PYTHON* variables, the user site and site-packages; the only
import path added is this checkout's root, derived from this file's resolved
location. Everything else is in ``offline_bootstrap.main``.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from r1.c3 import offline_bootstrap  # noqa: E402

if __name__ == '__main__':
    offline_bootstrap.main()
