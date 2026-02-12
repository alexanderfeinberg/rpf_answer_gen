#!/bin/bash
echo -e "\n (1) BUILDING Postgres & pgVector CONTAINER (20 seconds) \n"

if command -v docker-compose &> /dev/null
then
    # Bring down any existing docker containers
    sudo docker-compose down
    # Bring up the containers again (build fresh)
    sudo docker-compose up -d --build
else
# Bring down any existing docker containers
    sudo docker compose down
    # Fallback to new docker compose
    sudo docker compose up -d --build
fi

# Wait a few seconds to let Postgres fully boot
sleep 20

echo -e "\n (2) CHECKING DATABASE TABLES \n"

# Create tables
CONFIG_PATH="${CONFIG_FILE:-config/global.ini}"

python -u -m answer_gen.storage.db

echo -e "\n (3) SEEDING VERSION TABLES \n"
python -u -m answer_gen.storage.seed_chunk_versions "$CONFIG_PATH"
python -u -m answer_gen.storage.seed_answer_versions "$CONFIG_PATH"

echo -e "\n (4) Installing node dependencies \n"
cd answer_ui/
npm install

echo -e "\n (5) Launching web application at \n"
npm run dev&
sleep 2

echo -e "\n (6) Launching Document Ingestion & Answer API \n"
cd ../
python -m answer_gen.server.server
