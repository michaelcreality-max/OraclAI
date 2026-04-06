"""
Production Deployment Configuration
Docker, Kubernetes, and cloud deployment configs
"""

import os
from typing import Dict, Any, Optional

# ============================================================================
# DOCKER CONFIGURATION
# ============================================================================

DOCKERFILE = '''
# Production Dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app directory
WORKDIR /app

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "production_server:app"]
'''

DOCKER_COMPOSE = '''
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///data/oraclai.db
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  redis_data:
'''

# ============================================================================
# KUBERNETES CONFIGURATION
# ============================================================================

K8S_DEPLOYMENT = '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oraclai-app
  labels:
    app: oraclai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: oraclai
  template:
    metadata:
      labels:
        app: oraclai
    spec:
      containers:
      - name: oraclai
        image: oraclai:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          value: "postgresql://user:pass@db:5432/oraclai"
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: oraclai-secrets
              key: github-token
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: oraclai-service
spec:
  selector:
    app: oraclai
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: LoadBalancer
'''

K8S_CONFIGMAP = '''
apiVersion: v1
kind: ConfigMap
metadata:
  name: oraclai-config
data:
  LOG_LEVEL: "INFO"
  CACHE_TTL: "3600"
  MAX_WORKERS: "4"
  ENABLE_METRICS: "true"
'''

K8S_SECRETS = '''
apiVersion: v1
kind: Secret
metadata:
  name: oraclai-secrets
type: Opaque
stringData:
  github-token: "${GITHUB_TOKEN}"
  database-password: "${DB_PASSWORD}"
  jwt-secret: "${JWT_SECRET}"
'''

K8S_HPA = '''
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: oraclai-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: oraclai-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
'''

# ============================================================================
# NGINX CONFIGURATION
# ============================================================================

NGINX_CONFIG = '''
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:5000;
    }

    server {
        listen 80;
        server_name localhost;
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        location /health {
            proxy_pass http://app/health;
            access_log off;
        }

        location /static {
            alias /app/static;
            expires 1d;
            add_header Cache-Control "public, immutable";
        }
    }
}
'''

# ============================================================================
# GITHUB ACTIONS CI/CD
# ============================================================================

GITHUB_WORKFLOW = '''
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        python -m pytest test_suite.py -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install linters
      run: |
        pip install flake8 black isort
    
    - name: Run linters
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
        isort --check-only .

  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      uses: securecodewarrior/github-action-add-sarif@v1
    
    - name: Check for vulnerabilities
      run: |
        pip install safety bandit
        safety check
        bandit -r . -f json -o bandit-report.json || true

  build:
    needs: [test, lint]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t oraclai:${{ github.sha }} .
        docker tag oraclai:${{ github.sha }} oraclai:latest
    
    - name: Test Docker image
      run: |
        docker run --rm -p 5000:5000 -d --name test oraclai:${{ github.sha }}
        sleep 5
        curl -f http://localhost:5000/health || exit 1
        docker stop test

  deploy:
    needs: [build, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl apply -f k8s/
        kubectl rollout status deployment/oraclai-app
'''

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

ENV_EXAMPLE = '''
# Application
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///oraclai.db
# For PostgreSQL: postgresql://user:password@localhost:5432/oraclai

# GitHub Integration
GITHUB_TOKEN=your-github-personal-access-token

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs

# Cache
CACHE_TYPE=redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION_HOURS=24

# External APIs (optional)
# ALPHA_VANTAGE_API_KEY=
# POLYGON_API_KEY=

# Deployment
PORT=5000
HOST=0.0.0.0
WORKERS=4
'''

# ============================================================================
# GUNICORN CONFIGURATION
# ============================================================================

GUNICORN_CONFIG = '''
# Gunicorn configuration
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
errorlog = "-"
accesslog = "-"
loglevel = "info"

# Process naming
proc_name = "oraclai"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"

# SSL (if using)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Server hooks
def on_starting(server):
    print("Starting OraclAI server...")

def on_exit(server):
    print("Shutting down OraclAI server...")
'''

# ============================================================================
# DEPLOYMENT HELPER FUNCTIONS
# ============================================================================

def create_deployment_files(base_path: str = "deployment"):
    """Create all deployment configuration files"""
    os.makedirs(base_path, exist_ok=True)
    
    files = {
        "Dockerfile": DOCKERFILE,
        "docker-compose.yml": DOCKER_COMPOSE,
        "nginx.conf": NGINX_CONFIG,
        "gunicorn.conf.py": GUNICORN_CONFIG,
        
        # K8s files
        "k8s/01-namespace.yml": "apiVersion: v1\\nkind: Namespace\\nmetadata:\\n  name: oraclai\\n",
        "k8s/02-configmap.yml": K8S_CONFIGMAP,
        "k8s/03-secrets.yml": K8S_SECRETS,
        "k8s/04-deployment.yml": K8S_DEPLOYMENT,
        "k8s/05-hpa.yml": K8S_HPA,
        
        # GitHub Actions
        ".github/workflows/ci-cd.yml": GITHUB_WORKFLOW,
        
        # Environment
        ".env.example": ENV_EXAMPLE
    }
    
    for filepath, content in files.items():
        full_path = os.path.join(base_path, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"Created: {full_path}")
    
    return base_path


def get_deployment_summary() -> Dict[str, Any]:
    """Get summary of deployment configuration"""
    return {
        "containerization": {
            "docker": True,
            "docker_compose": True,
            "multi_stage_build": True,
            "health_checks": True
        },
        "orchestration": {
            "kubernetes": True,
            "auto_scaling": True,
            "load_balancing": True,
            "secrets_management": True
        },
        "cicd": {
            "github_actions": True,
            "automated_testing": True,
            "security_scanning": True,
            "auto_deployment": True
        },
        "monitoring": {
            "health_endpoints": True,
            "logging": True,
            "metrics": True
        },
        "security": {
            "non_root_user": True,
            "secret_management": True,
            "ssl_support": True
        }
    }


if __name__ == '__main__':
    path = create_deployment_files()
    print(f"\\nDeployment files created in: {path}")
    print("\\nTo deploy:")
    print("1. Local: docker-compose up -d")
    print("2. Kubernetes: kubectl apply -f deployment/k8s/")
    print("3. CI/CD: Push to GitHub, actions will deploy automatically")
