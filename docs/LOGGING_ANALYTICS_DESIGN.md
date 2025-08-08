# Sistema de Logging e Analytics - Cloud Cost Agent
## Design Técnico Completo

### 📊 **Visão Geral**

O sistema de logging e analytics será implementado usando a stack completa do Google Cloud Platform para capturar, processar e analisar todas as interações dos agentes de IA, permitindo insights profundos sobre:

- Performance dos agentes
- Qualidade das recomendações
- Padrões de uso
- Otimizações de custo
- Tendências de mercado

### 🏗️ **Arquitetura Proposta**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agentes IA    │───▶│  Cloud Logging   │───▶│   BigQuery      │
│   (CrewAI)      │    │  (Structured)    │    │  (Analytics)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Event Stream   │    │   Pub/Sub        │    │   Data Studio   │
│  (Real-time)    │    │  (Processing)    │    │  (Dashboards)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 📋 **Componentes do Sistema**

#### **1. Cloud Logging (Stackdriver)**
- **Função**: Coleta centralizada de logs
- **Formato**: JSON estruturado
- **Retenção**: 30 dias (depois transfere para BigQuery)
- **Filtros**: Por agente, tipo de análise, severidade

#### **2. Cloud Pub/Sub**
- **Função**: Stream de eventos em tempo real
- **Tópicos**: 
  - `agent-analysis-events`
  - `cost-comparison-results`
  - `recommendation-feedback`
- **Subscribers**: BigQuery, alertas, dashboards

#### **3. BigQuery**
- **Função**: Data warehouse para análises
- **Datasets**: 
  - `agent_analytics`
  - `cost_comparisons`
  - `user_interactions`
- **Particionamento**: Por data e tipo de agente

#### **4. Cloud Functions**
- **Função**: Processamento de eventos
- **Triggers**: Pub/Sub messages
- **Processamento**: Enriquecimento de dados, validação

#### **5. Data Studio**
- **Função**: Dashboards e visualizações
- **Conexão**: Direta com BigQuery
- **Atualizações**: Tempo real

### 📊 **Schema de Dados BigQuery**

#### **Tabela: agent_executions**
```sql
CREATE TABLE `cloud_cost_agent.agent_analytics.agent_executions` (
  execution_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  agent_type STRING NOT NULL,  -- 'aws_specialist', 'gcp_specialist', etc.
  agent_name STRING NOT NULL,
  task_type STRING NOT NULL,   -- 'cost_analysis', 'sla_check', etc.
  input_parameters JSON,
  execution_duration_ms INT64,
  status STRING NOT NULL,      -- 'success', 'error', 'timeout'
  error_message STRING,
  memory_usage_mb FLOAT64,
  cpu_usage_percent FLOAT64,
  session_id STRING,
  user_id STRING,
  request_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY agent_type, status;
```

#### **Tabela: cost_comparisons**
```sql
CREATE TABLE `cloud_cost_agent.agent_analytics.cost_comparisons` (
  comparison_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  analysis_type STRING NOT NULL,  -- 'compute', 'storage', 'comprehensive'
  providers ARRAY<STRING>,        -- ['aws', 'gcp', 'azure']
  input_requirements JSON,
  aws_results JSON,
  gcp_results JSON,
  azure_results JSON,
  onpremise_results JSON,
  final_recommendation STRING,
  confidence_score FLOAT64,
  cost_savings_percentage FLOAT64,
  cost_savings_amount_usd FLOAT64,
  reasoning TEXT,
  execution_time_ms INT64,
  session_id STRING,
  user_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY analysis_type, final_recommendation;
```

#### **Tabela: agent_interactions**
```sql
CREATE TABLE `cloud_cost_agent.agent_analytics.agent_interactions` (
  interaction_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  source_agent STRING NOT NULL,
  target_agent STRING,
  interaction_type STRING NOT NULL,  -- 'request', 'response', 'collaboration'
  message_content JSON,
  response_time_ms INT64,
  success BOOLEAN,
  session_id STRING,
  correlation_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY source_agent, interaction_type;
```

#### **Tabela: mcp_server_calls**
```sql
CREATE TABLE `cloud_cost_agent.agent_analytics.mcp_server_calls` (
  call_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  server_type STRING NOT NULL,     -- 'aws_pricing', 'gcp_pricing', etc.
  method_name STRING NOT NULL,
  input_parameters JSON,
  response_data JSON,
  response_time_ms INT64,
  status_code INT64,
  error_message STRING,
  cache_hit BOOLEAN,
  api_cost_usd FLOAT64,
  agent_id STRING,
  session_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY server_type, status_code;
```

#### **Tabela: user_feedback**
```sql
CREATE TABLE `cloud_cost_agent.agent_analytics.user_feedback` (
  feedback_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  session_id STRING NOT NULL,
  comparison_id STRING,
  recommendation_followed BOOLEAN,
  actual_savings_usd FLOAT64,
  satisfaction_score INT64,       -- 1-5 scale
  feedback_text TEXT,
  improvement_suggestions TEXT,
  user_id STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY recommendation_followed, satisfaction_score;
```

### 🔧 **Implementação Técnica**

#### **1. Logger Centralizado**
```python
# cloud_cost_agent/logging/gcp_logger.py
import json
import time
from datetime import datetime
from google.cloud import logging as cloud_logging
from google.cloud import pubsub_v1
from google.cloud import bigquery
import uuid

class CloudCostLogger:
    def __init__(self):
        self.cloud_logging_client = cloud_logging.Client()
        self.cloud_logging_client.setup_logging()
        
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(
            'cloud-cost-agent-project', 
            'agent-analysis-events'
        )
        
        self.bigquery_client = bigquery.Client()
        self.dataset_id = 'agent_analytics'
        
    def log_agent_execution(self, agent_type, agent_name, task_type, 
                          input_params, duration_ms, status, 
                          error_msg=None, session_id=None, user_id=None):
        """Log execução de agente"""
        
        execution_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        log_data = {
            'execution_id': execution_id,
            'timestamp': timestamp.isoformat(),
            'agent_type': agent_type,
            'agent_name': agent_name,
            'task_type': task_type,
            'input_parameters': input_params,
            'execution_duration_ms': duration_ms,
            'status': status,
            'error_message': error_msg,
            'session_id': session_id,
            'user_id': user_id,
            'request_id': str(uuid.uuid4())
        }
        
        # Log estruturado no Cloud Logging
        logger = self.cloud_logging_client.logger('agent-executions')
        logger.log_struct(log_data, severity='INFO')
        
        # Enviar para Pub/Sub para processamento em tempo real
        message_data = json.dumps(log_data).encode('utf-8')
        future = self.publisher.publish(self.topic_path, message_data)
        
        return execution_id
    
    def log_cost_comparison(self, analysis_type, providers, input_reqs,
                          results_by_provider, recommendation, confidence,
                          savings_pct, savings_amount, reasoning,
                          execution_time, session_id, user_id):
        """Log comparação de custos"""
        
        comparison_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        log_data = {
            'comparison_id': comparison_id,
            'timestamp': timestamp.isoformat(),
            'analysis_type': analysis_type,
            'providers': providers,
            'input_requirements': input_reqs,
            'results_by_provider': results_by_provider,
            'final_recommendation': recommendation,
            'confidence_score': confidence,
            'cost_savings_percentage': savings_pct,
            'cost_savings_amount_usd': savings_amount,
            'reasoning': reasoning,
            'execution_time_ms': execution_time,
            'session_id': session_id,
            'user_id': user_id
        }
        
        # Log estruturado
        logger = self.cloud_logging_client.logger('cost-comparisons')
        logger.log_struct(log_data, severity='INFO')
        
        # Pub/Sub
        message_data = json.dumps(log_data).encode('utf-8')
        future = self.publisher.publish(self.topic_path, message_data)
        
        return comparison_id
    
    def log_agent_interaction(self, source_agent, target_agent, 
                            interaction_type, message_content,
                            response_time, success, session_id):
        """Log interação entre agentes"""
        
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        log_data = {
            'interaction_id': interaction_id,
            'timestamp': timestamp.isoformat(),
            'source_agent': source_agent,
            'target_agent': target_agent,
            'interaction_type': interaction_type,
            'message_content': message_content,
            'response_time_ms': response_time,
            'success': success,
            'session_id': session_id,
            'correlation_id': str(uuid.uuid4())
        }
        
        logger = self.cloud_logging_client.logger('agent-interactions')
        logger.log_struct(log_data, severity='INFO')
        
        return interaction_id
    
    def log_mcp_server_call(self, server_type, method_name, input_params,
                          response_data, response_time, status_code,
                          error_msg, cache_hit, api_cost, agent_id, session_id):
        """Log chamadas para servidores MCP"""
        
        call_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        log_data = {
            'call_id': call_id,
            'timestamp': timestamp.isoformat(),
            'server_type': server_type,
            'method_name': method_name,
            'input_parameters': input_params,
            'response_data': response_data,
            'response_time_ms': response_time,
            'status_code': status_code,
            'error_message': error_msg,
            'cache_hit': cache_hit,
            'api_cost_usd': api_cost,
            'agent_id': agent_id,
            'session_id': session_id
        }
        
        logger = self.cloud_logging_client.logger('mcp-server-calls')
        logger.log_struct(log_data, severity='INFO')
        
        return call_id
```

#### **2. Decorador para Instrumentação Automática**
```python
# cloud_cost_agent/logging/decorators.py
import time
import functools
from .gcp_logger import CloudCostLogger

logger = CloudCostLogger()

def log_agent_execution(agent_type, task_type):
    """Decorador para log automático de execução de agentes"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            agent_name = func.__name__
            session_id = kwargs.get('session_id')
            user_id = kwargs.get('user_id')
            
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.log_agent_execution(
                    agent_type=agent_type,
                    agent_name=agent_name,
                    task_type=task_type,
                    input_params=kwargs,
                    duration_ms=duration_ms,
                    status='success',
                    session_id=session_id,
                    user_id=user_id
                )
                
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.log_agent_execution(
                    agent_type=agent_type,
                    agent_name=agent_name,
                    task_type=task_type,
                    input_params=kwargs,
                    duration_ms=duration_ms,
                    status='error',
                    error_msg=str(e),
                    session_id=session_id,
                    user_id=user_id
                )
                
                raise
                
        return wrapper
    return decorator

def log_mcp_call(server_type):
    """Decorador para log de chamadas MCP"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            method_name = func.__name__
            
            try:
                result = func(*args, **kwargs)
                response_time = int((time.time() - start_time) * 1000)
                
                logger.log_mcp_server_call(
                    server_type=server_type,
                    method_name=method_name,
                    input_params=kwargs,
                    response_data=result,
                    response_time=response_time,
                    status_code=200,
                    error_msg=None,
                    cache_hit=False,  # Implementar lógica de cache
                    api_cost=0.0,     # Calcular custo real da API
                    agent_id=kwargs.get('agent_id'),
                    session_id=kwargs.get('session_id')
                )
                
                return result
                
            except Exception as e:
                response_time = int((time.time() - start_time) * 1000)
                
                logger.log_mcp_server_call(
                    server_type=server_type,
                    method_name=method_name,
                    input_params=kwargs,
                    response_data=None,
                    response_time=response_time,
                    status_code=500,
                    error_msg=str(e),
                    cache_hit=False,
                    api_cost=0.0,
                    agent_id=kwargs.get('agent_id'),
                    session_id=kwargs.get('session_id')
                )
                
                raise
                
        return wrapper
    return decorator
```

### 📈 **Queries de Análise BigQuery**

#### **1. Performance dos Agentes**
```sql
-- Análise de performance por agente
SELECT 
  agent_type,
  agent_name,
  COUNT(*) as total_executions,
  AVG(execution_duration_ms) as avg_duration_ms,
  PERCENTILE_CONT(execution_duration_ms, 0.95) OVER() as p95_duration_ms,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*) * 100 as success_rate,
  AVG(CASE WHEN status = 'success' THEN execution_duration_ms END) as avg_success_duration_ms
FROM `cloud_cost_agent.agent_analytics.agent_executions`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY agent_type, agent_name
ORDER BY total_executions DESC;
```

#### **2. Análise de Recomendações**
```sql
-- Efetividade das recomendações
SELECT 
  final_recommendation,
  analysis_type,
  COUNT(*) as total_recommendations,
  AVG(confidence_score) as avg_confidence,
  AVG(cost_savings_percentage) as avg_savings_pct,
  SUM(cost_savings_amount_usd) as total_savings_usd,
  AVG(execution_time_ms) as avg_execution_time
FROM `cloud_cost_agent.agent_analytics.cost_comparisons`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY final_recommendation, analysis_type
ORDER BY total_savings_usd DESC;
```

#### **3. Padrões de Uso**
```sql
-- Padrões de uso por hora do dia
SELECT 
  EXTRACT(HOUR FROM timestamp) as hour_of_day,
  COUNT(*) as total_analyses,
  COUNT(DISTINCT session_id) as unique_sessions,
  AVG(execution_time_ms) as avg_execution_time,
  SUM(cost_savings_amount_usd) as total_savings
FROM `cloud_cost_agent.agent_analytics.cost_comparisons`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY hour_of_day
ORDER BY hour_of_day;
```

### 🎯 **Métricas e KPIs**

#### **Métricas de Performance**
- **Latência média** por tipo de agente
- **Taxa de sucesso** das execuções
- **Throughput** (análises por minuto)
- **Utilização de recursos** (CPU, memória)

#### **Métricas de Negócio**
- **Economia total** gerada pelas recomendações
- **Taxa de adoção** das recomendações
- **Satisfação do usuário** (feedback)
- **Precisão das estimativas** vs. custos reais

#### **Métricas Operacionais**
- **Disponibilidade** do sistema
- **Tempo de resposta** das APIs
- **Custos de infraestrutura** vs. valor gerado
- **Utilização de cache** dos MCPs

### 💰 **Estimativa de Custos GCP**

#### **Cloud Logging**
- **Volume estimado**: 10GB/mês
- **Custo**: $0.50/GB = $5/mês

#### **BigQuery**
- **Storage**: 100GB/mês = $2/mês
- **Queries**: 1TB processado/mês = $5/mês

#### **Pub/Sub**
- **Mensagens**: 1M/mês = $0.40/mês

#### **Cloud Functions**
- **Invocações**: 100K/mês = $0.20/mês

#### **Data Studio**
- **Gratuito** para uso básico

**Total estimado**: ~$13/mês

### 🚀 **Benefícios Esperados**

#### **Insights de Negócio**
- Identificar padrões de economia por setor
- Otimizar algoritmos de recomendação
- Detectar tendências de mercado
- Melhorar precisão das estimativas

#### **Otimização Técnica**
- Identificar gargalos de performance
- Otimizar cache dos MCPs
- Balancear carga entre agentes
- Reduzir custos de API

#### **Experiência do Usuário**
- Personalizar recomendações
- Acelerar análises frequentes
- Melhorar interface baseada no uso
- Provar ROI das recomendações

