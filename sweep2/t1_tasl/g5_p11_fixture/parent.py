"""Synthetic trusted scoring parent."""
import ar_isolated as iso

channel = iso.parent_start()
worker = iso.Worker("worker.py")
try:
    response, _ = worker.call("train", {})
    score = int(response["checksum"]) / 4096
    channel.write(f"step 5 loss: {1 - score}")
    channel.write(f"val_accuracy: {score}")
    channel.write(f"test_accuracy: {score}")
finally:
    worker.close()
    channel.close()
