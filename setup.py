from setuptools import setup, find_packages
from pathlib import Path


def load_requirements() -> list[str]:
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        return []
    lines = req_file.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


setup(
    name="warden",
    version="1.0.0",
    description="Warden AI – intelligent file system assistant",
    packages=find_packages(),
    include_package_data=True,
    install_requires=load_requirements(),
    entry_points={
        "console_scripts": [
            "warden=warden_cli:main",
        ],
    },
)

