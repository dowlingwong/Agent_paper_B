"""Paper B control package.

Policy learning, allocation and evaluation for the one-step continue/verify
decision problem of Paper B.  This package may import
:mod:`causal_branch.measurement`; the measurement facade must never import this
package.  ``make check-split`` enforces the direction.

Nothing here is scientific evidence.  The closed synthetic world in
:mod:`causal_branch.control.world` exists to exercise the schema, learners,
allocator and evaluator end to end (``make smoke-b``), and every run it
produces is marked ``ENGINEERING_ONLY``.
"""

from causal_branch.control.allocation import (  # noqa: F401
    ConservativeSelector,
    batch_top_q,
    streaming_threshold,
)
from causal_branch.control.evaluate import (  # noqa: F401
    PolicyEvaluation,
    evaluate_policies,
)
from causal_branch.control.learners import (  # noqa: F401
    AdvantageLearner,
    ActionValueLearner,
    OutcomeRiskLearner,
    UtilityDeficitLearner,
)
from causal_branch.control.schema import (  # noqa: F401
    B_BRANCH_SCHEMA_VERSION,
    BranchRecord,
    feature_projection,
    validate_record,
)
from causal_branch.control.world import (  # noqa: F401
    SyntheticWorld,
    generate_world,
)

__all__ = [
    "B_BRANCH_SCHEMA_VERSION",
    "BranchRecord",
    "feature_projection",
    "validate_record",
    "SyntheticWorld",
    "generate_world",
    "AdvantageLearner",
    "ActionValueLearner",
    "OutcomeRiskLearner",
    "UtilityDeficitLearner",
    "batch_top_q",
    "streaming_threshold",
    "ConservativeSelector",
    "PolicyEvaluation",
    "evaluate_policies",
]
