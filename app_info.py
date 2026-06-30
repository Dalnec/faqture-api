import sys
import subprocess


APP_INFO = {
    "client": "Faqture",
    "type": "api",
    "version": "1.3.0",
    "build_date": "2026-06-27",
    "source_branch": _branch if (_branch := None) else "unknown",
}


def _detect_branch():
    """Detect git branch at startup, fallback to 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


APP_INFO["source_branch"] = _detect_branch()


def show_banner():
    """Print application banner with version info."""
    print("=" * 50)
    print("  FAQTURE - Sistema de Comprobantes")
    print(f"  Cliente : {APP_INFO['client']}")
    print(f"  Tipo    : {APP_INFO['type']}")
    print(f"  Version : {APP_INFO['version']}")
    print(f"  Build   : {APP_INFO['build_date']}")
    print(f"  Rama    : {APP_INFO['source_branch']}")
    print("=" * 50)


def show_version():
    """Print version info and exit."""
    print(f"Faqture {APP_INFO['version']} ({APP_INFO['build_date']})")
    print(f"Branch: {APP_INFO['source_branch']}")
    print(f"Cliente: {APP_INFO['client']} ({APP_INFO['type']})")
    sys.exit(0)


def handle_version_arg():
    """Check if --version was passed and handle it."""
    if "--version" in sys.argv:
        show_version()
