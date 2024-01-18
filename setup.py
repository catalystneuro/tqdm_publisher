from pathlib import Path

from setuptools import find_packages, setup

root = Path(__file__).parent

with open(root / "README.md") as f:
    long_description = f.read()
with open(root / "requirements.txt") as f:
    install_requires = f.readlines()

setup(
    name="tqdm-publisher",
    version="0.1.0",
    description="Subscribe to TQDM progress bars with arbitrary functions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Garrett Flynn and Cody Baker",
    author_email="garrett.flynn@catalystneuro.com",
    url="https://github.com/catalystneuro/tqdm-publisher",
    keywords="tqdm",
    license_files=("license.txt",),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=install_requires,
    license="BSD-3-Clause",
)
