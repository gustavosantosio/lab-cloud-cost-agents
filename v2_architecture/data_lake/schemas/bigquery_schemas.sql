-- Cloud Cost Agent v2 - BigQuery Data Lake Schemas
-- Camadas: RAW → TRUSTED → REFINED

-- ============================================================================
-- RAW LAYER - Dados brutos de logs
-- ============================================================================

-- Dataset RAW
CREATE SCHEMA IF NOT EXISTS `cloud_cost_agent_raw`
OPTIONS (
  description = "Raw data layer - Dados brutos de logs e eventos",
  location = "US"
);

-- Tabela: raw_agent_logs
CREATE OR REPLACE TABLE `cloud_cost_agent_raw.raw_agent_logs` (
  log_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  agent_type STRING NOT NULL,
  agent_name STRING NOT NULL,
  log_level STRING NOT NULL,
  message STRING,
  raw_data JSON,
  session_id STRING,
  user_id STRING,
  source_system STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY agent_type, log_level
OPTIONS (
  description = "Logs brutos de todos os agentes do sistema",
  partition_expiration_days = 90
);

-- Tabela: raw_api_calls
CREATE OR REPLACE TABLE `cloud_cost_agent_raw.raw_api_calls` (
  call_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  mcp_server STRING NOT NULL,
  api_endpoint STRING NOT NULL,
  http_method STRING NOT NULL,
  request_headers JSON,
  request_body JSON,
  response_status INT64,
  response_headers JSON,
  response_body JSON,
  response_time_ms INT64,
  error_message STRING,
  agent_id STRING,
  session_id STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY mcp_server, response_status
OPTIONS (
  description = "Chamadas brutas para APIs externas via MCP servers",
  partition_expiration_days = 90
);

-- Tabela: raw_user_interactions
CREATE OR REPLACE TABLE `cloud_cost_agent_raw.raw_user_interactions` (
  interaction_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  user_id STRING,
  session_id STRING NOT NULL,
  interaction_type STRING NOT NULL,
  request_data JSON,
  response_data JSON,
  user_agent STRING,
  ip_address STRING,
  duration_ms INT64,
  status STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY interaction_type, status
OPTIONS (
  description = "Interações brutas dos usuários com o sistema",
  partition_expiration_days = 365
);

-- Tabela: raw_system_metrics
CREATE OR REPLACE TABLE `cloud_cost_agent_raw.raw_system_metrics` (
  metric_id STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  metric_name STRING NOT NULL,
  metric_value FLOAT64,
  metric_unit STRING,
  tags JSON,
  source_component STRING,
  environment STRING,
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY metric_name, source_component
OPTIONS (
  description = "Métricas brutas do sistema (CPU, memória, latência, etc.)",
  partition_expiration_days = 30
);

-- ============================================================================
-- TRUSTED LAYER - Dados limpos e estruturados
-- ============================================================================

-- Dataset TRUSTED
CREATE SCHEMA IF NOT EXISTS `cloud_cost_agent_trusted`
OPTIONS (
  description = "Trusted data layer - Dados limpos e estruturados",
  location = "US"
);

-- Tabela: trusted_agent_executions
CREATE OR REPLACE TABLE `cloud_cost_agent_trusted.trusted_agent_executions` (
  execution_id STRING NOT NULL,
  execution_timestamp TIMESTAMP NOT NULL,
  agent_type STRING NOT NULL,
  agent_name STRING NOT NULL,
  task_type STRING NOT NULL,
  input_parameters JSON,
  output_results JSON,
  execution_duration_ms INT64,
  status STRING NOT NULL,
  error_details JSON,
  performance_metrics STRUCT<
    cpu_usage_percent FLOAT64,
    memory_usage_mb FLOAT64,
    network_io_kb FLOAT64,
    disk_io_kb FLOAT64
  >,
  session_id STRING,
  user_id STRING,
  parent_execution_id STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(execution_timestamp)
CLUSTER BY agent_type, status, task_type
OPTIONS (
  description = "Execuções limpas e estruturadas dos agentes",
  partition_expiration_days = 365
);

-- Tabela: trusted_cost_analyses
CREATE OR REPLACE TABLE `cloud_cost_agent_trusted.trusted_cost_analyses` (
  analysis_id STRING NOT NULL,
  analysis_timestamp TIMESTAMP NOT NULL,
  analysis_type STRING NOT NULL,
  cloud_providers ARRAY<STRING>,
  input_requirements STRUCT<
    compute_requirements JSON,
    storage_requirements JSON,
    network_requirements JSON,
    compliance_requirements JSON,
    budget_constraints JSON
  >,
  provider_results ARRAY<STRUCT<
    provider STRING,
    monthly_cost_usd FLOAT64,
    annual_cost_usd FLOAT64,
    performance_score FLOAT64,
    reliability_score FLOAT64,
    compliance_score FLOAT64,
    detailed_breakdown JSON
  >>,
  recommendation STRUCT<
    recommended_provider STRING,
    confidence_score FLOAT64,
    cost_savings_usd FLOAT64,
    cost_savings_percentage FLOAT64,
    reasoning TEXT,
    risk_factors ARRAY<STRING>
  >,
  execution_metadata STRUCT<
    total_execution_time_ms INT64,
    agents_involved ARRAY<STRING>,
    api_calls_made INT64,
    data_sources_used ARRAY<STRING>
  >,
  session_id STRING,
  user_id STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(analysis_timestamp)
CLUSTER BY analysis_type, recommendation.recommended_provider
OPTIONS (
  description = "Análises de custo estruturadas e validadas",
  partition_expiration_days = 1095  -- 3 anos
);

-- Tabela: trusted_sla_metrics
CREATE OR REPLACE TABLE `cloud_cost_agent_trusted.trusted_sla_metrics` (
  sla_metric_id STRING NOT NULL,
  measurement_timestamp TIMESTAMP NOT NULL,
  cloud_provider STRING NOT NULL,
  service_name STRING NOT NULL,
  region STRING NOT NULL,
  sla_type STRING NOT NULL,  -- 'uptime', 'performance', 'support'
  sla_target_percentage FLOAT64,
  actual_percentage FLOAT64,
  measurement_period_hours INT64,
  incidents ARRAY<STRUCT<
    incident_id STRING,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    severity STRING,
    impact_description TEXT
  >>,
  penalty_amount_usd FLOAT64,
  credits_earned_usd FLOAT64,
  compliance_status STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(measurement_timestamp)
CLUSTER BY cloud_provider, sla_type, compliance_status
OPTIONS (
  description = "Métricas de SLA estruturadas por provedor e serviço",
  partition_expiration_days = 1095  -- 3 anos
);

-- Tabela: trusted_compliance_checks
CREATE OR REPLACE TABLE `cloud_cost_agent_trusted.trusted_compliance_checks` (
  compliance_check_id STRING NOT NULL,
  check_timestamp TIMESTAMP NOT NULL,
  cloud_provider STRING NOT NULL,
  service_name STRING NOT NULL,
  compliance_framework STRING NOT NULL,  -- 'LGPD', 'SOC2', 'ISO27001', etc.
  check_category STRING NOT NULL,
  check_name STRING NOT NULL,
  check_description TEXT,
  status STRING NOT NULL,  -- 'COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'NOT_APPLICABLE'
  severity STRING,  -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
  findings ARRAY<STRUCT<
    finding_id STRING,
    description TEXT,
    recommendation TEXT,
    remediation_effort STRING
  >>,
  evidence JSON,
  assessor_agent STRING,
  session_id STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(check_timestamp)
CLUSTER BY compliance_framework, status, severity
OPTIONS (
  description = "Verificações de compliance estruturadas",
  partition_expiration_days = 2555  -- 7 anos (requisito legal)
);

-- Tabela: trusted_legal_analyses
CREATE OR REPLACE TABLE `cloud_cost_agent_trusted.trusted_legal_analyses` (
  legal_analysis_id STRING NOT NULL,
  analysis_timestamp TIMESTAMP NOT NULL,
  analysis_type STRING NOT NULL,  -- 'LGPD', 'CONTRACT', 'REGULATION', 'POLICY'
  cloud_provider STRING NOT NULL,
  service_name STRING,
  legal_question TEXT NOT NULL,
  relevant_documents ARRAY<STRUCT<
    document_id STRING,
    document_name STRING,
    document_type STRING,
    relevance_score FLOAT64,
    key_excerpts ARRAY<STRING>
  >>,
  legal_opinion STRUCT<
    conclusion TEXT,
    risk_level STRING,
    recommendations ARRAY<STRING>,
    legal_basis ARRAY<STRING>,
    confidence_score FLOAT64
  >,
  regulatory_references ARRAY<STRUCT<
    regulation_name STRING,
    article_section STRING,
    description TEXT,
    compliance_requirement TEXT
  >>,
  assessor_agent STRING,
  session_id STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(analysis_timestamp)
CLUSTER BY analysis_type, legal_opinion.risk_level
OPTIONS (
  description = "Análises jurídicas estruturadas com base em documentos",
  partition_expiration_days = 2555  -- 7 anos (requisito legal)
);

-- ============================================================================
-- REFINED LAYER - Dados prontos para análise e dashboards
-- ============================================================================

-- Dataset REFINED
CREATE SCHEMA IF NOT EXISTS `cloud_cost_agent_refined`
OPTIONS (
  description = "Refined data layer - Dados prontos para análise e BI",
  location = "US"
);

-- Tabela: refined_cost_comparisons
CREATE OR REPLACE TABLE `cloud_cost_agent_refined.refined_cost_comparisons` (
  comparison_id STRING NOT NULL,
  analysis_date DATE NOT NULL,
  analysis_month STRING NOT NULL,  -- YYYY-MM
  analysis_quarter STRING NOT NULL,  -- YYYY-Q1
  workload_category STRING NOT NULL,
  workload_size STRING NOT NULL,  -- 'SMALL', 'MEDIUM', 'LARGE', 'ENTERPRISE'
  
  -- Custos por provedor
  aws_monthly_cost_usd FLOAT64,
  gcp_monthly_cost_usd FLOAT64,
  azure_monthly_cost_usd FLOAT64,
  onpremise_monthly_cost_usd FLOAT64,
  
  -- Scores normalizados (0-100)
  aws_total_score FLOAT64,
  gcp_total_score FLOAT64,
  azure_total_score FLOAT64,
  onpremise_total_score FLOAT64,
  
  -- Recomendação final
  recommended_provider STRING NOT NULL,
  confidence_level STRING NOT NULL,  -- 'LOW', 'MEDIUM', 'HIGH'
  potential_savings_usd FLOAT64,
  potential_savings_percentage FLOAT64,
  
  -- Fatores de decisão
  cost_weight_percentage FLOAT64,
  performance_weight_percentage FLOAT64,
  compliance_weight_percentage FLOAT64,
  sla_weight_percentage FLOAT64,
  
  -- Métricas de qualidade
  analysis_completeness_percentage FLOAT64,
  data_freshness_hours FLOAT64,
  
  -- Metadados
  total_analyses_count INT64,
  unique_users_count INT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY analysis_date
CLUSTER BY workload_category, recommended_provider
OPTIONS (
  description = "Comparações de custo agregadas e prontas para dashboards",
  partition_expiration_days = 1095  -- 3 anos
);

-- Tabela: refined_recommendations
CREATE OR REPLACE TABLE `cloud_cost_agent_refined.refined_recommendations` (
  recommendation_id STRING NOT NULL,
  recommendation_date DATE NOT NULL,
  recommendation_type STRING NOT NULL,  -- 'COST_OPTIMIZATION', 'MIGRATION', 'SCALING'
  priority STRING NOT NULL,  -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
  
  -- Contexto
  target_workload STRING NOT NULL,
  current_provider STRING,
  recommended_provider STRING,
  
  -- Impacto financeiro
  current_monthly_cost_usd FLOAT64,
  projected_monthly_cost_usd FLOAT64,
  monthly_savings_usd FLOAT64,
  annual_savings_usd FLOAT64,
  implementation_cost_usd FLOAT64,
  payback_period_months FLOAT64,
  
  -- Impacto operacional
  migration_complexity STRING,  -- 'LOW', 'MEDIUM', 'HIGH'
  estimated_downtime_hours FLOAT64,
  risk_level STRING,  -- 'LOW', 'MEDIUM', 'HIGH'
  
  -- Detalhes da recomendação
  recommendation_summary TEXT,
  implementation_steps ARRAY<STRING>,
  success_criteria ARRAY<STRING>,
  potential_risks ARRAY<STRING>,
  
  -- Status de implementação
  implementation_status STRING,  -- 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'REJECTED'
  implementation_date DATE,
  actual_savings_usd FLOAT64,
  
  -- Metadados
  generated_by_agent STRING,
  approved_by_user STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY recommendation_date
CLUSTER BY priority, implementation_status
OPTIONS (
  description = "Recomendações refinadas com tracking de implementação",
  partition_expiration_days = 1095  -- 3 anos
);

-- Tabela: refined_performance_metrics
CREATE OR REPLACE TABLE `cloud_cost_agent_refined.refined_performance_metrics` (
  metric_date DATE NOT NULL,
  metric_hour INT64 NOT NULL,  -- 0-23
  
  -- Métricas do sistema
  total_analyses_completed INT64,
  avg_analysis_duration_seconds FLOAT64,
  success_rate_percentage FLOAT64,
  error_rate_percentage FLOAT64,
  
  -- Métricas por agente
  operational_agent_executions INT64,
  specialist_agent_executions INT64,
  coordinator_agent_executions INT64,
  
  -- Métricas de MCP
  total_api_calls INT64,
  avg_api_response_time_ms FLOAT64,
  api_error_rate_percentage FLOAT64,
  cache_hit_rate_percentage FLOAT64,
  
  -- Métricas de usuário
  unique_users INT64,
  total_sessions INT64,
  avg_session_duration_minutes FLOAT64,
  user_satisfaction_score FLOAT64,
  
  -- Métricas de negócio
  total_savings_identified_usd FLOAT64,
  recommendations_generated INT64,
  recommendations_implemented INT64,
  implementation_success_rate_percentage FLOAT64,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY metric_date
CLUSTER BY metric_date, metric_hour
OPTIONS (
  description = "Métricas de performance agregadas por hora",
  partition_expiration_days = 365
);

-- Tabela: refined_business_insights
CREATE OR REPLACE TABLE `cloud_cost_agent_refined.refined_business_insights` (
  insight_id STRING NOT NULL,
  insight_date DATE NOT NULL,
  insight_category STRING NOT NULL,  -- 'COST_TREND', 'PROVIDER_COMPARISON', 'OPTIMIZATION_OPPORTUNITY'
  insight_type STRING NOT NULL,
  
  -- Conteúdo do insight
  insight_title STRING NOT NULL,
  insight_description TEXT NOT NULL,
  insight_impact STRING NOT NULL,  -- 'LOW', 'MEDIUM', 'HIGH'
  
  -- Dados de suporte
  supporting_data JSON,
  trend_data ARRAY<STRUCT<
    period STRING,
    value FLOAT64,
    change_percentage FLOAT64
  >>,
  
  -- Recomendações
  recommended_actions ARRAY<STRING>,
  estimated_impact_usd FLOAT64,
  confidence_score FLOAT64,
  
  -- Metadados
  generated_by_model STRING,
  data_sources ARRAY<STRING>,
  freshness_score FLOAT64,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY insight_date
CLUSTER BY insight_category, insight_impact
OPTIONS (
  description = "Insights de negócio gerados automaticamente",
  partition_expiration_days = 1095  -- 3 anos
);

-- ============================================================================
-- VIEWS PARA ANÁLISE
-- ============================================================================

-- View: Resumo diário de atividades
CREATE OR REPLACE VIEW `cloud_cost_agent_refined.daily_activity_summary` AS
SELECT 
  DATE(execution_timestamp) as activity_date,
  agent_type,
  COUNT(*) as total_executions,
  COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as successful_executions,
  AVG(execution_duration_ms) as avg_duration_ms,
  SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as error_count
FROM `cloud_cost_agent_trusted.trusted_agent_executions`
WHERE execution_timestamp >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY activity_date, agent_type
ORDER BY activity_date DESC, total_executions DESC;

-- View: Top recomendações por economia
CREATE OR REPLACE VIEW `cloud_cost_agent_refined.top_savings_opportunities` AS
SELECT 
  recommendation_type,
  target_workload,
  current_provider,
  recommended_provider,
  SUM(monthly_savings_usd) as total_monthly_savings,
  COUNT(*) as recommendation_count,
  AVG(confidence_score) as avg_confidence
FROM `cloud_cost_agent_refined.refined_recommendations`
WHERE implementation_status = 'PENDING'
  AND recommendation_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY 1,2,3,4
HAVING total_monthly_savings > 100
ORDER BY total_monthly_savings DESC
LIMIT 20;

-- View: Compliance status por provedor
CREATE OR REPLACE VIEW `cloud_cost_agent_refined.compliance_status_summary` AS
SELECT 
  cloud_provider,
  compliance_framework,
  COUNT(*) as total_checks,
  COUNT(CASE WHEN status = 'COMPLIANT' THEN 1 END) as compliant_checks,
  COUNT(CASE WHEN status = 'NON_COMPLIANT' THEN 1 END) as non_compliant_checks,
  ROUND(COUNT(CASE WHEN status = 'COMPLIANT' THEN 1 END) * 100.0 / COUNT(*), 2) as compliance_percentage
FROM `cloud_cost_agent_trusted.trusted_compliance_checks`
WHERE check_timestamp >= DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY cloud_provider, compliance_framework
ORDER BY compliance_percentage DESC;

