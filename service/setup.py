from setuptools import setup, find_packages

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="adaptive-rehab-ai",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-driven adaptive difficulty system for VR rehabilitation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arartawil/adaptive-rehab-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "grpcio>=1.60.0",
        "grpcio-tools>=1.60.0",
        "protobuf>=4.25.0",
        "pyyaml>=6.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "stable-baselines3>=2.2.0",
        "scikit-fuzzy>=0.4.2",
        "gymnasium>=0.29.0",
        "python-dotenv>=1.0.0",
        "colorlog>=6.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "adaptrehab-service=adaptrehab.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "adaptrehab": ["configs/*.yaml"],
    },
)
