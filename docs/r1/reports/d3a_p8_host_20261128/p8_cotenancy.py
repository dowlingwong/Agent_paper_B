"""P8 deepthought co-tenancy check: 16 pinned workers, 65 s, sample load every 5 s."""
import json
import multiprocessing as mp
import os
import time
from datetime import datetime, timezone


def busy(seconds, cpu):
    os.sched_setaffinity(0, {cpu})
    end = time.monotonic() + seconds
    value = 0
    while time.monotonic() < end:
        for i in range(10000):
            value += i


def record(phase, cpus, workers, load):
    free = cpus - (load - workers)
    return {"utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "phase": phase, "cpus": cpus, "workers_running": workers,
            "load1": round(load, 2), "free_for_others": round(free, 2),
            "ok": free >= 10}


def main():
    cpus = os.cpu_count()
    pre = os.getloadavg()[0]
    print(json.dumps(record("pre", cpus, 0, pre)), flush=True)
    seconds = 65
    workers = [mp.Process(target=busy, args=(seconds, i % cpus)) for i in range(16)]
    for worker in workers:
        worker.start()
    started = time.monotonic()
    while time.monotonic() - started < seconds:
        time.sleep(5)
        print(json.dumps(record("during", cpus, 16, os.getloadavg()[0])), flush=True)
    for worker in workers:
        worker.join()


if __name__ == "__main__":
    main()
