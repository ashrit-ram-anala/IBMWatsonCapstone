#!/bin/bash

# IBM Banking Data Pipeline - Quick Start Script
# This script helps you quickly set up and start the application

set -e

echo "=================================="
echo "IBM Banking Data Pipeline Setup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠ No .env file found. Creating from .env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✓ Created backend/.env file${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Please edit backend/.env and add your IBM Watsonx credentials:${NC}"
    echo "  - WATSONX_API_KEY"
    echo "  - WATSONX_PROJECT_ID"
    echo "  - IBM_CLOUD_API_KEY"
    echo ""
    read -p "Have you added your credentials? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Please add your credentials to backend/.env and run this script again${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Environment configuration found${NC}"
echo ""

# Build and start services
echo "Starting services with Docker Compose..."
echo ""

docker-compose up -d --build

echo ""
echo -e "${GREEN}✓ Services are starting...${NC}"
echo ""

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Services are running!${NC}"
else
    echo -e "${RED}✗ Some services failed to start${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "=================================="
echo "🎉 Setup Complete!"
echo "=================================="
echo ""
echo "Access your application:"
echo -e "  ${GREEN}Frontend Dashboard:${NC} http://localhost:4200"
echo -e "  ${GREEN}API Documentation:${NC}  http://localhost:8000/docs"
echo -e "  ${GREEN}API Health Check:${NC}   http://localhost:8000/health"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  View status:      docker-compose ps"
echo ""
echo "Sample data available at: sample_data/transactions_sample.csv"
echo ""
echo "For detailed setup instructions, see SETUP.md"
echo "=================================="
