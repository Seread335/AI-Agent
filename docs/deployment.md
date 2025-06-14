# Deployment Guide

This guide covers different deployment options for the AI Agent System.

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Using Docker Compose

1. Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  ai-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - QWEN_API_KEY=${QWEN_API_KEY}
      - AGENTICA_API_KEY=${AGENTICA_API_KEY}
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - ai-agent

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secret
    volumes:
      - grafana-storage:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  grafana-storage:
```

2. Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-agent'
    static_configs:
      - targets: ['ai-agent:8000']
```

4. Deploy:
```bash
docker-compose up -d
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured
- helm (optional)

### Deployment Steps

1. Create Kubernetes manifests:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agent
  template:
    metadata:
      labels:
        app: ai-agent
    spec:
      containers:
      - name: ai-agent
        image: ai-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEEPSEEK_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-agent-secrets
              key: deepseek-api-key
        resources:
          limits:
            cpu: "1"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-agent
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: ai-agent
```

2. Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Production Considerations

### Security
- Set up proper authentication
- Use HTTPS/TLS
- Implement rate limiting
- Secure API keys in a vault

### Monitoring
- Set up Prometheus metrics
- Configure Grafana dashboards
- Set up log aggregation (e.g., ELK stack)
- Configure alerts

### Scaling
- Use load balancer
- Implement caching
- Configure auto-scaling
- Monitor resource usage

### Backup
- Regular database backups
- Configuration backups
- Log retention policy

### Maintenance
- Regular security updates
- Performance optimization
- API version management
- Regular health checks
