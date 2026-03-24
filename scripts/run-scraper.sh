#!/bin/bash
# Env-Vars aus /proc/1/environ laden (vom Docker-Hauptprozess)
export $(xargs -0 < /proc/1/environ)
cd /app
python run.py --all
