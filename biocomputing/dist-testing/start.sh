#!/bin/bash

serve -s bioweb/panel/build -l 3200 &
python3 bioweb/flask_server.py
