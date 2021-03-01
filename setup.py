# coding: utf-8

"""
    LAMP Cortex 

    Data anlysis pipeline for the LAMP platform
    Contact: team@digitalpsych.org
"""

from setuptools import setup, find_packages

__version__ = "develop"

setup(
    name="LAMP_cortex",
    version=__version__,
    description="LAMP Platform",
    author="Division of Digital Psychiatry at Beth Israel Deaconess Medical Center.",
    author_email="team@digitalpsych.org",
    url="https://docs.lamp.digital/",
    keywords=["LAMP Cortex"],
    install_requires=[
      "LAMP-core",
      "datetime",
      "numpy",
      "pandas",
      "altair",
      "tzwhere",
      "geopy>=2.0",
      "pytz",
      "tzwhere", 
      "entrypoints", 
      "tool",
      "lifelines", 
      "sklearn"
    ],
    python_requires='>=3',
    packages=find_packages(exclude=["test", "tests"]),
    include_package_data=True,
    long_description="""\
    The LAMP Analysis Pipeline.
    """
)
