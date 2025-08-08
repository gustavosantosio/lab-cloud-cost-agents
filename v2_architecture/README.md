# Cloud Cost Agent v2 - Arquitetura Multi-Agentes Avançada

## 🏗️ Visão Geral da Arquitetura

Sistema completo de análise de custos de nuvem com arquitetura multi-agentes usando CrewAI, servidores MCP e Data Lake no BigQuery.

### 📊 Estrutura Hierárquica

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTE OPERACIONAL                       │
│                   (Gerente Master)                          │
│    Conecta: AWS, GCP, CrewAI, Looker, Prometheus, Grafana  │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼────┐    ┌──────▼──────┐    ┌─────▼─────┐
│ESPECIAL│    │COORDENADORES│    │    MCP    │
│ISTAS   │    │             │    │ SERVERS   │
└────────┘    └─────────────┘    └───────────┘
```

## 🤖 Agentes do Sistema

### 🎯 **Agente Operacional (1)**
- **Nome**: `MasterOperationalAgent`
- **Função**: Gerente de toda a cadeia de agentes
- **Conexões**: 
  - AWS (boto3, AWS CLI)
  - Google Cloud (gcloud SDK)
  - CrewAI (orquestração)
  - Looker (dashboards)
  - Prometheus (métricas)
  - Grafana (visualização)

### 👨‍💻 **Agentes Especialistas (2)**
1. **AWS Specialist Agent**
   - Especialista em serviços AWS
   - Análise de custos EC2, S3, RDS, etc.
   - Otimizações específicas AWS

2. **GCP Specialist Agent**
   - Especialista em serviços Google Cloud
   - Análise de custos Compute Engine, Cloud Storage, etc.
   - Otimizações específicas GCP

### 🎛️ **Agentes Coordenadores (5)**
1. **SLA Coordinator Agent**
   - Análise de SLAs por provedor
   - Monitoramento de uptime
   - Cálculo de penalidades

2. **Cost Coordinator Agent**
   - Coordenação de análises de custo
   - Comparações entre provedores
   - Otimizações de TCO

3. **Compliance Coordinator Agent**
   - Verificação de conformidade
   - Padrões de segurança
   - Certificações (ISO, SOC, etc.)

4. **Legal Coordinator Agent**
   - Normas brasileiras (LGPD, etc.)
   - Instruções normativas
   - Legislação aplicável
   - **Conecta ao RAG** com documentos PDF

5. **Report Generator Agent**
   - Geração de relatórios finais
   - Consolidação de análises
   - Recomendações finais

## 🔌 Servidores MCP (4)

### 1. **AWS MCP Server**
```python
# Conexão com APIs AWS
- AWS Cost Explorer API
- AWS Pricing API  
- AWS CloudWatch API
- AWS Trusted Advisor API
```

### 2. **GCP MCP Server**
```python
# Conexão com APIs Google Cloud
- Cloud Billing API
- Cloud Monitoring API
- Cloud Asset Inventory API
- Recommender API
```

### 3. **SLA Analysis MCP Server**
```python
# Análise de SLAs
- Uptime monitoring
- Performance metrics
- SLA compliance tracking
- Penalty calculations
```

### 4. **Legal RAG MCP Server**
```python
# Sistema RAG para documentos jurídicos
- PDF document processing
- Vector embeddings
- Semantic search
- Legal document retrieval
```

## 🏗️ Data Lake BigQuery

### Camadas de Dados

#### 📥 **RAW Layer**
```sql
-- Dados brutos de logs
dataset: cloud_cost_agent_raw
tables:
  - raw_agent_logs
  - raw_api_calls  
  - raw_user_interactions
  - raw_system_metrics
```

#### 🧹 **TRUSTED Layer**
```sql
-- Dados limpos e estruturados
dataset: cloud_cost_agent_trusted
tables:
  - trusted_agent_executions
  - trusted_cost_analyses
  - trusted_sla_metrics
  - trusted_compliance_checks
```

#### 📊 **REFINED Layer**
```sql
-- Dados prontos para análise
dataset: cloud_cost_agent_refined
tables:
  - refined_cost_comparisons
  - refined_recommendations
  - refined_performance_metrics
  - refined_business_insights
```

## 🗂️ Estrutura de Diretórios (Windows)

```
cloud-cost-agent-v2\
├── agents\
│   ├── operational\
│   │   └── master_operational_agent.py
│   ├── specialists\
│   │   ├── aws_specialist_agent.py
│   │   └── gcp_specialist_agent.py
│   └── coordinators\
│       ├── sla_coordinator_agent.py
│       ├── cost_coordinator_agent.py
│       ├── compliance_coordinator_agent.py
│       ├── legal_coordinator_agent.py
│       └── report_generator_agent.py
├── mcp_servers\
│   ├── aws_mcp_server.py
│   ├── gcp_mcp_server.py
│   ├── sla_analysis_mcp_server.py
│   └── legal_rag_mcp_server.py
├── data_lake\
│   ├── schemas\
│   │   ├── raw_schemas.sql
│   │   ├── trusted_schemas.sql
│   │   └── refined_schemas.sql
│   ├── etl\
│   │   ├── raw_to_trusted.py
│   │   └── trusted_to_refined.py
│   └── setup\
│       └── create_datasets.sql
├── rag_system\
│   ├── document_processor.py
│   ├── vector_store.py
│   ├── embeddings_manager.py
│   └── legal_documents\
│       └── pdfs\
├── orchestration\
│   ├── crew_orchestrator.py
│   ├── workflow_manager.py
│   └── task_scheduler.py
├── config\
│   ├── settings.py
│   ├── credentials.json
│   └── environment.env
├── scripts\
│   ├── setup.bat
│   ├── run.bat
│   └── deploy.ps1
├── tests\
│   ├── test_agents.py
│   ├── test_mcp_servers.py
│   └── test_integration.py
├── docs\
│   ├── architecture.md
│   ├── api_reference.md
│   └── deployment_guide.md
├── requirements.txt
└── README.md
```

## 🔄 Fluxo de Operação

### 1. **Inicialização**
```
Master Operational Agent
    ↓
Inicializa todos os MCPs
    ↓
Configura conexões (AWS, GCP, etc.)
    ↓
Ativa agentes especialistas e coordenadores
```

### 2. **Análise**
```
Especialistas coletam dados
    ↓
Coordenadores processam informações
    ↓
Legal Agent consulta RAG
    ↓
Dados são logados no BigQuery (RAW)
```

### 3. **Processamento**
```
ETL: RAW → TRUSTED
    ↓
ETL: TRUSTED → REFINED
    ↓
Report Generator consolida resultados
    ↓
Master Agent entrega relatório final
```

## 🛠️ Tecnologias Utilizadas

### **Core**
- **CrewAI**: Orquestração de agentes
- **Python 3.11+**: Linguagem principal
- **MCP (Model Context Protocol)**: Comunicação entre agentes

### **Cloud & APIs**
- **Google Cloud BigQuery**: Data Lake
- **AWS APIs**: Cost Explorer, Pricing
- **GCP APIs**: Cloud Billing, Monitoring
- **Looker**: Dashboards
- **Prometheus/Grafana**: Monitoramento

### **AI & ML**
- **OpenAI GPT-4**: LLM principal
- **LangChain**: Framework para RAG
- **ChromaDB**: Vector database para RAG
- **Sentence Transformers**: Embeddings

### **Windows Specific**
- **PowerShell**: Scripts de automação
- **Windows Task Scheduler**: Agendamento
- **IIS**: Web server (opcional)
- **Windows Services**: Background processes

## 🚀 Instalação (Windows)

### **Pré-requisitos**
```powershell
# Python 3.11+
winget install Python.Python.3.11

# Git
winget install Git.Git

# Google Cloud SDK
winget install Google.CloudSDK

# AWS CLI
winget install Amazon.AWSCLI
```

### **Setup do Projeto**
```powershell
# Clone do repositório
git clone https://github.com/your-org/cloud-cost-agent-v2.git
cd cloud-cost-agent-v2

# Executar setup
.\scripts\setup.bat
```

## 📊 Métricas e KPIs

### **Performance**
- Tempo de resposta por agente
- Taxa de sucesso das análises
- Throughput de processamento
- Utilização de recursos

### **Negócio**
- Economia total identificada
- Precisão das recomendações
- Satisfação do usuário
- ROI das otimizações

### **Técnicas**
- Disponibilidade do sistema
- Latência das APIs
- Qualidade dos dados
- Cobertura de testes

## 🔐 Segurança

### **Autenticação**
- Service accounts para GCP
- IAM roles para AWS
- API keys criptografadas
- OAuth 2.0 para usuários

### **Dados**
- Criptografia em trânsito (TLS)
- Criptografia em repouso (BigQuery)
- Logs auditáveis
- Compliance LGPD

## 📈 Roadmap

### **Fase 1** (Atual)
- ✅ Arquitetura base
- ✅ Agentes principais
- ✅ MCPs básicos
- ✅ Data Lake

### **Fase 2** (Próxima)
- 🔄 RAG system completo
- 🔄 Dashboard Looker
- 🔄 Alertas Prometheus
- 🔄 Testes automatizados

### **Fase 3** (Futuro)
- 📋 Multi-cloud (Azure)
- 📋 ML predictions
- 📋 Auto-optimization
- 📋 Mobile app

---

**Versão**: 2.0  
**Data**: Janeiro 2025  
**Plataforma**: Windows 10/11  
**Status**: Em desenvolvimento

