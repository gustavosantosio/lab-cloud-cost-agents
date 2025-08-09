"""
Pipeline de Dados para ETL entre camadas do Data Lake
Processa dados de RAW → TRUSTED → REFINED
"""
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth import default

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.project_config import config
from agents.base.logger import AgentLogger

class DataPipeline:
    """
    Pipeline de dados para processamento ETL entre camadas
    """
    
    def __init__(self):
        self.logger = AgentLogger("DataPipeline")
        self.client = None
        self.project_id = config.gcp.project_id
        self.dataset_raw = "cloud_agents_raw"
        self.dataset_trusted = "cloud_agents_trusted"
        self.dataset_refined = "cloud_agents_refined"
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa cliente BigQuery"""
        try:
            if config.gcp.credentials_path and os.path.exists(config.gcp.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    config.gcp.credentials_path
                )
            else:
                credentials, _ = default()
            
            self.client = bigquery.Client(
                credentials=credentials,
                project=self.project_id
            )
            
            self.logger.info("Cliente BigQuery inicializado para pipeline")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar BigQuery: {str(e)}")
            self.client = None
    
    def process_raw_to_trusted(self, processing_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa dados de RAW para TRUSTED
        
        Args:
            processing_date: Data para processamento (YYYY-MM-DD), padrão é ontem
        """
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            # Data de processamento
            if not processing_date:
                processing_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            self.logger.info(f"Iniciando processamento RAW → TRUSTED para {processing_date}")
            
            # Queries de transformação
            transformation_queries = {
                "agent_performance": f"""
                INSERT INTO `{self.project_id}.{self.dataset_trusted}.agent_performance`
                SELECT
                    DATE(timestamp) as date,
                    agent_name,
                    agent_type,
                    COUNT(*) as total_executions,
                    COUNTIF(log_level != 'ERROR') as successful_executions,
                    COUNTIF(log_level = 'ERROR') as failed_executions,
                    AVG(COALESCE(execution_time_ms, 0)) as avg_execution_time_ms,
                    MAX(COALESCE(execution_time_ms, 0)) as max_execution_time_ms,
                    MIN(COALESCE(execution_time_ms, 0)) as min_execution_time_ms,
                    SAFE_DIVIDE(COUNTIF(log_level = 'ERROR'), COUNT(*)) as error_rate
                FROM `{self.project_id}.{self.dataset_raw}.agent_logs`
                WHERE DATE(timestamp) = '{processing_date}'
                GROUP BY DATE(timestamp), agent_name, agent_type
                """,
                
                "cost_analysis_clean": f"""
                INSERT INTO `{self.project_id}.{self.dataset_trusted}.cost_analysis_clean`
                SELECT
                    DATE(timestamp) as date,
                    provider,
                    CASE 
                        WHEN service IN ('EC2', 'Compute Engine') THEN 'Compute'
                        WHEN service IN ('S3', 'Cloud Storage') THEN 'Storage'
                        WHEN service IN ('RDS', 'Cloud SQL') THEN 'Database'
                        ELSE 'Other'
                    END as service_category,
                    service as service_name,
                    COALESCE(region, 'global') as region,
                    CAST(JSON_EXTRACT_SCALAR(cost_data, '$.amount') AS NUMERIC) as cost_usd,
                    CAST(JSON_EXTRACT_SCALAR(usage_data, '$.quantity') AS NUMERIC) as usage_quantity,
                    JSON_EXTRACT_SCALAR(usage_data, '$.unit') as usage_unit,
                    1 as resource_count,
                    COALESCE(account_id, 'unknown') as account_id
                FROM `{self.project_id}.{self.dataset_raw}.cost_analysis_raw`
                WHERE DATE(timestamp) = '{processing_date}'
                    AND JSON_EXTRACT_SCALAR(cost_data, '$.amount') IS NOT NULL
                """,
                
                "sla_performance": f"""
                INSERT INTO `{self.project_id}.{self.dataset_trusted}.sla_performance`
                SELECT
                    DATE(timestamp) as date,
                    provider,
                    service,
                    COALESCE(region, 'global') as region,
                    AVG(CASE WHEN metric_type = 'availability' THEN metric_value END) as availability_percentage,
                    SUM(CASE WHEN metric_type = 'downtime' THEN metric_value END) as downtime_minutes,
                    COUNT(DISTINCT incident_id) as incident_count,
                    99.9 as sla_target, -- SLA padrão
                    AVG(CASE WHEN metric_type = 'availability' THEN metric_value END) < 99.9 as sla_breach,
                    LEAST(100, AVG(CASE WHEN metric_type = 'availability' THEN metric_value END)) as performance_score
                FROM `{self.project_id}.{self.dataset_raw}.sla_metrics_raw`
                WHERE DATE(timestamp) = '{processing_date}'
                GROUP BY DATE(timestamp), provider, service, region
                """,
                
                "compliance_status": f"""
                INSERT INTO `{self.project_id}.{self.dataset_trusted}.compliance_status`
                SELECT
                    DATE(timestamp) as date,
                    provider,
                    framework,
                    CASE 
                        WHEN control_id LIKE '%ACCESS%' THEN 'Access Control'
                        WHEN control_id LIKE '%ENCRYPT%' THEN 'Encryption'
                        WHEN control_id LIKE '%AUDIT%' THEN 'Auditing'
                        ELSE 'General'
                    END as control_category,
                    COUNT(*) as total_checks,
                    COUNTIF(check_result = 'PASS') as passed_checks,
                    COUNTIF(check_result = 'FAIL') as failed_checks,
                    COUNTIF(check_result = 'FAIL' AND severity = 'CRITICAL') as critical_failures,
                    SAFE_DIVIDE(COUNTIF(check_result = 'PASS'), COUNT(*)) * 100 as compliance_percentage,
                    CASE 
                        WHEN COUNTIF(check_result = 'FAIL' AND severity = 'CRITICAL') > 0 THEN 90
                        WHEN COUNTIF(check_result = 'FAIL' AND severity = 'HIGH') > 0 THEN 70
                        WHEN COUNTIF(check_result = 'FAIL') > 0 THEN 50
                        ELSE 10
                    END as risk_score
                FROM `{self.project_id}.{self.dataset_raw}.compliance_checks_raw`
                WHERE DATE(timestamp) = '{processing_date}'
                GROUP BY DATE(timestamp), provider, framework, control_category
                """
            }
            
            # Executar transformações
            results = {}
            for table_name, query in transformation_queries.items():
                try:
                    # Deletar dados existentes para a data
                    delete_query = f"""
                    DELETE FROM `{self.project_id}.{self.dataset_trusted}.{table_name}`
                    WHERE date = '{processing_date}'
                    """
                    
                    delete_job = self.client.query(delete_query)
                    delete_job.result()
                    
                    # Inserir novos dados
                    job = self.client.query(query)
                    job.result()
                    
                    self.logger.info(f"Tabela {table_name} processada", {
                        "rows_affected": job.num_dml_affected_rows,
                        "processing_date": processing_date
                    })
                    
                    results[table_name] = {
                        "status": "success",
                        "rows_processed": job.num_dml_affected_rows
                    }
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar {table_name}: {str(e)}")
                    results[table_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "processing_date": processing_date,
                "layer_transition": "RAW → TRUSTED",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro no processamento RAW → TRUSTED: {str(e)}")
            return {"error": str(e)}
    
    def process_trusted_to_refined(self, processing_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa dados de TRUSTED para REFINED
        
        Args:
            processing_date: Data para processamento (YYYY-MM-DD), padrão é ontem
        """
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            # Data de processamento
            if not processing_date:
                processing_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            self.logger.info(f"Iniciando processamento TRUSTED → REFINED para {processing_date}")
            
            # Queries de agregação e insights
            aggregation_queries = {
                "cost_optimization_insights": f"""
                INSERT INTO `{self.project_id}.{self.dataset_refined}.cost_optimization_insights`
                WITH cost_analysis AS (
                    SELECT 
                        provider,
                        service_category,
                        SUM(cost_usd) as total_cost,
                        COUNT(*) as resource_count
                    FROM `{self.project_id}.{self.dataset_trusted}.cost_analysis_clean`
                    WHERE date = '{processing_date}'
                    GROUP BY provider, service_category
                ),
                optimization_opportunities AS (
                    SELECT 
                        provider,
                        service_category,
                        total_cost,
                        CASE 
                            WHEN service_category = 'Compute' THEN total_cost * 0.3
                            WHEN service_category = 'Storage' THEN total_cost * 0.2
                            ELSE total_cost * 0.15
                        END as potential_savings,
                        CASE 
                            WHEN service_category = 'Compute' THEN 'Reserved Instances'
                            WHEN service_category = 'Storage' THEN 'Storage Class Optimization'
                            ELSE 'General Optimization'
                        END as optimization_type
                    FROM cost_analysis
                    WHERE total_cost > 100 -- Apenas custos significativos
                )
                SELECT
                    '{processing_date}' as analysis_date,
                    provider,
                    optimization_type,
                    total_cost as current_cost_usd,
                    potential_savings as potential_savings_usd,
                    SAFE_DIVIDE(potential_savings, total_cost) * 100 as savings_percentage,
                    CASE 
                        WHEN potential_savings > 1000 THEN 'High'
                        WHEN potential_savings > 500 THEN 'Medium'
                        ELSE 'Low'
                    END as implementation_effort,
                    CASE 
                        WHEN potential_savings > 0 THEN CAST(total_cost / (potential_savings * 12) AS INT64)
                        ELSE NULL
                    END as roi_months,
                    CONCAT('Optimize ', service_category, ' resources for ', provider) as recommendation,
                    potential_savings / 100 as priority_score
                FROM optimization_opportunities
                """,
                
                "provider_comparison": f"""
                INSERT INTO `{self.project_id}.{self.dataset_refined}.provider_comparison`
                WITH cost_by_provider AS (
                    SELECT 
                        service_category,
                        SUM(CASE WHEN provider = 'aws' THEN cost_usd END) as aws_cost,
                        SUM(CASE WHEN provider = 'gcp' THEN cost_usd END) as gcp_cost
                    FROM `{self.project_id}.{self.dataset_trusted}.cost_analysis_clean`
                    WHERE date = '{processing_date}'
                    GROUP BY service_category
                ),
                sla_by_provider AS (
                    SELECT 
                        service,
                        AVG(CASE WHEN provider = 'aws' THEN performance_score END) as aws_sla,
                        AVG(CASE WHEN provider = 'gcp' THEN performance_score END) as gcp_sla
                    FROM `{self.project_id}.{self.dataset_trusted}.sla_performance`
                    WHERE date = '{processing_date}'
                    GROUP BY service
                ),
                compliance_by_provider AS (
                    SELECT 
                        framework,
                        AVG(CASE WHEN provider = 'aws' THEN compliance_percentage END) as aws_compliance,
                        AVG(CASE WHEN provider = 'gcp' THEN compliance_percentage END) as gcp_compliance
                    FROM `{self.project_id}.{self.dataset_trusted}.compliance_status`
                    WHERE date = '{processing_date}'
                    GROUP BY framework
                )
                SELECT
                    '{processing_date}' as comparison_date,
                    c.service_category,
                    c.aws_cost as aws_cost_usd,
                    c.gcp_cost as gcp_cost_usd,
                    s.aws_sla as aws_sla_score,
                    s.gcp_sla as gcp_sla_score,
                    comp.aws_compliance as aws_compliance_score,
                    comp.gcp_compliance as gcp_compliance_score,
                    CASE 
                        WHEN c.aws_cost < c.gcp_cost AND s.aws_sla >= s.gcp_sla THEN 'aws'
                        WHEN c.gcp_cost < c.aws_cost AND s.gcp_sla >= s.aws_sla THEN 'gcp'
                        ELSE 'hybrid'
                    END as recommended_provider,
                    'Based on cost and SLA analysis' as recommendation_reason
                FROM cost_by_provider c
                LEFT JOIN sla_by_provider s ON c.service_category = s.service
                LEFT JOIN compliance_by_provider comp ON TRUE
                """,
                
                "executive_dashboard": f"""
                INSERT INTO `{self.project_id}.{self.dataset_refined}.executive_dashboard`
                WITH daily_metrics AS (
                    SELECT 
                        SUM(cost_usd) as total_spend,
                        COUNT(DISTINCT provider) as provider_count
                    FROM `{self.project_id}.{self.dataset_trusted}.cost_analysis_clean`
                    WHERE date = '{processing_date}'
                ),
                previous_day_metrics AS (
                    SELECT 
                        SUM(cost_usd) as prev_total_spend
                    FROM `{self.project_id}.{self.dataset_trusted}.cost_analysis_clean`
                    WHERE date = DATE_SUB('{processing_date}', INTERVAL 1 DAY)
                ),
                sla_metrics AS (
                    SELECT 
                        AVG(performance_score) as avg_sla_score
                    FROM `{self.project_id}.{self.dataset_trusted}.sla_performance`
                    WHERE date = '{processing_date}'
                ),
                compliance_metrics AS (
                    SELECT 
                        AVG(compliance_percentage) as avg_compliance,
                        AVG(risk_score) as avg_risk_score
                    FROM `{self.project_id}.{self.dataset_trusted}.compliance_status`
                    WHERE date = '{processing_date}'
                ),
                optimization_metrics AS (
                    SELECT 
                        SUM(potential_savings_usd) as total_potential_savings,
                        COUNT(*) as optimization_count
                    FROM `{self.project_id}.{self.dataset_refined}.cost_optimization_insights`
                    WHERE analysis_date = '{processing_date}'
                ),
                agent_metrics AS (
                    SELECT 
                        AVG(100 - error_rate * 100) as avg_agent_health
                    FROM `{self.project_id}.{self.dataset_trusted}.agent_performance`
                    WHERE date = '{processing_date}'
                )
                SELECT
                    '{processing_date}' as report_date,
                    dm.total_spend as total_cloud_spend_usd,
                    SAFE_DIVIDE(dm.total_spend - pdm.prev_total_spend, pdm.prev_total_spend) * 100 as month_over_month_change,
                    COALESCE(om.total_potential_savings, 0) as potential_savings_usd,
                    COALESCE(sm.avg_sla_score, 0) as overall_sla_score,
                    COALESCE(cm.avg_compliance, 0) as compliance_score,
                    COALESCE(cm.avg_risk_score, 0) as risk_score,
                    COALESCE(om.optimization_count, 0) as optimization_opportunities,
                    0 as critical_issues, -- Calculado em pipeline separado
                    COALESCE(am.avg_agent_health, 0) as agent_health_score
                FROM daily_metrics dm
                CROSS JOIN previous_day_metrics pdm
                LEFT JOIN sla_metrics sm ON TRUE
                LEFT JOIN compliance_metrics cm ON TRUE
                LEFT JOIN optimization_metrics om ON TRUE
                LEFT JOIN agent_metrics am ON TRUE
                """,
                
                "legal_compliance_summary": f"""
                INSERT INTO `{self.project_id}.{self.dataset_refined}.legal_compliance_summary`
                WITH compliance_by_framework AS (
                    SELECT 
                        framework,
                        provider,
                        AVG(compliance_percentage) as avg_compliance,
                        AVG(risk_score) as avg_risk,
                        SUM(failed_checks) as total_gaps
                    FROM `{self.project_id}.{self.dataset_trusted}.compliance_status`
                    WHERE date = '{processing_date}'
                    GROUP BY framework, provider
                )
                SELECT
                    '{processing_date}' as assessment_date,
                    'Brazil' as jurisdiction,
                    framework as regulation,
                    CASE 
                        WHEN avg_compliance >= 95 THEN 'Compliant'
                        WHEN avg_compliance >= 80 THEN 'Partially Compliant'
                        ELSE 'Non-Compliant'
                    END as compliance_status,
                    CASE 
                        WHEN avg_risk >= 80 THEN 'High'
                        WHEN avg_risk >= 50 THEN 'Medium'
                        ELSE 'Low'
                    END as risk_level,
                    total_gaps as gaps_identified,
                    avg_compliance < 95 as remediation_required,
                    CASE 
                        WHEN framework = 'LGPD' AND avg_compliance < 80 THEN 50000
                        WHEN avg_risk >= 80 THEN 25000
                        ELSE 0
                    END as estimated_penalty_risk_usd,
                    DATE_ADD('{processing_date}', INTERVAL 30 DAY) as next_review_date,
                    'Cloud Operations Team' as responsible_team
                FROM compliance_by_framework
                """
            }
            
            # Executar agregações
            results = {}
            for table_name, query in aggregation_queries.items():
                try:
                    # Deletar dados existentes para a data
                    date_field = {
                        "cost_optimization_insights": "analysis_date",
                        "provider_comparison": "comparison_date", 
                        "executive_dashboard": "report_date",
                        "legal_compliance_summary": "assessment_date"
                    }.get(table_name, "date")
                    
                    delete_query = f"""
                    DELETE FROM `{self.project_id}.{self.dataset_refined}.{table_name}`
                    WHERE {date_field} = '{processing_date}'
                    """
                    
                    delete_job = self.client.query(delete_query)
                    delete_job.result()
                    
                    # Inserir novos dados
                    job = self.client.query(query)
                    job.result()
                    
                    self.logger.info(f"Tabela REFINED {table_name} processada", {
                        "rows_affected": job.num_dml_affected_rows,
                        "processing_date": processing_date
                    })
                    
                    results[table_name] = {
                        "status": "success",
                        "rows_processed": job.num_dml_affected_rows
                    }
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar {table_name}: {str(e)}")
                    results[table_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "processing_date": processing_date,
                "layer_transition": "TRUSTED → REFINED",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro no processamento TRUSTED → REFINED: {str(e)}")
            return {"error": str(e)}
    
    def run_full_pipeline(self, processing_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa pipeline completo RAW → TRUSTED → REFINED
        
        Args:
            processing_date: Data para processamento (YYYY-MM-DD)
        """
        try:
            if not processing_date:
                processing_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            self.logger.info(f"Iniciando pipeline completo para {processing_date}")
            
            # Executar RAW → TRUSTED
            trusted_result = self.process_raw_to_trusted(processing_date)
            
            # Executar TRUSTED → REFINED
            refined_result = self.process_trusted_to_refined(processing_date)
            
            # Consolidar resultados
            pipeline_success = (
                trusted_result.get("success", False) and 
                refined_result.get("success", False)
            )
            
            return {
                "success": pipeline_success,
                "processing_date": processing_date,
                "pipeline_stages": {
                    "raw_to_trusted": trusted_result,
                    "trusted_to_refined": refined_result
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro no pipeline completo: {str(e)}")
            return {"error": str(e)}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Retorna status do pipeline"""
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            # Verificar última execução
            status_query = f"""
            SELECT 
                'raw' as layer,
                COUNT(*) as total_records,
                MAX(timestamp) as last_update
            FROM `{self.project_id}.{self.dataset_raw}.agent_logs`
            WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAYS)
            
            UNION ALL
            
            SELECT 
                'trusted' as layer,
                COUNT(*) as total_records,
                MAX(date) as last_update
            FROM `{self.project_id}.{self.dataset_trusted}.agent_performance`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAYS)
            
            UNION ALL
            
            SELECT 
                'refined' as layer,
                COUNT(*) as total_records,
                MAX(report_date) as last_update
            FROM `{self.project_id}.{self.dataset_refined}.executive_dashboard`
            WHERE report_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAYS)
            """
            
            job = self.client.query(status_query)
            results = job.result()
            
            status = {}
            for row in results:
                status[row.layer] = {
                    "total_records": row.total_records,
                    "last_update": row.last_update.isoformat() if row.last_update else None
                }
            
            return {
                "success": True,
                "pipeline_status": status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status do pipeline: {str(e)}")
            return {"error": str(e)}

def main():
    """Função principal para executar o pipeline"""
    pipeline = DataPipeline()
    
    print("Executando pipeline de dados...")
    result = pipeline.run_full_pipeline()
    
    if result.get("success"):
        print("✅ Pipeline executado com sucesso!")
        print(f"Data processada: {result['processing_date']}")
        
        # Mostrar resultados por estágio
        for stage, stage_result in result["pipeline_stages"].items():
            print(f"\n{stage.upper()}:")
            if stage_result.get("success"):
                for table, table_result in stage_result["results"].items():
                    status = "✅" if table_result["status"] == "success" else "❌"
                    rows = table_result.get("rows_processed", 0)
                    print(f"  {status} {table}: {rows} registros")
            else:
                print(f"  ❌ Erro: {stage_result.get('error')}")
    else:
        print(f"❌ Erro no pipeline: {result.get('error')}")

if __name__ == "__main__":
    main()

