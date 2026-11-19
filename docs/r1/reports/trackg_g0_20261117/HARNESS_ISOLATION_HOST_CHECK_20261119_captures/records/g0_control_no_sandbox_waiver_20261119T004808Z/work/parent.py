"""Frozen parent: never imports train.py; computes the metric from the worker's predictions."""
import ar_isolated as iso
chan = iso.parent_start()
import os
import sys
import numpy as np

steps = int(sys.argv[1])
print("parent dumpable-off; starting worker", flush=True)
worker = iso.Worker("worker.py")
try:
    worker.call("train", {"steps": steps})
    x = np.arange(20, dtype=np.float32)
    labels = (np.arange(20) % 2 == 0).astype(np.int64)
    _, arrays = worker.call("predict", {}, {"x": x})
    preds = arrays.get("y")
    if preds is None or preds.shape != labels.shape:
        print("AR_ERROR predictions have the wrong shape", flush=True)
        sys.exit(3)
    buffer = iso.SharedBuffer((4,), "float32")
    worker.call("fill", {}, {}, fds=[buffer.fd])
    filled = buffer.snapshot()
    buffer.close()
    print(f"parent shared buffer sum={float(filled.sum()):g}", flush=True)
    accuracy = float((preds == labels).mean())
except iso.IsolationProtocolError as error:
    print(f"AR_ERROR worker: {error}"[:500], flush=True)
    sys.exit(4)
finally:
    worker.close()
chan.write(f"val_accuracy: {accuracy:.4f}")
chan.write("test_accuracy: 0.4242")
chan.close()
