"""Setup configuration for storybench."""

from setuptools import setup, find_packages

setup(
    name="storybench",
    version="0.1.0",
    description="A modular tool for evaluating the creativity of LLMs",
    author="Todd",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "llama-cpp-python>=0.2.0",
        "huggingface-hub>=0.16.0",
        "nvidia-ml-py>=12.535.0",
        "openai>=1.0.0",
        "anthropic>=0.20.0",
        "google-generativeai>=0.3.0",
        "aiohttp>=3.8.0",
        "pyyaml>=6.0",
        "tqdm>=4.65.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "pre-commit>=3.3.0",
            "mypy>=1.4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "storybench=storybench.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Researchers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
