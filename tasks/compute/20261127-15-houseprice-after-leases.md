# compute/20261127-15 — houseprice CPU-set check: rerun once 0-3 and 4-7 are free

Your driver waited an hour and timed out with `STOP: a lease stayed busy for an hour; nothing ran`, with no run root and no sealed scene.
That is the driver's helper guard (R1-NO-TIMEOUT (4)), not an outcome and not a STOP of the check. MetaMaze (0-3) and Forest Cover (4-7)
still hold the leases. Rerun `run_cpuset_check.sh` with a new capture directory after **both** have sealed. Do not take the leases while
they run. If the driver can wait longer by an option, use it. Do not edit the reviewed driver.
