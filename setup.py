# coding: utf-8

"""
    LAMP Platform

    The LAMP Platform API.

    The version of the OpenAPI document: 1.0.0
    Contact: team@digitalpsych.org
"""

from setuptools import setup, find_packages

setup(
    name="LAMP_cortex",
    version="1.0.3",
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
      "lifelines"
    ],
    python_requires='>=3',
    packages=find_packages(exclude=["test", "tests"]),
    include_package_data=True,
    long_description="""\
    The LAMP Analysis Pipeline.
    """
)
