"""Helpers for loading (and on-demand fetching) the ethoscopy tutorial datasets.

The tutorial pickle files are intentionally not shipped inside the PyPI wheel
(``overview_data.pkl`` alone is ~31 MB). They live in the ``gilestrolab/ethoscopy``
GitHub repository and can be pulled on demand with
:func:`download_tutorial_data`. By default downloads land in a user-writable
cache directory (``~/.cache/ethoscopy/tutorial_data/``) so that installs into
read-only locations (system-wide site-packages, Docker images owned by root,
conda envs, etc.) still work for non-root users.

Search order used by :func:`get_tutorial` and :func:`ethoscopy.misc.get_HMM`:

1. ``<package>/misc/tutorial_data/`` — useful for dev / editable installs and
   pre-populated Docker images.
2. ``$ETHOSCOPY_TUTORIAL_DATA_DIR`` — explicit override, mainly for shared
   environments.
3. ``~/.cache/ethoscopy/tutorial_data/`` — the user-writable default for
   ``download_tutorial_data()``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlretrieve

import pandas as pd

# Raw-file URLs on the main branch of the public repo. Pinning to main keeps
# the download aligned with the shipped tutorial notebooks.
_REPO_RAW_BASE = (
    "https://raw.githubusercontent.com/gilestrolab/ethoscopy/main"
    "/src/ethoscopy/misc/tutorial_data"
)

TUTORIAL_DATA_FILES: tuple[str, ...] = (
    "overview_data.pkl",
    "overview_meta.pkl",
    "circadian_data.pkl",
    "circadian_meta.pkl",
    "4_states_F_WT.pkl",
    "4_states_M_WT.pkl",
)

TUTORIAL_DATA_URLS: dict[str, str] = {
    name: f"{_REPO_RAW_BASE}/{name}" for name in TUTORIAL_DATA_FILES
}

ENV_OVERRIDE = "ETHOSCOPY_TUTORIAL_DATA_DIR"


def package_tutorial_data_dir() -> Path:
    """Location inside the installed ethoscopy package. May be read-only."""
    return Path(__file__).absolute().parent / "tutorial_data"


def user_tutorial_data_dir() -> Path:
    """User-writable cache directory (default for downloads)."""
    return Path.home() / ".cache" / "ethoscopy" / "tutorial_data"


def _search_paths() -> list[Path]:
    """Directories consulted (in order) when looking up a tutorial pickle."""
    paths = [package_tutorial_data_dir()]
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        paths.append(Path(override).expanduser())
    paths.append(user_tutorial_data_dir())
    return paths


def _find_pickle(name: str) -> Path | None:
    """Return the first existing location for *name*, or None."""
    for base in _search_paths():
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def _missing_files_message(missing: list[str] | None = None) -> str:
    """Build the actionable error message shown when pickles are missing."""
    searched = "\n".join(f"    - {p}" for p in _search_paths())
    missing_line = ""
    if missing:
        missing_line = f"\nMissing file(s): {', '.join(missing)}\n"
    return (
        f"Tutorial data files were not found.{missing_line}\n"
        f"Searched locations (in order):\n"
        f"{searched}\n\n"
        f"The pickles are not bundled with the PyPI wheel to keep the install "
        f"lean (overview_data.pkl alone is ~31 MB).\n\n"
        f"To download them, run once:\n\n"
        f"    >>> import ethoscopy as etho\n"
        f"    >>> etho.download_tutorial_data()\n\n"
        f"By default this populates:\n"
        f"    {user_tutorial_data_dir()}\n\n"
        f"Or fetch them manually from:\n"
        f"    {_REPO_RAW_BASE}/\n"
        f"and place them in one of the searched locations above, or point\n"
        f"${ENV_OVERRIDE} at a directory that contains them.\n"
    )


def download_tutorial_data(
    dest_dir: str | Path | None = None,
    overwrite: bool = False,
    verbose: bool = True,
) -> Path:
    """Download the tutorial pickle files from the ethoscopy GitHub repository.

    Fetches the six datasets used by the tutorial notebooks (overview and
    circadian data + metadata, plus the two pre-trained 4-state HMM pickles)
    so that :func:`get_tutorial` and :func:`ethoscopy.misc.get_HMM.get_HMM`
    can find them.

    Args:
        dest_dir (str | Path, optional): Destination directory. Defaults to the
            user-writable cache at ``~/.cache/ethoscopy/tutorial_data/``, which
            works for non-root users even when ethoscopy is installed into a
            read-only location (system Python, Docker image, conda base env).
            Pass :func:`package_tutorial_data_dir` to install into the package
            directory instead (requires write access, used by the Docker image
            during build).
        overwrite (bool): If False (default), files already present at
            ``dest_dir`` are skipped.
        verbose (bool): If True, print one line per file.

    Returns:
        Path: The directory the files were written to.

    Raises:
        PermissionError: If ``dest_dir`` (or its parents) cannot be created.
        URLError: If the repository cannot be reached.
    """
    target = (
        Path(dest_dir).expanduser()
        if dest_dir is not None
        else user_tutorial_data_dir()
    )

    try:
        target.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot create tutorial data directory at {target}: {exc}\n"
            f"Pass dest_dir=<writable path> (or set ${ENV_OVERRIDE} and pass "
            f"that path) to choose a different location."
        ) from exc

    for name, url in TUTORIAL_DATA_URLS.items():
        out = target / name
        if out.exists() and not overwrite:
            if verbose:
                print(f"  [skip] {name} (already present)")
            continue
        if verbose:
            print(f"  [get ] {name} <- {url}")
        try:
            urlretrieve(url, out)
        except URLError as exc:
            raise URLError(
                f"Failed to download {name} from {url}: {exc.reason}"
            ) from exc

    if verbose:
        print(f"Tutorial data ready in: {target}", file=sys.stdout)
    return target


def get_tutorial(data_type: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load example datasets for tutorial notebooks.

    Provides access to pre-packaged datasets for learning ethoscopy functionality.
    Available datasets:
    - 'overview': Basic movement and sleep data
    - 'circadian': Extended recording for circadian analysis

    The underlying pickle files are not bundled with the pip install. Call
    :func:`download_tutorial_data` once to fetch them, or download manually
    from the URLs in :data:`TUTORIAL_DATA_URLS`. The search order is
    documented in this module's docstring.

    Args:
        data_type (str): Dataset to load ('overview' or 'circadian')

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (data, metadata) DataFrames

    Raises:
        KeyError: If data_type is not 'overview' or 'circadian'
        FileNotFoundError: If tutorial data files cannot be found
    """
    data_type = data_type.lower()
    valid_types = {"overview", "circadian"}
    if data_type not in valid_types:
        raise KeyError(f'data_type must be one of: {", ".join(valid_types)}')

    data_name = f"{data_type}_data.pkl"
    meta_name = f"{data_type}_meta.pkl"
    data_path = _find_pickle(data_name)
    meta_path = _find_pickle(meta_name)

    missing = [
        n for n, p in ((data_name, data_path), (meta_name, meta_path)) if p is None
    ]
    if missing:
        raise FileNotFoundError(_missing_files_message(missing))

    try:
        data = pd.read_pickle(data_path)
        meta = pd.read_pickle(meta_path)
    except FileNotFoundError:
        # Race: file disappeared between lookup and read.
        raise FileNotFoundError(_missing_files_message())

    return data, meta
