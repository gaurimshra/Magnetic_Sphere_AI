"""External service clients.

Every client is written to fail closed: missing credentials or provider outages
return `None`/disabled results so the demo pipeline continues to run.
"""

