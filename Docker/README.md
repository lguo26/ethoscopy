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

## Database Preparation for Docker

When mounting ethoscope database files into Docker containers with read-only permissions (`:ro`), you may encounter "database disk image is malformed" errors. This occurs when SQLite databases are in WAL (Write-Ahead Logging) mode but mounted on read-only filesystems where WAL companion files (`.db-wal`, `.db-shm`) cannot be accessed.

### Understanding the Issue

**Why this happens:**
- Ethoscope databases may be created in **WAL mode** for better write performance
- WAL mode requires companion files (`.db-wal` and `.db-shm`) alongside the main `.db` file
- Docker read-only mounts (`:ro`) prevent SQLite from accessing these files properly
- This causes intermittent "database disk image is malformed" errors during data loading

**Symptoms:**
- Intermittent loading failures for specific ROIs
- Error message: "database disk image is malformed"
- Same ROI may succeed on some loads and fail on others
- More common with large databases (>1 GB)

### Solution: Convert Databases to DELETE Mode

Before mounting databases in Docker, convert them from WAL to DELETE mode:

#### Using the Python Script (Recommended)

```bash
# From the ethoscopy project root
python3 scripts/convert_wal_to_delete.py /mnt/ethoscope_data/results --dry-run

# Convert all databases with detailed output
python3 scripts/convert_wal_to_delete.py /mnt/ethoscope_data/results --verbose

# Force conversion even for recently modified files (use with caution)
python3 scripts/convert_wal_to_delete.py /mnt/ethoscope_data/results --force
```

#### Using the Bash Wrapper

```bash
# From the ethoscopy project root
./scripts/convert_databases.sh /mnt/ethoscope_data/results
```

#### Manual Conversion Using sqlite3

For individual databases:

```bash
sqlite3 /path/to/database.db "PRAGMA wal_checkpoint(TRUNCATE); PRAGMA journal_mode=DELETE;"
```

For bulk conversion:

```bash
find /mnt/ethoscope_data/results -name "*.db" -type f -exec sqlite3 {} "PRAGMA wal_checkpoint(TRUNCATE); PRAGMA journal_mode=DELETE;" \;
```

### Verification

After conversion, verify the database is in DELETE mode:

```bash
sqlite3 /path/to/database.db "PRAGMA journal_mode;"
# Should output: delete

sqlite3 /path/to/database.db "PRAGMA integrity_check;"
# Should output: ok
```

### Best Practices

1. **Run conversion BEFORE starting Docker containers**
   ```bash
   # From the ethoscopy project root, convert databases first
   ./scripts/convert_databases.sh /mnt/ethoscope_data/results

   # Then start containers
   cd Docker && docker compose up -d
   ```

2. **Do NOT convert databases while ethoscopes are actively writing**
   - The conversion script skips files modified in the last 24 hours by default
   - Use `--force` to override this safety check if needed

3. **Test on a backup first**
   ```bash
   # Create a test copy
   cp /path/to/database.db /tmp/test.db

   # Test conversion
   sqlite3 /tmp/test.db "PRAGMA wal_checkpoint(TRUNCATE); PRAGMA journal_mode=DELETE;"

   # Verify it works
   sqlite3 /tmp/test.db "PRAGMA integrity_check;"
   ```

4. **Consider converting at the ethoscope source** (upstream fix)
   - Configure ethoscopes to use DELETE mode by default
   - Prevents the need for post-processing

### Troubleshooting

**Q: I still get "malformed" errors after conversion**

A: The ethoscopy library now includes improved connection handling that should work with both WAL and DELETE mode databases. If you still encounter issues:
1. Verify the database was actually converted: `sqlite3 database.db "PRAGMA journal_mode;"`
2. Check database integrity: `sqlite3 database.db "PRAGMA integrity_check;"`
3. Ensure you're using ethoscopy version 2.0.4 or later

**Q: Can I convert databases while Docker is running?**

A: Yes, but you should restart the container after conversion:
```bash
# From the ethoscopy project root
./scripts/convert_databases.sh /mnt/ethoscope_data/results
cd Docker && docker compose restart ethoscope-lab
```

**Q: Will this affect data quality or analysis?**

A: No. The conversion only changes how SQLite manages the database internally. All data remains identical and analysis results are unaffected.

**Q: How do I check if a database is in WAL mode?**

A:
```bash
sqlite3 database.db "PRAGMA journal_mode;"
```
Output will be either `wal` or `delete` (or `truncate`, `persist`, `memory`).

### Emergency Quick Fix

If you need to work immediately and can't run the full conversion:

```bash
# SSH to host machine (not inside container)
# Convert just the failing database
sqlite3 /path/to/failing/database.db "PRAGMA wal_checkpoint(TRUNCATE); PRAGMA journal_mode=DELETE;"

# Restart container
docker compose restart ethoscope-lab
```
