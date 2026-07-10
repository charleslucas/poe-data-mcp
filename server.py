"""Compatibility shim so `python POEMCP/server.py` still launches the server.

The implementation now lives in the ``poemcp`` package (``poemcp/server.py``).
This shim keeps the suite's existing ``.mcp.json`` invocation working; it is not
part of the published wheel.
"""

from poemcp.server import main

if __name__ == "__main__":
    main()
