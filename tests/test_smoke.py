import subprocess
import sys

from floc import __version__


def test_cli_version():
    r = subprocess.run([sys.executable, "-m", "floc", "--version"], capture_output=True, text=True)
    assert r.returncode == 0
    assert r.stdout.strip() == __version__
