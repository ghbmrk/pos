"""BuildSpec schema and validator (G3a, docs/spec.md)."""
from .spec import BuildSpec, SpecError, load_spec  # noqa: F401
from .validate import Issue, Report, validate  # noqa: F401
from . import actors, data  # noqa: F401,E402
from .slate import SlateError, load_slate, parse_slate, validate_slate  # noqa: F401
