#!/usr/bin/env python3
"""Publish a tutorial notebook to a BookStack page as rendered markdown.

Pipeline (per notebook):

    1. Execute the notebook against a fresh kernel (nbconvert --execute).
    2. Strip Plotly JS-laden outputs from the executed notebook — they bloat the
       render to tens of MB and BookStack can't display them interactively
       anyway. Each stripped Plotly output is replaced with a one-line
       placeholder so the reader can tell something was there.
    3. Convert the cleaned notebook to markdown (nbconvert --to markdown),
       which emits seaborn figures as separate PNG files alongside the .md.
    4. Upload every PNG to the BookStack image gallery (associated with the
       target page) and rewrite the markdown to reference the uploaded URLs.
    5. Create or update the BookStack page with the final markdown.

Credentials are read from a .env file (or env vars) containing:

    BOOKSTACK_BASE_URL=https://your-bookstack/api
    BOOKSTACK_API_TOKEN=TOKEN_ID:TOKEN_SECRET

Usage:
    publish_tutorials.py <notebook.ipynb> --page-id <N>
    publish_tutorials.py <notebook.ipynb> --book-id <B> --create --title "…"
    publish_tutorials.py <notebook.ipynb> --page-id 16 --env-file ~/.mcp/.env

Nothing is done over the network until the local render succeeds.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests

DEFAULT_ENV_FILE = Path.home() / "Code/dockers/MCPs/.env"
DEFAULT_WORKDIR = Path("/tmp/ethoscopy_publish_tutorials")

PLOTLY_PLACEHOLDER = (
    "*(Plotly figure omitted from static docs — run the notebook locally "
    "for the interactive version.)*"
)

AUTO_GENERATED_BANNER_TMPL = (
    "> **Auto-generated from [`{nb_relpath}`]({nb_github_url}).** "
    "Executed against the seaborn canvas so every figure is inline as a "
    "static PNG. Plotly-only cells are kept for context and marked as "
    "placeholders — for the interactive version, run the source notebook.\n\n"
    "---\n\n"
)


@dataclass
class BookStackClient:
    base_url: str
    token: str

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Token {self.token}"}

    def upload_image(self, path: Path, page_id: int, name: str) -> str:
        url = urljoin(self.base_url + "/", "image-gallery")
        with path.open("rb") as fh:
            r = requests.post(
                url,
                headers=self._headers,
                data={"type": "gallery", "uploaded_to": page_id, "name": name},
                files={"image": (path.name, fh, "image/png")},
                timeout=60,
            )
        r.raise_for_status()
        return r.json()["url"]

    def create_page(self, book_id: int, name: str, markdown: str) -> int:
        url = urljoin(self.base_url + "/", "pages")
        r = requests.post(
            url,
            headers=self._headers,
            json={"book_id": book_id, "name": name, "markdown": markdown},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["id"]

    def update_page(self, page_id: int, markdown: str, name: str | None = None) -> None:
        url = urljoin(self.base_url + "/", f"pages/{page_id}")
        payload: dict[str, object] = {"markdown": markdown}
        if name is not None:
            payload["name"] = name
        r = requests.put(url, headers=self._headers, json=payload, timeout=60)
        r.raise_for_status()


def load_env(env_file: Path | None) -> tuple[str, str]:
    """Resolve (base_url, token), env vars taking precedence over the file."""
    base_url = os.environ.get("BOOKSTACK_BASE_URL")
    token = os.environ.get("BOOKSTACK_API_TOKEN")
    if env_file and env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            v = v.strip().strip('"').strip("'")
            if k == "BOOKSTACK_BASE_URL" and not base_url:
                base_url = v
            elif k == "BOOKSTACK_API_TOKEN" and not token:
                token = v
    if not base_url or not token:
        sys.exit(
            "Missing BookStack credentials. Set BOOKSTACK_BASE_URL and "
            "BOOKSTACK_API_TOKEN in env vars or point --env-file at a file "
            f"containing them (default: {DEFAULT_ENV_FILE})."
        )
    return base_url.rstrip("/"), token


def execute_notebook(src: Path, dst: Path, kernel: str, timeout: int) -> None:
    """Run the notebook against a fresh kernel and write outputs to dst."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--execute", "--to", "notebook", "--inplace",
            f"--ExecutePreprocessor.timeout={timeout}",
            f"--ExecutePreprocessor.kernel_name={kernel}",
            str(dst),
        ],
        check=True,
    )


def strip_plotly_outputs(nb_path: Path) -> None:
    """Remove Plotly HTML/JS outputs, replacing cells that had one with a note."""
    nb = json.loads(nb_path.read_text())

    def is_plotly(out: dict) -> bool:
        data = out.get("data", {})
        if "application/vnd.plotly.v1+json" in data:
            return True
        html = data.get("text/html")
        if isinstance(html, list):
            html = "".join(html)
        return isinstance(html, str) and "plotly" in html.lower()

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        outs = cell.get("outputs", [])
        kept = [o for o in outs if not (
            o.get("output_type") in ("display_data", "execute_result")
            and is_plotly(o)
        )]
        if len(kept) != len(outs) and not any(
            o.get("output_type") in ("display_data", "execute_result") for o in kept
        ):
            kept.append({
                "output_type": "display_data",
                "data": {"text/markdown": [PLOTLY_PLACEHOLDER]},
                "metadata": {},
            })
        cell["outputs"] = kept

    nb_path.write_text(json.dumps(nb, indent=1))


def convert_to_markdown(nb_path: Path, stem: str) -> tuple[Path, Path]:
    """Run nbconvert --to markdown, return (md_path, support_dir)."""
    subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "markdown",
            "--output", stem,
            str(nb_path),
        ],
        check=True,
        cwd=nb_path.parent,
    )
    md = nb_path.parent / f"{stem}.md"
    support = nb_path.parent / f"{stem}_files"
    return md, support


def rewrite_image_refs(md: Path, support: Path, client: BookStackClient,
                       page_id: int, notebook_stem: str) -> None:
    """Upload every PNG in support/ and rewrite the markdown image refs."""
    if not support.exists():
        return
    url_map: dict[str, str] = {}
    for png in sorted(support.glob("*.png")):
        name = f"{notebook_stem}__{png.stem}"
        print(f"  upload {png.name} as {name!r}", file=sys.stderr)
        url_map[png.name] = client.upload_image(png, page_id, name)

    text = md.read_text()
    for fname, url in url_map.items():
        text = text.replace(f"{support.name}/{fname}", url)
    md.write_text(text)


def prepend_banner(md: Path, notebook_relpath: str, github_base: str) -> None:
    text = md.read_text()
    banner = AUTO_GENERATED_BANNER_TMPL.format(
        nb_relpath=notebook_relpath,
        nb_github_url=f"{github_base.rstrip('/')}/{notebook_relpath}",
    )
    md.write_text(banner + text)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("notebook", type=Path,
                   help="Path to the source .ipynb (relative or absolute)")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-id", type=int,
                       help="Existing BookStack page ID to update")
    group.add_argument("--create", action="store_true",
                       help="Create a new page instead of updating")
    p.add_argument("--book-id", type=int,
                   help="BookStack book ID (required with --create)")
    p.add_argument("--title", type=str,
                   help="Page title. Defaults to notebook basename.")
    p.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE,
                   help=f"Path to .env with BOOKSTACK_* vars (default: {DEFAULT_ENV_FILE})")
    p.add_argument("--workdir", type=Path, default=DEFAULT_WORKDIR,
                   help=f"Working directory for intermediate files (default: {DEFAULT_WORKDIR})")
    p.add_argument("--kernel", default="python3",
                   help="Jupyter kernel name used to execute the notebook")
    p.add_argument("--timeout", type=int, default=600,
                   help="Per-cell execution timeout in seconds")
    p.add_argument("--github-base", default=(
        "https://github.com/gilestrolab/ethoscopy/blob/main"),
        help="URL prefix used to build the 'source notebook' link in the banner")
    args = p.parse_args()

    if args.create and args.book_id is None:
        p.error("--book-id is required with --create")

    notebook = args.notebook.resolve()
    if not notebook.is_file():
        sys.exit(f"Notebook not found: {notebook}")

    base_url, token = load_env(args.env_file)
    client = BookStackClient(base_url=base_url, token=token)

    stem = re.sub(r"[^0-9A-Za-z_]+", "_", notebook.stem)
    work = args.workdir / stem
    work.mkdir(parents=True, exist_ok=True)
    executed = work / "executed.ipynb"

    print(f"[1/5] Executing {notebook.name} in {work}", file=sys.stderr)
    execute_notebook(notebook, executed, args.kernel, args.timeout)

    print("[2/5] Stripping Plotly outputs", file=sys.stderr)
    strip_plotly_outputs(executed)

    print("[3/5] Converting to markdown", file=sys.stderr)
    md_path, support_dir = convert_to_markdown(executed, stem)

    # Resolve the page: create it first if requested, so we have an ID to
    # attach uploaded images to via 'uploaded_to='.
    title = args.title or notebook.stem.replace("_", " ").strip()
    if args.create:
        page_id = client.create_page(args.book_id, title,
                                     markdown="_Placeholder — populated by publish_tutorials.py…_")
        print(f"[4/5] Created page id={page_id}", file=sys.stderr)
    else:
        page_id = args.page_id
        print(f"[4/5] Updating existing page id={page_id}", file=sys.stderr)

    print("[5/5] Uploading images and rewriting refs", file=sys.stderr)
    rewrite_image_refs(md_path, support_dir, client, page_id, stem)

    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=notebook.parent, text=True,
        ).strip())
        notebook_relpath = notebook.relative_to(repo_root).as_posix()
    except (subprocess.CalledProcessError, ValueError):
        notebook_relpath = notebook.name
    prepend_banner(md_path, notebook_relpath, args.github_base)

    client.update_page(page_id, md_path.read_text(), name=title if args.create else None)
    print(f"done → {base_url.rstrip('/api').rstrip('/')}/books/.../page/{page_id}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
