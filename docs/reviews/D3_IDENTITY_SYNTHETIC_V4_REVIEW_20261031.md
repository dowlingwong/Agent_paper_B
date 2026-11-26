# Independent review: D3 protected-input and OFD synthetic building blocks

**LIMITED ACCEPT: synthetic building block only; production isolation BLOCK.** The reviewed source, tests, README and administrator plan all matched `SHA256SUMS`, whose own SHA-256 was `f5ab71aba777430797f361680d25e4e81e3201bf85c73ac9602ae6084b036c92`. An independent reviewer ran 20 local synthetic unit tests: all passed. The production entry remains an unconditional STOP.

Previous reviews found ordinary `OSError` leakage, `kcmp` ABI misidentification or integer truncation, and file descriptor leaks after close failure. The v4 tests specifically cover those reported paths. A descriptor whose `close()` fails has an indeterminate kernel state and is not blindly closed a second time; the tests do not prove it was released.

The guard does not establish trusted root ancestry, mount or ACLs, protection against the owning UID writing after validation, a separate service UID, production launcher, actual cross-process `kcmp` permissions, namespace isolation, GPU access or real lease lifetime. Same-UID execution and synthetic mocks cannot prove any of those. No portal fixture, model, GPU or original STOP fixture was touched during review.
