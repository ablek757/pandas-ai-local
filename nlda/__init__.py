"""pandas-ai-local: natural-language driven automated data analysis."""

from .agent import AnalysisAgent
from .config import Config, load_config

__version__ = "0.1.0"
__all__ = ["AnalysisAgent", "Config", "load_config", "__version__"]
