from setuptools import setup, find_packages

setup(
    name="batch-annotation-tool",
    version="0.1.0",
    description="Comprehensive batch annotation tool for biomedical image classification",
    author="BioAST Team",
    author_email="team@bioast.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "Pillow>=8.3.0",
        "PyYAML>=5.4.0",
        "click>=8.0.0",
        "tqdm>=4.62.0",
        "scikit-learn>=1.0.0",
        "torch>=1.9.0",
        "torchvision>=0.10.0",
        "onnxruntime>=1.8.0",
        "opencv-python>=4.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "pytest-mock>=3.6.0",
            "black>=21.7.0",
            "flake8>=3.9.0",
            "isort>=5.9.0",
            "mypy>=0.910",
            "bandit>=1.7.0",
            "radon>=5.1.0",
            "mutmut>=2.2.0",
            "hypothesis>=6.14.0",
        ],
        "web": [
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
            "jinja2>=3.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "batch-annotate=batch_annotation_tool.src.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)