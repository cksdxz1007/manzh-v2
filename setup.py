from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="manzh",
    version="1.0.4",
    author="cynning",
    author_email="cynningli@gmail.com",
    description="Man手册中文翻译工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cksdxz1007/ManZH",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: System :: Systems Administration",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Utilities"
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "manzh=manzh.cli:main",
        ],
    },
    scripts=[
        "bin/manzh",
    ],
    package_data={
        "manzh": ["config.json.example"],
    },
    data_files=[
        ("share/man/man1", ["docs/manzh.1"]),
    ],
    py_modules=["main"],
)
