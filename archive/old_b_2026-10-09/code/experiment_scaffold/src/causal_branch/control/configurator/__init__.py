"""Paper B configurator scaffold (B-DAC1..3): serialiser, frozen encoder, shared heads.

Design reference: ``docs/paper_split/B_DAC_CONFIGURATOR_AMENDMENT_20261004.md``.
ENGINEERING ONLY until run on qualified pilot data; the Kev and CLM encoders are
stubbed until their artifacts are bound.
"""

from causal_branch.control.configurator.encoder import (  # noqa: F401
    CLMBinding,
    CLMEncoder,
    EmbeddingCache,
    EncoderError,
    EncoderUnavailable,
    KevBinding,
    KevEncoder,
    MockEncoder,
)
from causal_branch.control.configurator.heads import (  # noqa: F401
    FEATURE_SETS,
    ConfiguratorError,
    EmbeddingProjector,
    evaluate_with_configurator,
    fit_feature_map,
)
from causal_branch.control.configurator.serialiser import (  # noqa: F401
    DecisionHistory,
    HistoryEvent,
    SerialiserError,
    serialise,
    serialise_root,
)
