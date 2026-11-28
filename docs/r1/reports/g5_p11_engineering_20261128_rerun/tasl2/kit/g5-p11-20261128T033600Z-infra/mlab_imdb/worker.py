"""Synthetic isolated worker."""
import ar_isolated as iso

connection = iso.worker_connect()

import train


def train_one(meta, arrays, fds):
    return {"checksum": train.checksum()}, {}


iso.serve({"train": train_one}, connection)
