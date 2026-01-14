"""
Adaptive Rehab AI - Real-time AI-powered difficulty adaptation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="adaptive-rehab-ai",
    version="0.1.0",
    author="AR Artawil",
    author_email="your.email@example.com",  # Update this
    description="Real-time AI-powered difficulty adaptation for VR rehabilitation and games",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arartawil/adaptive-rehab-ai",
    project_urls={
        "Bug Tracker": "https://github.com/arartawil/adaptive-rehab-ai/issues",
        "Documentation": "https://github.com/arartawil/adaptive-rehab-ai#readme",
        "Source Code": "https://github.com/arartawil/adaptive-rehab-ai",
    },
    packages=find_packages(where="service"),
    package_dir={"": "service"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
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
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "grpcio>=1.60.0",
        "grpcio-tools>=1.60.0",
        "protobuf>=4.25.0",
        "pyyaml>=6.0",
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "pydantic>=2.5.0",
        "httpx>=0.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.7.0",
        ],
        "ui": [
            "tk>=0.1.0",  # Tkinter for demo UIs
        ],
        "ml": [
            "stable-baselines3>=2.2.0",  # For RL module (future)
            "scikit-fuzzy>=0.4.2",       # For fuzzy logic module (future)
            "numpy>=1.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "adaptrehab-grpc=adaptrehab.comms.run_grpc_server:main",
            "adaptrehab-rest=adaptrehab.comms.run_rest_server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "adaptrehab": ["*.yaml", "proto/*.proto"],
    },
    keywords=[
        "rehabilitation",
        "vr",
        "adaptive",
        "ai",
        "difficulty-adjustment",
        "therapy",
        "gaming",
        "machine-learning",
        "healthcare",
    ],
    zip_safe=False,
)
