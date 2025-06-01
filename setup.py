from setuptools import setup, find_packages

setup(
    name="spyq",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "toml>=0.10.0", 
        "psutil>=5.0.0",
        "aiofiles>=0.8.0",
        "pydantic>=1.10.0"
    ],
    entry_points={
        "console_scripts": [
            "spyq=spyq.cli:cli",
        ],
    },
)
