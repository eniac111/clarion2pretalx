#!/bin/bash

./venv/bin/gunicorn pretalx.wsgi --name pretalx --workers 1 --max-requests 1200  --max-requests-jitter 50 --log-level=debug --bind=127.0.0.1:8345  
