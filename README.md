# Feature Flags App

A lightweight **Feature Flags App** built with **Python** (**Flask**), **MongoDB** and a frontend using HTML, CSS, and JavaScript.

This app lets you create, update, toggle, and delete feature flags across multiple environments (`development`, `staging`, `production`).  

<img src="feature-flags-web-demo.png" alt="feature-flags-web-demo" width="1000">

### Repositories Structure
This project is split into three repositories, each with a specific role in the deployment and delivery workflow:

 1. **Application** Repository **([feature-flags-app](https://github.com/shaarron/feature-flags-app#))** **<--Current Repo**
     * Contains the Feature Flags API & UI 
     * Contains the GitHub Actions workflows to build the feature-flags-app image & sync frontend s3 bucket 

2. **Infrastructure** Repository **([feature-flags-infrastructure](https://github.com/shaarron/feature-flags-infrastructure))**  
   * Contains Terraform code for provisioning the required AWS resources (VPC, EKS, S3, CloudFront, Route53, etc.).
   * Contains the GitHub Actions workflow to apply the terraform
3. **Resources** Repository **([feature-flags-resources](https://github.com/shaarron/feature-flags-resources))** 
   * Holds Helm charts and Argo CD Applications that define the Kubernetes manifests. 
   * Implements GitOps: Argo CD watches this repo and syncs changes to the EKS cluster.


  
## Table of Contents

  - [**Github Actions**](#github-actions)
    - [Feature Flags CI/CD](#feature-flags-cicd)
    - [Sync Frontend to S3](#sync-frontend-to-s3)

  - [**Architecture**](#architecture)
    - [Service Architecture](#service-architecture)
    - [Docker Compose Architecture](#docker-compose-architecture)
    - [Full Flow Architecture](#full-flow-architecture)
    - [VPC Architecture](#vpc-architecture)

  - [**Observabillity**](#observabillity)
    - [Monitoring](#monitoring)
    - [Logging](#logging)
  - [**Running locally**](#running-locally)
    - [Using Docker Compose](#using-docker-compose)
    - [Running app as a standalone](#running-app-as-a-standalone-no-db-using-python-virtual-environment)
  - [**API Documentation**](#api-documentation)
## Github Actions

### [Feature Flags CI/CD](.github/workflows/feature-flags-ci-cd.yaml) 
This GitHub Actions workflow automates testing, versioning, and publishing of the **Feature Flags API** Docker image to **AWS Elastic Container Registry (ECR)** & GitHub Container Registry (**GHCR**).


### [Sync Frontend to S3](.github/workflows/s3-frontend-sync.yaml)

This workflow detects changes in frontend dir (on push to **[/frontend](/frontend))** and syncs the changes to the s3 bucket that holds those static files.

### [Feature Flags Infrastructure](.github/workflows/feature-flags-infrastructure.yaml)

This workflow runs Terraform from the **[feature-flags-infrastructure](https://github.com/shaarron/feature-flags-infrastructure)** repository to provision AWS infrastructure resources.

## Architecture 

### Service Architecture 

**API**:
   - Acts as the core API server for managing feature flags.
   - Provides endpoints for creating, updating, toggling, and deleting feature flags.
   - Includes environment-specific configurations for `dev`, `staging`, `prod`.

 **MongoDB**:
   - Serves as the persistent storage for feature flags.

**Frontend**:
   - Static, Stored in S3 and served via CloudFront.

### Full Flow Architecture

![feature-flags-full-architecture](/feature-flags-full-diagram.svg)

### VPC Architecture - High Availability

![feature-flags-full-architecture](/ff-vpc-diagram.svg)



## Observabillity 
### Monitoring

Prometheus metrics: available at **/metrics**
### Logging 
Structured logs: JSON format with latency, method, status, and path.

## Running locally

### Using Docker Compose

#### Docker Compose architecture 

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


#### Instructions 
```bash
git clone https://github.com/shaarron/feature-flags-app.git

cd feature-flags-app


# Create environment file (optional - defaults will be used if not provided)
cat > .env << EOF
MONGO_INITDB_ROOT_USERNAME=
MONGO_INITDB_ROOT_PASSWORD=
EOF

# Start all services
docker compose -f docker-compose.local.yaml up -d
```

The application will be available at:
- **Web Interface**: http://localhost
- **API**: http://localhost/flags
- **MongoDB**: localhost:27017


### Running app as a standalone (no DB): Using Python Virtual Environment

```bash
git clone https://github.com/shaarron/feature-flags-app.git
cd feature-flags-app

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate 

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at http://localhost:5000


## API Documentation

### Endpoints
  
#### 1. Create a Feature Flag
```
POST /flags 
```
##### Request Body:

```sh
{
  "name": "dark-mode",
  "description": "Enable dark theme for all users",
  "environments": {
    "development": true,
    "staging": true,
    "production": false
  }
}
```
**Response (201)
**
```sh
{
  "_id": "abc123",
  "name": "dark-mode",
  "description": "Enable dark theme for all users",
  "environments": {...}
}
```

#### 2. Get All Flags

```
GET /flags?environment=staging
```

Retrieves all feature flags, with an `enabled` field for the selected environment.

**Response**
```sh
[
  {
    "_id": "abc123",
    "name": "dark-mode",
    "description": "Enable dark theme for all users",
    "environments": {...},
    "enabled": true
  }
]
```

#### 3. Get a Single Flag
```
GET /flags/<id>
```

Fetches a specific feature flag by ID.

**Response**
```sh
{
  "_id": "abc123",
  "name": "dark-mode",
  "description": "Enable dark theme for all users",
  "environments": {...}
}
```

##### 4. Update a Flag
```
PUT /flags/<id>
```
Updates name, description, or environment states.

**Request Body** (partial update allowed):
```sh
{
  "description": "Enable dark mode toggle for users"
}
```

 **Response**
```sh
{
  "_id": "abc123",
  "name": "dark-mode",
  "description": "Enable dark mode toggle for users",
  "environments": {...}
}
```

##### 5. Delete a Flag
```
DELETE /flags/<id>
```
Deletes a feature flag.

**Response (204):**
```sh
{
  "message": "Feature flag deleted"
}
```

#### 6. Toggle a Flag
```
POST /flags/<id>/toggle
```
Toggles a flag’s enabled state in a given environment.

**Request Body:**
```sh
{
  "environment": "production"
}
```

**Response (200)**
```sh
{
  "_id": "abc123",
  "name": "dark-mode",
  "enabled": true
}
```


