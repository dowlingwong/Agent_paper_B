# CPU-masked static tests (Track G port kits) run before the five U2 isolated-node smokes
# Command (accepted kit-update helper /home/dowling/r1_engineering/iso_kit_update_20261119/scripts/run_static_tests.sh):
#   systemd-run --user --scope -p Delegate=yes -- bash -c 'cd <kit worktree>; PYTHONPATH=src
#     PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= timeout 300 taskset -c 0-15 \
#     <envs/torch312/bin/python> -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"'
# Mask: taskset -c 0-15, CUDA_VISIBLE_DEVICES= (GPU-masked), delegated user cgroup, no pytest cache, no bytecode.
# Kit tips at test time: mlab fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9, mlgym f07875de79a5a57739227b13e0fd52d31646edaf.
# Accepted kit-update reference (TRACKG_ISO_KIT_UPDATE_20261119.md sec 4): mlab 218 passed / 2 failed / 1 skipped /
# 5 deselected; mlgym 225 passed / 2 failed / 1 skipped / 6 deselected. Both reproduced below.
# The two failures in each kit are the accepted environment failures documented in kit report sec 4:
#   test_trackg_review_round2.py::test_child_that_leaves_the_group_but_not_the_session_is_killed
#     (fixture job runs under /usr/bin/python3 3.10, which has no subprocess.Popen process_group=)
#   test_trackg_t0_identity.py::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit
#     (langchain-openai not installed in envs/torch312)
# Exit code is 1 because of those two known environment failures; the pass/skip/deselect counts match.
