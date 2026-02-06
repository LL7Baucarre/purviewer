#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup configuration for purrrr."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="purrrr",
    version="0.1.0",
    author="LL7Baucarre",
    description="A powerful command-line tool for analyzing Microsoft Purview audit logs and Entra sign-ins",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LL7Baucarre/purrrr",
    project_urls={
        "Bug Tracker": "https://github.com/LL7Baucarre/purrrr/issues",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "purrrr=purrrr.main:main",
        ],
    },
    include_package_data=True,
)
