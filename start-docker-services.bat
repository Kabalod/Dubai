@echo off
echo Starting all services via Docker Compose...
echo.

echo Starting Django Backend (realty-main)...
cd realty-main
docker compose --profile local up --build -d
echo Django Backend started on http://localhost:8000
echo.

echo Starting React Frontend (DXB-frontend-develop)...
cd ..\DXB-frontend-develop
docker compose up --build -d
echo React Frontend started on http://localhost:3000
echo.

echo Starting pfimport-main...
cd ..\pfimport-main
python manage.py runserver 8002
echo pfimport-main started on http://localhost:8002
echo.

echo All services started!
echo.
echo Frontend: http://localhost:3000
echo Django Backend: http://localhost:8000
echo pfimport: http://localhost:8002
echo.
echo Press any key to exit...
pause > nul
