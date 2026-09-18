class NotConfiguredError(RuntimeError):
    """Raised when a source/integration is used but its required credentials aren't set."""
