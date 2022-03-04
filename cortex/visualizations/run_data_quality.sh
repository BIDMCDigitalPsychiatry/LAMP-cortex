#!/bin/bash
apt-get update -y
pip -q install LAMP-core && \
pip -q install pytz && \
pip -q install altair && \
pip -q install pandas && \
pip -q install LAMP-cortex

python3 -c'import sys, cortex.visualizations; cortex.visualizations.data_quality.data_quality(sys.argv[1])' "$1"
