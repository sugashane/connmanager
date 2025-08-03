from setuptools import find_packages, setup

setup(
    name="connmanager",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "cm=connmanager.main:main",
        ],
    },
    author="Shane Bebber",
    author_email="shanebebber@gmail.com",
    description="A connection manager for SSH, RDP, VNC, and VMRC.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/sugashane/connmanager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "cryptography"
    ],
)
