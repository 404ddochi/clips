"""Application-specific exceptions."""

from __future__ import annotations


class ClipsError(Exception):
    """Base error for CLIPS domain logic."""


class ConfigurationError(ClipsError):
    """Invalid or unsafe configuration."""
