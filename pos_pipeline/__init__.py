"""BuildSpec schema and validator (G3a, docs/spec.md)."""
from .spec import BuildSpec, SpecError, load_spec  # noqa: F401
from .validate import Issue, Report, validate  # noqa: F401
