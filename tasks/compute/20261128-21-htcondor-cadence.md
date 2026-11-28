# compute/20261128-21 — HTCondor pool reads: less often, record only changes

Six pool reads today all found no startable A100/L40S. From now on read the TOpAS `c03-001-175` and ETP L40S `Start` state at most every 3 hours, and
make a record branch only when the state changes (a slot becomes startable, or a new class appears); otherwise one line in your round status. When a
slot is startable, submit the D.3 single-card preflight as `compute/20261128-03` says. The D.3a route does not depend on it (P7 layout is the TASL-2
RTX 4090).
