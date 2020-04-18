from setuptools import setup, find_packages

setup(
    name="misc-crypto",
    version="1.0",
    description="Mischievous cryptography implementations",
    author="Chih-Cheng Liang",
    author_email="cc@ethereum.org",
    packages=find_packages(exclude=("tests")),
    install_requires=["eth-utils>=1.8.4,<2", "py-ecc==2.0.0"],
    python_requires=">=3.5, <4",
    extras_require={
        "test": ["pytest>=5.3.2"],
        "lint": ["black>=19.3b0", "mypy==0.740"],
    },
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
