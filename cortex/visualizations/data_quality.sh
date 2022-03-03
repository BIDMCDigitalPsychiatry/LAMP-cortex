#!/bin/bash
apt-get update -y
pip -q install LAMP-core && \
pip -q install pytz && \
pip -q install altair && \
pip -q install pandas && \
pip -q install LAMP-cortex

python3 visualizations/data_quality.py --researcher-id $2
