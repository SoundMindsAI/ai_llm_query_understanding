#!/usr/bin/env python3
"""
Installation script for the LLM Query Understanding Service package.

This file allows the package to be installed using pip or other Python package managers.
"""
from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="llm_query_understand",
    version="1.0.0",
    description="A service that transforms natural language queries into structured data using LLMs",
    author="SoundMindsAI",
    author_email="info@soundmindsai.com",
    url="https://github.com/soundmindsai/ai_llm_query_understanding",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "llm-query-server=scripts.start_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.12",
    ],
)
