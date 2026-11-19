import sys
sys.path.insert(0, sys.argv[1])
import ar_isolated as iso
c = iso.worker_connect()
import os
iso.serve({"ping": lambda m, a, f: ({"pid": os.getpid(), "uid": os.getuid()}, {})}, c)
