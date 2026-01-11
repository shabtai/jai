"""Setup configuration for AI Docker Wrapper Tool."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="docker-wrapper",
    version="1.0.0",
    author="Your Name",
    description="AI-powered tool for automatic Dockerfile generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shabtai/jai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "docker-wrapper=docker_wrapper:main",
        ],
    },
)
