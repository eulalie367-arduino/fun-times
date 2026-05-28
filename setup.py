"""Setup configuration for RAG Pipeline."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rag-pipeline",
    version="1.0.0",
    author="Anthropic",
    description="Production-Ready Retrieval-Augmented Generation Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anthropics/rag-pipeline",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "chromadb>=0.4.24",
        "sentence-transformers>=2.2.2",
        "huggingface-hub>=0.20.1",
        "anthropic>=0.28.0",
        "pydantic>=2.6.1",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
        "tenacity>=8.2.3",
        "structlog>=24.1.0",
        "python-json-logger>=2.0.7",
        "prometheus-client>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
