from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gollm",
    version="0.1.0",
    author="Tom Sapletta",
    author_email="info@softreck.dev",
    description="Go Learn, Lead, Master! - Inteligentny system kontroli jakości kodu z integracją LLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wronai/gollm",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8.1",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "toml>=0.10.0",
        "psutil>=5.0.0",
        "aiofiles>=0.8.0",
        "pydantic>=1.10.0",
        "aiohttp>=3.9.0"
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'coverage>=7.0.0',
        ],
        'llm': [
            'openai>=1.0.0',
            'anthropic>=0.3.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'gollm=gollm.cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='code-quality linting llm python automation',
)
