---
applyTo: '**'
---
# IGNORE FILE
# This file is ignored by Copilot and Copilot should not read or suggest code based on its contents.
.env

# Code base structure
app/
  config/ # Configuration files (e.g., db.py, redis.py)
  exception/ # Custom exceptions
  datastore/ # Data extraction and repository
  model/ # Database models
  service/ # Business logic and recommendation algorithms
  rest/ # REST API endpoints
  utils/ # Utility functions
  server.py            # Entry point of the application

# Code commenting
Don't comment in any code lines. Only add comments in markdown files.

# Run source code
Always run in venv and check before run if we are in venv or not.
Use this command to move into vevn stage ".\venv\Scripts\Activate".