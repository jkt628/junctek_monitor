"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""

import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()
URL = "https://github.com/AnalogThinker/junctek_monitor"

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="junctek_monitor",
    version="0.1.0",
    url=URL,
    description="Publish to MQTT from Juntek / Junctek / Koolertron Battery Monitor (KG KF series)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AnalogThinker",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GPLv3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="juntek, junctek, koolertron, battery monitor, mqtt",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11, <4",
    install_requires=[
        "bleak",
        "paho-mqtt",
        "PyYAML",
        "pyserial",
    ],
    entry_points={
        "console_scripts": [
            "BTjuntek=junctek_monitor.BTjuntek:main",
            "juntek485=junctek_monitor.juntek485:main",
        ],
    },
    package_data={
        "": [
            "jt_mqtt.yaml",
            "ha-jt.service",
        ],
    },
    project_urls={  # Optional
        "Bug Reports": URL + "/issues",
        "Source": URL,
    },
)
