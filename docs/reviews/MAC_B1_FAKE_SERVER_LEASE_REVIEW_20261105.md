# Independent B1 fake-server lease test review

**Verdict: ACCEPTED for the synthetic test only.** Reviewed test-only commit `fee514f3df471c47fd64118e87668ccf16659dec` against `0ac5ce9` in an independent local clone. This is not acceptance of B1 readiness, authorization, or evidence from TASL-7.

The test takes a real temporary cooperative flock and passes its descriptor through `LlamaServerInstance.start` to the loopback-only fake server. It closes the parent's descriptor, verifies that an independently opened flock remains unavailable while the child runs, stops the child it started and then verifies the lock can be acquired. Thus this exercises the actual `pass_fds` route to the fake server rather than relying only on a mocked process. `verify_server_fd` is deliberately mocked: the test does not establish Linux `/proc` observability, a native llama-server's FD behavior, or all crash schedules. The existing unrelated comment deletion changes no test assertion.

Independent local Python test with sandbox permission for loopback-only fake server: `r1/tests/test_llama_server_instance.py -k 'b1_lease or start_records_argv_cmdline'`: **2 passed, 19 deselected**. No real remote server, model, GPU, or experiment was used. The target host's lock conventions and native server FD behavior remain separately gated checks.
