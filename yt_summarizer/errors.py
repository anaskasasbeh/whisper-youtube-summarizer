"""Error type shown to the user as a short, friendly message (no traceback)."""


class SummarizerError(Exception):
    """A problem the user can fix (bad URL, missing key, file too large, ...)."""
