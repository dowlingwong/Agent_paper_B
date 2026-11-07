"""Print the real chained server exception in the DRYRUN child only."""
import traceback
from r1.exam.runtime import ExamRunner
from r1.scripts.exam_runner import main

original_server = ExamRunner.server

def traced_server(self, *args, **kwargs):
    try:
        return original_server(self, *args, **kwargs)
    except Exception:
        traceback.print_exc()
        raise

ExamRunner.server = traced_server
if __name__ == '__main__':
    raise SystemExit(main())
