# Insecure Flask App

This is a simple Flask web application created for assignment.

## Features
- User registration and login
- Post creation
- Image upload
- SQLite database

## How to Run

### Without Docker
pip install -r requirements.txt
python app.py

### With Docker
docker build -t tulasi-app .
docker run -p 5000:5000 tulasi-app

Open browser:
http://localhost:5000
