# Ethoscopelab docker instance

Note: Most users will **not** need to recreate this image. These instructions are just provided as reference.
The ethoscopelab docker instance lives on dockerhub at the following address: [https://hub.docker.com/r/ggilestro/ethoscope-lab](https://hub.docker.com/r/ggilestro/ethoscope-lab) and this is what regular users should download and run. Follow instructions there and on the [ethoscopy manual](https://bookstack.lab.gilest.ro/books/ethoscopy/page/getting-started).


## Docker files that were used to create the ethoscope-lab docker instance

The files in this folder can be used to recreate the image as uploaded on dockerhub. 

The command to use to recreate that image is `JUPYTER_HUB_TAG=5.3.0 ETHOSCOPE_LAB_TAG=1.0 docker compose build`. This creates the image with the specified tag. For Docker Hub deployment, push the image: `docker push ggilestro/ethoscope-lab:1.0`. To also create a latest tag: `docker tag ggilestro/ethoscope-lab:1.0 ggilestro/ethoscope-lab:latest && docker push ggilestro/ethoscope-lab:latest`. You can verify your local images with `docker images | grep ethoscope-lab`.

After creation, the image can be run using the enclosed `docker-compose.yml` file, replacing values as fit.

## Add new users to the JupyterHub

To add new users to the JupyterHub instance:

### 1. Modify the jupyterhub_config.py file

Edit the `allowed_users` set on lines 14-19 to include your new usernames:

```python
c.Authenticator.allowed_users = {
    'amadabhushi', 'ggilestro', 'mjoyce', 'lguo',
    'labguest1', 'labguest2', 'labguest3', 'labguest4',
    'labguest5', 'labguest6', 'labguest7', 'labguest8',
    'ethoscopelab', 'newuser1', 'newuser2'  # Add your new users here
}
```

To make a user an admin, add them to the `admin_users` set on line 22:

```python
c.Authenticator.admin_users = {'ggilestro', 'newadmin'}
```

### 2. Restart the Docker container

After modifying the config file:

```bash
docker compose down
docker compose up -d
```

**Notes:**
- All users share the same password: `ethoscope` (line 11)
- The system uses DummyAuthenticator for simple shared-password authentication
- Each user gets their own home directory at `/home/{username}`
- Home directories are created automatically when users first log in

## Mounting Home Directories as Volumes

To persist user data and notebooks across container restarts, you should mount user home directories as Docker volumes. This is done by modifying the `docker-compose.yml` file.

### Benefits of mounting home directories:

1. **Data Persistence**: User notebooks, data files, and configurations survive container restarts and updates
2. **Backup and Recovery**: Easy to backup user data by copying the mounted directories
3. **Performance**: Direct access to host filesystem, avoiding container storage overhead
4. **Sharing**: Users can access their files from the host system if needed

### Example volume configuration:

Add volumes to your `docker-compose.yml`:

```yaml
services:
  jupyterhub:
    volumes:
      - ./user_data:/home  # Maps host ./user_data to container /home
      - ./jupyterhub_config.py:/srv/jupyterhub/jupyterhub_config.py
```

Or for individual user directories:

```yaml
volumes:
  - ./users/ggilestro:/home/ggilestro
  - ./users/amadabhushi:/home/amadabhushi
  - ./users/shared:/home/shared  # Shared directory for all users
```

This ensures all user work is preserved even when containers are recreated or updated.


