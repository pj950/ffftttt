from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="futu-tsi-ewo-signals",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Futu intraday TSI/EWO signal generator with backtesting and WeChat notifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/futu-tsi-ewo-signals",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "futu-backtest=src.backtest.run_backtest:main",
            "futu-signals=src.realtime.signal_runner:main",
        ],
    },
)
