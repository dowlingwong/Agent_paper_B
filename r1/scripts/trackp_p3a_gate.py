"""Hold a P.3a worker until the independent watchdog confirms readiness."""
import os
import sys

fd=int(sys.argv[1])
if os.read(fd,1) != b"1":
    raise SystemExit("STOP: P.3a watchdog handshake failed")
os.close(fd)
os.execv(sys.argv[2],sys.argv[2:])
