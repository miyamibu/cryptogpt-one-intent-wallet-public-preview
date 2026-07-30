"""Discovery marker for the actual-HTTP preview test.

The full validation runner executes tools/test_local_preview_http.py directly
so browser binaries are required only in the visual/integration phase.
"""

from tools.test_local_preview_http import main

__all__ = ["main"]
