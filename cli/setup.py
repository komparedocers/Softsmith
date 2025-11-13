from setuptools import setup, find_packages

setup(
    name="smaker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer==0.9.0",
        "requests==2.31.0",
        "rich==13.7.0",
        "websocket-client==1.7.0",
    ],
    entry_points={
        "console_scripts": [
            "smaker=smaker.main:app",
        ],
    },
)
