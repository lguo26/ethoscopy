"""
JupyterHub User Configuration
==============================

This file defines the allowed users and admin users for JupyterHub.

Usage:
------
Edit the sets below to add/remove users. This file is imported by jupyterhub_config.py.

Notes:
------
- For OAuth authenticators (GitHub, Google, GitLab, Keycloak):
  - The ALLOWED_USERS list is ignored if allow_all=True is set
  - You can override this by setting ENFORCE_WHITELIST_FOR_OAUTH=true in .env
  - Admin users still apply regardless of authentication method

- For Dummy authenticator:
  - ALLOWED_USERS is always enforced
  - Users must be in this list to log in with the shared password
"""

# Default allowed users
# These usernames correspond to home directories that will be created
ALLOWED_USERS = {
    'amadabhushi',
    'ggilestro',
    'mjoyce',
    'lguo',
    'labguest1',
    'labguest2',
    'labguest3',
    'labguest4',
    'labguest5',
    'labguest6',
    'labguest7',
    'labguest8',
    'ethoscopelab'
}

# Admin users have special privileges:
# - Can access the admin panel
# - Can start/stop other users' servers
# - Can add users to the hub
ADMIN_USERS = {
    'ggilestro'
}
