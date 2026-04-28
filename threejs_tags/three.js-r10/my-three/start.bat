@echo off
echo Starting My Three.js Demo Server...
echo.
echo Open http://localhost:8080/examples/demo.html in your browser
echo.
cd /d "%~dp0"
python -m http.server 8080
