"""Frozen worker entry: imports the editable train.py and serves the parent's requests."""
import ar_isolated as iso
conn = iso.worker_connect()
import numpy as np
import train


def h_train(meta, arrays, fds):
    train.train(int(meta["steps"]))
    return {}, {}


def h_predict(meta, arrays, fds):
    return {}, {"y": np.asarray(train.predict(arrays["x"]), dtype=np.int64)}


def h_fill(meta, arrays, fds):
    buf = iso.SharedBuffer((4,), "float32", fd=fds[0])
    buf.array[:] = np.asarray(train.fill(), dtype=np.float32)
    buf.close()
    return {}, {}


iso.serve({"train": h_train, "predict": h_predict, "fill": h_fill}, conn)
