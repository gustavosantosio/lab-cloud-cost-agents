# API Documentation

## Base URL
- **Demo**: https://y0h0i3cqn6yq.manus.space
- **Local**: http://localhost:5000

## Authentication
Atualmente não é necessária autenticação para a versão demo.

## Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-25T10:00:00Z",
  "service": "Cloud Cost Analysis API - Demo Version",
  "version": "1.0.0"
}
```

### Providers Information
```http
GET /api/providers/info
```

**Response:**
```json
{
  "providers": {
    "aws": {
      "name": "Amazon Web Services",
      "regions": ["us-east-1", "us-east-2", "..."],
      "instance_types": ["t3.micro", "t3.small", "..."],
      "storage_types": ["s3_standard", "s3_ia", "..."]
    },
    "gcp": {
      "name": "Google Cloud Platform",
      "regions": ["us-central1", "us-east1", "..."],
      "machine_types": ["e2-micro", "e2-small", "..."],
      "storage_types": ["standard", "nearline", "..."]
    }
  },
  "workload_types": ["general", "compute_intensive", "..."],
  "performance_priorities": ["cost_optimized", "balanced", "..."]
}
```

### Analysis Templates
```http
GET /api/templates
```

**Response:**
```json
{
  "templates": {
    "startup_web_app": {
      "name": "Startup Web Application",
      "description": "Configuração típica para aplicação web de startup",
      "aws_instance_type": "t3.small",
      "gcp_machine_type": "e2-small",
      "aws_storage_type": "s3_standard",
      "gcp_storage_type": "standard",
      "storage_size_gb": 100,
      "workload_type": "web_application",
      "monthly_budget": 200
    }
  }
}
```

### Analysis History
```http
GET /api/analysis/history
```

**Response:**
```json
{
  "analyses": [
    {
      "id": "1",
      "type": "comprehensive",
      "timestamp": "2025-01-15T10:30:00Z",
      "status": "completed",
      "recommendation": "AWS",
      "savings_potential": 25.5
    }
  ]
}
```

### Compute Analysis
```http
POST /api/analyze/compute
```

**Request Body:**
```json
{
  "aws_instance_type": "t3.medium",
  "gcp_machine_type": "e2-medium",
  "aws_region": "us-east-1",
  "gcp_region": "us-central1",
  "workload_type": "general"
}
```

**Response:**
```json
{
  "analysis_type": "compute_costs",
  "requirements": {
    "aws_instance_type": "t3.medium",
    "gcp_machine_type": "e2-medium",
    "aws_region": "us-east-1",
    "gcp_region": "us-central1",
    "workload_type": "general"
  },
  "result": {
    "recommendation": "AWS",
    "aws_cost": 156.80,
    "gcp_cost": 204.30,
    "savings": 23.5,
    "confidence": 87,
    "reasoning": "Baseado na análise de custos, performance e escalabilidade"
  },
  "timestamp": "2025-07-25T10:00:00Z",
  "demo_mode": true
}
```

### Storage Analysis
```http
POST /api/analyze/storage
```

**Request Body:**
```json
{
  "aws_storage_type": "s3_standard",
  "gcp_storage_type": "standard",
  "aws_region": "us-east-1",
  "gcp_region": "us-central1",
  "storage_size_gb": 1000
}
```

**Response:**
```json
{
  "analysis_type": "storage_costs",
  "requirements": {
    "aws_storage_type": "s3_standard",
    "gcp_storage_type": "standard",
    "aws_region": "us-east-1",
    "gcp_region": "us-central1",
    "storage_size_gb": 1000
  },
  "result": {
    "recommendation": "GCP",
    "aws_cost_per_gb": 0.023,
    "gcp_cost_per_gb": 0.020,
    "savings": 13.0,
    "confidence": 92,
    "reasoning": "GCP oferece melhor custo-benefício para armazenamento"
  },
  "timestamp": "2025-07-25T10:00:00Z",
  "demo_mode": true
}
```

### Comprehensive Analysis
```http
POST /api/analyze/comprehensive
```

**Request Body:**
```json
{
  "aws_instance_type": "t3.medium",
  "gcp_machine_type": "e2-medium",
  "aws_region": "us-east-1",
  "gcp_region": "us-central1",
  "workload_type": "general",
  "aws_storage_type": "s3_standard",
  "gcp_storage_type": "standard",
  "storage_size_gb": 1000,
  "monthly_budget": 500,
  "performance_priority": "balanced",
  "time_horizon_months": 36
}
```

**Response:**
```json
{
  "analysis_type": "comprehensive",
  "requirements": { /* request body */ },
  "result": {
    "recommendation": "AWS",
    "total_monthly_cost_aws": 245.60,
    "total_monthly_cost_gcp": 298.40,
    "monthly_savings": 52.80,
    "annual_savings": 633.60,
    "tco_3_years": 1900.80,
    "confidence": 89,
    "breakdown": {
      "compute": {"aws": 156.80, "gcp": 204.30},
      "storage": {"aws": 23.00, "gcp": 20.00},
      "network": {"aws": 45.80, "gcp": 54.10},
      "additional": {"aws": 20.00, "gcp": 20.00}
    },
    "reasoning": "AWS oferece melhor custo-benefício geral considerando todos os fatores"
  },
  "timestamp": "2025-07-25T10:00:00Z",
  "demo_mode": true
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Dados JSON requeridos",
  "timestamp": "2025-07-25T10:00:00Z"
}
```

### 500 Internal Server Error
```json
{
  "error": "Erro interno do servidor",
  "timestamp": "2025-07-25T10:00:00Z"
}
```

### 503 Service Unavailable
```json
{
  "error": "Sistema CrewAI não disponível",
  "timestamp": "2025-07-25T10:00:00Z"
}
```

## Rate Limiting
Atualmente não há rate limiting na versão demo.

## CORS
A API suporta CORS para todas as origens na versão demo.

## Examples

### cURL Examples

**Health Check:**
```bash
curl -X GET https://y0h0i3cqn6yq.manus.space/api/health
```

**Compute Analysis:**
```bash
curl -X POST https://y0h0i3cqn6yq.manus.space/api/analyze/compute \
  -H "Content-Type: application/json" \
  -d '{
    "aws_instance_type": "t3.medium",
    "gcp_machine_type": "e2-medium",
    "aws_region": "us-east-1",
    "gcp_region": "us-central1",
    "workload_type": "general"
  }'
```

### JavaScript Examples

**Using Fetch:**
```javascript
// Health check
const health = await fetch('https://y0h0i3cqn6yq.manus.space/api/health');
const healthData = await health.json();

// Compute analysis
const analysis = await fetch('https://y0h0i3cqn6yq.manus.space/api/analyze/compute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    aws_instance_type: 't3.medium',
    gcp_machine_type: 'e2-medium',
    aws_region: 'us-east-1',
    gcp_region: 'us-central1',
    workload_type: 'general'
  })
});
const analysisData = await analysis.json();
```

### Python Examples

**Using Requests:**
```python
import requests

# Health check
response = requests.get('https://y0h0i3cqn6yq.manus.space/api/health')
health_data = response.json()

# Compute analysis
payload = {
    'aws_instance_type': 't3.medium',
    'gcp_machine_type': 'e2-medium',
    'aws_region': 'us-east-1',
    'gcp_region': 'us-central1',
    'workload_type': 'general'
}

response = requests.post(
    'https://y0h0i3cqn6yq.manus.space/api/analyze/compute',
    json=payload
)
analysis_data = response.json()
```

