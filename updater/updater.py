"""
Faqture Auto-Updater
Checks GitHub Releases for new versions and installs them silently.
Runs as a scheduled task (every 6 hours) or manually.
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITHUB_OWNER = "Dalnec"
GITHUB_REPO = "faqture-api"
SERVICE_NAME = "FaqtureServicio"
INSTALL_DIR = Path(r"C:\Program Files\Faqture")
VERSION_FILE = "version.txt"
UPDATER_LOG = "updater.log"
SETUP_ASSET_PATTERN = "Setup.exe"

GITHUB_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging():
    log_path = INSTALL_DIR / UPDATER_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("faqture-updater")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(str(log_path), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return logger


log = setup_logging()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read_local_version() -> str:
    version_path = Path(sys.executable).parent / VERSION_FILE
    if not version_path.exists():
        log.warning(f"Version file not found: {version_path}")
        return "0.0.0"
    return version_path.read_text(encoding="utf-8").strip()


def parse_semver(version_str: str) -> tuple:
    version_str = version_str.lstrip("vV")
    parts = version_str.split(".")
    try:
        return tuple(int(p) for p in parts[:3])
    except (ValueError, IndexError):
        return (0, 0, 0)


def github_request(url: str) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("FAQTURE_UPDATE_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    else:
        log.warning("FAQTURE_UPDATE_TOKEN not set - public repo fallback")

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(url: str, dest: Path, headers: dict = None) -> None:
    if headers is None:
        headers = {}
    token = os.environ.get("FAQTURE_UPDATE_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    log.debug(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if check and result.returncode != 0:
        log.error(f"Command failed: {result.stderr}")
    return result


# ---------------------------------------------------------------------------
# NSSM helpers
# ---------------------------------------------------------------------------


def nssm_stop() -> bool:
    r = run_command(["nssm", "stop", SERVICE_NAME], check=False)
    return r.returncode == 0


def nssm_start() -> bool:
    r = run_command(["nssm", "start", SERVICE_NAME], check=False)
    return r.returncode == 0


# ---------------------------------------------------------------------------
# Main update logic
# ---------------------------------------------------------------------------


def check_and_update():
    log.info("=== Faqture Updater started ===")

    local_version = read_local_version()
    log.info(f"Local version: {local_version}")

    try:
        release = github_request(GITHUB_API)
    except urllib.error.HTTPError as e:
        log.error(f"GitHub API error: {e.code} {e.reason}")
        return
    except Exception as e:
        log.error(f"Failed to check releases: {e}")
        return

    remote_version = release.get("tag_name", "").lstrip("vV")
    log.info(f"Remote version: {remote_version}")

    if parse_semver(remote_version) <= parse_semver(local_version):
        log.info("Already up to date.")
        return

    log.info(f"New version available: {remote_version}")

    # Find the Setup.exe asset
    assets = release.get("assets", [])
    setup_asset = None
    for asset in assets:
        if asset.get("name", "").endswith(SETUP_ASSET_PATTERN):
            setup_asset = asset
            break

    if not setup_asset:
        log.error(f"No asset matching *{SETUP_ASSET_PATTERN} found in release")
        return

    download_url = setup_asset["browser_download_url"]
    log.info(f"Downloading: {setup_asset['name']}")

    # Download to temp directory
    tmp_dir = Path(tempfile.mkdtemp(prefix="faqture_update_"))
    installer_path = tmp_dir / setup_asset["name"]

    try:
        download_file(download_url, installer_path)
        log.info(f"Downloaded to: {installer_path}")

        # Stop the service
        log.info(f"Stopping service {SERVICE_NAME}...")
        nssm_stop()

        # Run silent install
        log.info("Running installer silently...")
        installer_cmd = [
            str(installer_path),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
        ]
        r = run_command(installer_cmd, check=False)
        log.info(f"Installer exit code: {r.returncode}")

        if r.returncode == 0:
            log.info("Update completed successfully")
        else:
            log.warning(f"Installer returned non-zero code: {r.returncode}")

    except Exception as e:
        log.error(f"Update failed: {e}", exc_info=True)
    finally:
        # Cleanup
        try:
            installer_path.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass

    log.info("=== Faqture Updater finished ===")


if __name__ == "__main__":
    check_and_update()
