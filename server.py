"""Compatibility shim so `python server.py` still launches the server.

The implementation now lives in the ``poe_data_mcp`` package (``poe_data_mcp/server.py``).
This shim keeps the suite's existing ``.mcp.json`` invocation working; it is not
part of the published wheel.
"""

from poe_data_mcp.server import main

if __name__ == "__main__":
    main()
