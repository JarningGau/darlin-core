"""
Public library entry points for darlinpy.

Supported user-facing APIs are exported from this module. Internal subpackages
remain importable for maintainers but are not part of the stable user contract
unless explicitly re-exported here.
"""

__version__ = "1.0.0"
__author__ = "Jarning Gau"

# Export main API interfaces
from .api import analyze_sequences
from .config.amplicon_configs import AmpliconConfig
from .utils.build_config import build_carlin_config

__all__ = [
    "__version__",
    "__author__",
    "analyze_sequences",
    "AmpliconConfig",
    "build_carlin_config",
]
