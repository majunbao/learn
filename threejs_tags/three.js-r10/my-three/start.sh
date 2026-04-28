#!/bin/bash
echo "Starting My Three.js Demo Server..."
echo ""
echo "Open http://localhost:8080/examples/demo.html in your browser"
echo ""
cd "$(dirname "$0")"
python3 -m http.server 8080
