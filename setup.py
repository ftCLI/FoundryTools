from pathlib import Path

import setuptools

this_directory = Path(__file__).parent
long_description = this_directory.joinpath("README.md").read_text(encoding="utf-8")


def _get_requirements() -> list[str]:
    """
    Relax hard pinning in setup.py
    """
    with open("requirements.txt", encoding="utf-8") as requirements:
        return [line.replace("==", ">=") for line in requirements.readlines()]


setuptools.setup(
    name="foundrytools",
    version="0.1.4",
    description="A library for working with fonts in Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cesare Gilento",
    author_email="ftcli@proton.me",
    url="https://github.com/ftCLI/FoundryTools",
    packages=setuptools.find_packages(),
    package_data={"foundrytools": ["py.typed", "data/*"]},
    include_package_data=True,
    install_requires=_get_requirements(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Text Processing :: Fonts",
    ],
    python_requires=">=3.10",
    zip_safe=False,
)
