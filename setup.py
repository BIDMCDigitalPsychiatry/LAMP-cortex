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
    version="1.0.1,
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
      "altair".
      "tzwhere",
      "geopy",
      "pytz",
    ],
    extras_require={':python_version >= "3.6"': ['future']},
    packages=find_packages(exclude=["test", "tests"]),
    include_package_data=True,
    long_description="""\
    The LAMP Analysis Pipeline.
    """
)
