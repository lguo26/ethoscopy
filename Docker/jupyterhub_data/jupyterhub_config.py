#  Some spawners allow shell-style expansion here, allowing you to use
#  environment variables. Most, including the default, do not. Consult the
#  documentation for your spawner to verify!
#  Default: ['jupyterhub-singleuser']

#c.Spawner.cmd = ['jupyterhub-singleuser'] #Default would be single user
c.Spawner.cmd = ['jupyter-labhub', '--allow-root']

# Simple authentication with shared password
c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
c.DummyAuthenticator.password = 'ethoscope'

# Allowed users - add as many users as you need, they will all share the same password
c.Authenticator.allowed_users = {
    'amadabhushi', 'ggilestro', 'mjoyce', 'lguo',
    'labguest1', 'labguest2', 'labguest3', 'labguest4',
    'labguest5', 'labguest6', 'labguest7', 'labguest8',
    'ethoscopelab'
}

# Admin users
c.Authenticator.admin_users = {'ggilestro'}

# Custom spawner that doesn't require system users
from jupyterhub.spawner import LocalProcessSpawner
import os

class ConfigUserSpawner(LocalProcessSpawner):
    def make_preexec_fn(self, name):
        """Don't try to switch users - run everything as current user"""
        return None
    
    def user_env(self, env):
        """Set user environment without system user lookup"""
        env = env.copy()
        home_dir = f'/home/{self.user.name}'
        
        # Ensure home directory exists with proper permissions
        os.makedirs(home_dir, mode=0o755, exist_ok=True)
        
        # Set environment variables
        env['USER'] = self.user.name
        env['HOME'] = home_dir
        env['SHELL'] = '/bin/bash'
        env['LOGNAME'] = self.user.name
        
        return env

c.JupyterHub.spawner_class = ConfigUserSpawner
c.Spawner.notebook_dir = '/home/{username}'

# Timeouts
c.Spawner.http_timeout = 60
c.Spawner.start_timeout = 60
