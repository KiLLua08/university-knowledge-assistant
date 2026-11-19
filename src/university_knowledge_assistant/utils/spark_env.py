"""Shared local Spark environment setup.

The smoke test already proved that Spark needs this interpreter path and, on
Windows, a JAVA_HOME that is visible to the current process. Keeping the
setup in one place avoids duplicating that logic in every Spark entry point.
"""

import os
import sys
from pathlib import Path


def prepare_spark_environment() -> None:
    """Point Spark at the running interpreter and a valid Java 17 install."""
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    java_home = os.environ.get("JAVA_HOME", "").strip().strip('"')
    if java_home and (Path(java_home) / "bin" / "java.exe").exists():
        os.environ["JAVA_HOME"] = java_home
        return

    if os.name != "nt":
        return

    # Windows stores JAVA_HOME in the registry; a fresh shell may not have it.
    import winreg

    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, "Environment") as key:
                value, _ = winreg.QueryValueEx(key, "JAVA_HOME")
        except OSError:
            continue

        candidate = str(value).strip().strip('"')
        if (Path(candidate) / "bin" / "java.exe").exists():
            os.environ["JAVA_HOME"] = candidate
            bin_dir = str(Path(candidate) / "bin")
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            return
