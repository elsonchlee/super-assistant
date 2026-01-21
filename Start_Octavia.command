#!/bin/bash
# 🦅 Octavia Launcher
# This script forces Chrome to open Octavia in a standalone window (App Mode)

echo "Starting Octavia System..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --app="https://elsonchlee-super-assistant-app-leyv8e.streamlit.app/"

# Close this terminal window after launching
osascript -e 'tell application "Terminal" to close front window' & exit
