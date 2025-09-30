#!/bin/bash

# Simple script to run the TUI from the development environment
cd "$(dirname "$0")"
PYTHONPATH="$(pwd)" .venv/bin/python3.13 -m connmanager.main tui
