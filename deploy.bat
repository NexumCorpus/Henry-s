@echo off
REM Henry's SmartStock AI - Production Deployment Script (Windows)
REM Usage: deploy.bat [environment]
REM Example: deploy.bat production

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

set COMPOSE_FILE=docker-compose.prod.yml

echo 🚀 Starting deployment for Henry's SmartStock AI - %ENVIRONMENT% environment

REM Check if required files exist
if not exist ".env" (
    echo ❌ Error: .env file not found. Please copy .env.production to .env and configure it.
    exit /b 1
)

if not exist "%COMPOSE_FILE%" (
    echo ❌ Error: %COMPOSE_FILE% not found.
    exit /b 1
)

echo 📋 Pre-deployment checks...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: docker-compose is not installed.
    exit /b 1
)

echo ✅ Pre-deployment checks passed

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "logs\nginx" mkdir logs\nginx
if not exist "nginx\ssl" mkdir nginx\ssl
if not exist "backups" mkdir backups

REM Stop existing containers
echo 🛑 Stopping existing containers...
docker-compose -f %COMPOSE_FILE% down --remove-orphans

REM Pull latest images
echo 📥 Pulling latest images...
docker-compose -f %COMPOSE_FILE% pull

REM Build and start services
echo 🏗️  Building and starting services...
docker-compose -f %COMPOSE_FILE% up -d --build

REM Wait for services to be healthy
echo ⏳ Waiting for services to be healthy...
timeout /t 30 /nobreak >nul

echo 🏥 Checking service health...

REM Check backend
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend health check failed
    exit /b 1
) else (
    echo ✅ Backend is healthy
)

REM Check frontend
curl -f http://localhost:80/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Frontend health check failed
    exit /b 1
) else (
    echo ✅ Frontend is healthy
)

REM Run database migrations
echo 🗄️  Running database migrations...
docker-compose -f %COMPOSE_FILE% exec backend alembic upgrade head

REM Show deployment status
echo 📊 Deployment Status:
docker-compose -f %COMPOSE_FILE% ps

echo 🎉 Deployment completed successfully!
echo.
echo 📱 Application URLs:
echo    Frontend: http://localhost:80
echo    Backend API: http://localhost:8000
echo    API Documentation: http://localhost:8000/docs
echo.
echo 🔐 Default Admin Credentials:
echo    Email: admin@henrysonmarket.com
echo    Password: admin123
echo    ⚠️  Please change the default password immediately!
echo.
echo 📝 Next Steps:
echo    1. Change the default admin password
echo    2. Configure SSL certificates for HTTPS
echo    3. Set up domain name and DNS
echo    4. Configure backup schedule
echo    5. Set up monitoring and alerts
echo.
echo 📚 View logs: docker-compose -f %COMPOSE_FILE% logs -f [service_name]
echo 🛑 Stop services: docker-compose -f %COMPOSE_FILE% down

pause