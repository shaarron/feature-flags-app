# Feature Flags Service

A lightweight **Feature Flags Service** built with **Flask** and **MongoDB**,  
This app lets you create, update, toggle, and delete feature flags across multiple environments (`development`, `staging`, `production`).  

### CI/CD 
This repository includes a **GitHub Actions workflow** that automates testing, versioning, and publishing of the **Feature Flags API** Docker image to **AWS Elastic Container Registry (ECR)** & GitHub Container Registry (**GHCR**).


## Architecture 

### Service Architecture 

**API**:
   - Acts as the core API server for managing feature flags.
   - Provides endpoints for creating, updating, toggling, and deleting feature flags.
   - Includes environment-specific configurations for `development`, `staging`, and `production`.

 **DB**:
   - Serves as the persistent storage for feature flags.
   - Stores data in collections, with support for indexing and querying.
   - If DB is unavailable, the app falls back to an in-memory storage option.

### Docker Compose Architecture

The `docker-compose.yml` file orchestrates the following services:

   
- **app (Flask API)**:
  - Runs the Flask application inside a Python-based Docker container.
  - Exposes port `5000` internally for communication with Nginx.
  - Connects to **MongoDB** for persistence.

- **Mongodb**:
  - Stores feature flag configurations.
  - Runs on port 27017 inside the container.
  - Persists data on a mounted Docker volume (**db-data**).

- **Nginx**:
  - Acts as a reverse **proxy** for the Flask API.
  - Listens on port **80** of the host for external access.
  - Routes incoming requests to the Flask backend on port 5000.
  - Serves the static UI assets (index.html, app.js)

- **Networks**:
    - **app-network**: Connects **Nginx** ↔ **API**. 
    - **db-network**: Connects **API** ↔ **MongoDB**. 


- **Volumes**:
    - **db-data**: Ensures MongoDB data is persisted across container restarts.
    - **Config mounts** (./nginx.conf, ./static, ./templates) are shared with the Nginx service for configuration and static asset serving.



![dokcer-compose-architecture](/docker-compose-architecture.svg)

### Full Flow Architecture

![feature-flags-full-architecture](/feature-flags-full-diagram.svg)



## Requirements

- **Python 3.9+**
- **MongoDB** (optional – falls back to in-memory storage if not available)

## Running locally


### Using Docker Compose

```bash
git clone https://github.com/your-username/feature-flags-service.git
cd feature-flags-service

# Create environment file (optional - defaults will be used if not provided)
cat > .env << EOF
MONGO_INITDB_DATABASE=
MONGO_INITDB_ROOT_USERNAME=
MONGO_INITDB_ROOT_PASSWORD=
EOF

# Start all services
docker-compose up -d
```

The application will be available at:
- **Web Interface**: http://localhost
- **API**: http://localhost/flags
- **MongoDB**: localhost:27017


### Running APP as a standalone (no DB): Using Python Virtual Environment

```bash
git clone https://github.com/your-username/feature-flags-service.git
cd feature-flags-service

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate 

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be availble at http://localhost:5000




