"""Setup configuration for storybench."""

from setuptools import setup, find_packages

setup(
    name="storybench",
    version="0.2.0",
    description="Enterprise LLM creativity evaluation with MongoDB Atlas backend",
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
        # Web interface dependencies
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "aiofiles>=23.2.0",
        "pydantic>=2.5.0",
        # MongoDB dependencies (Phase 4)
        "motor>=3.3.0",
        "pymongo>=4.6.0",
        "bson>=0.5.10",
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
            # Web UI testing dependencies
            "selenium>=4.22.0",
            "pytest-selenium>=4.1.0",
            "pytest-html>=4.0.0",
            "webdriver-manager>=4.0.1",
            "requests>=2.26.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "storybench=storybench.cli:cli",
            "storybench-web=storybench.web.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Researchers",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11", 
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Database :: Database Engines/Servers",
    ],
)
