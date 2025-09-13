#!/bin/bash

echo "Monitoring Voice Control debug messages..."
echo "Start kitty and try Voice Control dictation"
echo "Press Ctrl+C to stop monitoring"
echo "----------------------------------------"

# Stream console logs filtering for Voice Control debug messages
log stream --predicate 'eventMessage contains "[VC-Debug]"' --style compact