"""Custom exceptions for the grading system."""


class EmptyOutputError(RuntimeError):
    """Raised when an agent produces empty or missing output."""
    pass
