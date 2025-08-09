"""
Configuração do BigQuery Data Lake
Sistema de logs com camadas RAW, TRUSTED e REFINED
"""
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth import default

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.project_config import config
from agents.base.logger import AgentLogger

class BigQueryDataLake:
    """
    Configuração e gerenciamento do Data Lake no BigQuery
    """
    
    def __init__(self):
        self.logger = AgentLogger("BigQueryDataLake")
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
            
            self.logger.info("Cliente BigQuery inicializado", {
                "project_id": self.project_id
            })
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar BigQuery: {str(e)}")
            self.client = None
    
    def create_datasets(self) -> Dict[str, Any]:
        """Cria os datasets para as camadas do Data Lake"""
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            datasets_config = {
                self.dataset_raw: {
                    "description": "Camada RAW - Dados brutos de logs dos agentes",
                    "location": "US",
                    "default_table_expiration_ms": None  # Sem expiração
                },
                self.dataset_trusted: {
                    "description": "Camada TRUSTED - Dados limpos e estruturados",
                    "location": "US", 
                    "default_table_expiration_ms": None
                },
                self.dataset_refined: {
                    "description": "Camada REFINED - Dados prontos para análise e relatórios",
                    "location": "US",
                    "default_table_expiration_ms": None
                }
            }
            
            created_datasets = []
            
            for dataset_id, config_data in datasets_config.items():
                try:
                    # Verificar se dataset já existe
                    dataset_ref = self.client.dataset(dataset_id)
                    
                    try:
                        self.client.get_dataset(dataset_ref)
                        self.logger.info(f"Dataset {dataset_id} já existe")
                        created_datasets.append({"name": dataset_id, "status": "exists"})
                        continue
                    except:
                        pass  # Dataset não existe, criar
                    
                    # Criar dataset
                    dataset = bigquery.Dataset(dataset_ref)
                    dataset.description = config_data["description"]
                    dataset.location = config_data["location"]
                    
                    if config_data["default_table_expiration_ms"]:
                        dataset.default_table_expiration_ms = config_data["default_table_expiration_ms"]
                    
                    dataset = self.client.create_dataset(dataset, timeout=30)
                    
                    self.logger.info(f"Dataset {dataset_id} criado", {
                        "location": dataset.location,
                        "description": dataset.description
                    })
                    
                    created_datasets.append({"name": dataset_id, "status": "created"})
                    
                except Exception as e:
                    self.logger.error(f"Erro ao criar dataset {dataset_id}: {str(e)}")
                    created_datasets.append({"name": dataset_id, "status": "error", "error": str(e)})
            
            return {
                "success": True,
                "datasets": created_datasets,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na criação de datasets: {str(e)}")
            return {"error": str(e)}
    
    def create_raw_tables(self) -> Dict[str, Any]:
        """Cria tabelas na camada RAW"""
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            raw_tables = {
                "agent_logs": {
                    "description": "Logs brutos de todos os agentes",
                    "schema": [
                        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                        bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("agent_type", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("log_level", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("message", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("extra_data", "JSON", mode="NULLABLE"),
                        bigquery.SchemaField("session_id", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("task_id", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("execution_time_ms", "INTEGER", mode="NULLABLE"),
                        bigquery.SchemaField("error_details", "JSON", mode="NULLABLE")
                    ]
                },
                "mcp_requests": {
                    "description": "Logs de requisições MCP entre agentes",
                    "schema": [
                        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                        bigquery.SchemaField("mcp_server", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("tool_name", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("request_data", "JSON", mode="REQUIRED"),
                        bigquery.SchemaField("response_data", "JSON", mode="NULLABLE"),
                        bigquery.SchemaField("response_time_ms", "INTEGER", mode="NULLABLE"),
                        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("error_message", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("requesting_agent", "STRING", mode="REQUIRED")
                    ]
                },
                "cost_analysis_raw": {
                    "description": "Dados brutos de análise de custos",
                    "schema": [
                        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                        bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("service", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("resource_id", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("cost_data", "JSON", mode="REQUIRED"),
                        bigquery.SchemaField("usage_data", "JSON", mode="NULLABLE"),
                        bigquery.SchemaField("region", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("account_id", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("tags", "JSON", mode="NULLABLE")
                    ]
                },
                "sla_metrics_raw": {
                    "description": "Métricas brutas de SLA",
                    "schema": [
                        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                        bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("service", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("metric_type", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("metric_value", "FLOAT", mode="REQUIRED"),
                        bigquery.SchemaField("metric_unit", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("region", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("availability_zone", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("incident_id", "STRING", mode="NULLABLE")
                    ]
                },
                "compliance_checks_raw": {
                    "description": "Resultados brutos de verificações de compliance",
                    "schema": [
                        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                        bigquery.SchemaField("framework", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("control_id", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("resource_id", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("check_result", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("details", "JSON", mode="NULLABLE"),
                        bigquery.SchemaField("remediation", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("provider", "STRING", mode="REQUIRED")
                    ]
                }
            }
            
            created_tables = []
            
            for table_name, table_config in raw_tables.items():
                try:
                    table_ref = self.client.dataset(self.dataset_raw).table(table_name)
                    
                    # Verificar se tabela já existe
                    try:
                        self.client.get_table(table_ref)
                        self.logger.info(f"Tabela RAW {table_name} já existe")
                        created_tables.append({"name": table_name, "status": "exists"})
                        continue
                    except:
                        pass  # Tabela não existe, criar
                    
                    # Criar tabela
                    table = bigquery.Table(table_ref, schema=table_config["schema"])
                    table.description = table_config["description"]
                    
                    # Configurar particionamento por timestamp
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field="timestamp"
                    )
                    
                    table = self.client.create_table(table)
                    
                    self.logger.info(f"Tabela RAW {table_name} criada", {
                        "schema_fields": len(table.schema),
                        "partitioned": True
                    })
                    
                    created_tables.append({"name": table_name, "status": "created"})
                    
                except Exception as e:
                    self.logger.error(f"Erro ao criar tabela {table_name}: {str(e)}")
                    created_tables.append({"name": table_name, "status": "error", "error": str(e)})
            
            return {
                "success": True,
                "tables": created_tables,
                "dataset": self.dataset_raw,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na criação de tabelas RAW: {str(e)}")
            return {"error": str(e)}
    
    def create_trusted_tables(self) -> Dict[str, Any]:
        """Cria tabelas na camada TRUSTED"""
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            trusted_tables = {
                "agent_performance": {
                    "description": "Métricas de performance dos agentes processadas",
                    "schema": [
                        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("agent_type", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("total_executions", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("successful_executions", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("failed_executions", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("avg_execution_time_ms", "FLOAT", mode="REQUIRED"),
                        bigquery.SchemaField("max_execution_time_ms", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("min_execution_time_ms", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("error_rate", "FLOAT", mode="REQUIRED")
                    ]
                },
                "cost_analysis_clean": {
                    "description": "Dados de custos limpos e normalizados",
                    "schema": [
                        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("service_category", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("service_name", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("region", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("cost_usd", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("usage_quantity", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("usage_unit", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("resource_count", "INTEGER", mode="NULLABLE"),
                        bigquery.SchemaField("account_id", "STRING", mode="REQUIRED")
                    ]
                },
                "sla_performance": {
                    "description": "Métricas de SLA processadas",
                    "schema": [
                        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("service", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("region", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("availability_percentage", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("downtime_minutes", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("incident_count", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("sla_target", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("sla_breach", "BOOLEAN", mode="REQUIRED"),
                        bigquery.SchemaField("performance_score", "NUMERIC", mode="REQUIRED")
                    ]
                },
                "compliance_status": {
                    "description": "Status de compliance processado",
                    "schema": [
                        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("framework", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("control_category", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("total_checks", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("passed_checks", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("failed_checks", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("critical_failures", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("compliance_percentage", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("risk_score", "NUMERIC", mode="REQUIRED")
                    ]
                }
            }
            
            created_tables = []
            
            for table_name, table_config in trusted_tables.items():
                try:
                    table_ref = self.client.dataset(self.dataset_trusted).table(table_name)
                    
                    # Verificar se tabela já existe
                    try:
                        self.client.get_table(table_ref)
                        self.logger.info(f"Tabela TRUSTED {table_name} já existe")
                        created_tables.append({"name": table_name, "status": "exists"})
                        continue
                    except:
                        pass
                    
                    # Criar tabela
                    table = bigquery.Table(table_ref, schema=table_config["schema"])
                    table.description = table_config["description"]
                    
                    # Configurar particionamento por data
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field="date"
                    )
                    
                    table = self.client.create_table(table)
                    
                    self.logger.info(f"Tabela TRUSTED {table_name} criada")
                    created_tables.append({"name": table_name, "status": "created"})
                    
                except Exception as e:
                    self.logger.error(f"Erro ao criar tabela TRUSTED {table_name}: {str(e)}")
                    created_tables.append({"name": table_name, "status": "error", "error": str(e)})
            
            return {
                "success": True,
                "tables": created_tables,
                "dataset": self.dataset_trusted,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na criação de tabelas TRUSTED: {str(e)}")
            return {"error": str(e)}
    
    def create_refined_tables(self) -> Dict[str, Any]:
        """Cria tabelas na camada REFINED"""
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            refined_tables = {
                "cost_optimization_insights": {
                    "description": "Insights de otimização de custos para relatórios",
                    "schema": [
                        bigquery.SchemaField("analysis_date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("optimization_type", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("current_cost_usd", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("potential_savings_usd", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("savings_percentage", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("implementation_effort", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("roi_months", "INTEGER", mode="NULLABLE"),
                        bigquery.SchemaField("recommendation", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("priority_score", "NUMERIC", mode="REQUIRED")
                    ]
                },
                "provider_comparison": {
                    "description": "Comparação entre provedores para decisões estratégicas",
                    "schema": [
                        bigquery.SchemaField("comparison_date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("service_category", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("aws_cost_usd", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("gcp_cost_usd", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("aws_sla_score", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("gcp_sla_score", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("aws_compliance_score", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("gcp_compliance_score", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("recommended_provider", "STRING", mode="NULLABLE"),
                        bigquery.SchemaField("recommendation_reason", "STRING", mode="NULLABLE")
                    ]
                },
                "executive_dashboard": {
                    "description": "Métricas executivas agregadas",
                    "schema": [
                        bigquery.SchemaField("report_date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("total_cloud_spend_usd", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("month_over_month_change", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("potential_savings_usd", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("overall_sla_score", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("compliance_score", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("risk_score", "NUMERIC", mode="REQUIRED"),
                        bigquery.SchemaField("optimization_opportunities", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("critical_issues", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("agent_health_score", "NUMERIC", mode="REQUIRED")
                    ]
                },
                "legal_compliance_summary": {
                    "description": "Resumo de compliance jurídico",
                    "schema": [
                        bigquery.SchemaField("assessment_date", "DATE", mode="REQUIRED"),
                        bigquery.SchemaField("jurisdiction", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("regulation", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("compliance_status", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("risk_level", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("gaps_identified", "INTEGER", mode="REQUIRED"),
                        bigquery.SchemaField("remediation_required", "BOOLEAN", mode="REQUIRED"),
                        bigquery.SchemaField("estimated_penalty_risk_usd", "NUMERIC", mode="NULLABLE"),
                        bigquery.SchemaField("next_review_date", "DATE", mode="NULLABLE"),
                        bigquery.SchemaField("responsible_team", "STRING", mode="REQUIRED")
                    ]
                }
            }
            
            created_tables = []
            
            for table_name, table_config in refined_tables.items():
                try:
                    table_ref = self.client.dataset(self.dataset_refined).table(table_name)
                    
                    # Verificar se tabela já existe
                    try:
                        self.client.get_table(table_ref)
                        self.logger.info(f"Tabela REFINED {table_name} já existe")
                        created_tables.append({"name": table_name, "status": "exists"})
                        continue
                    except:
                        pass
                    
                    # Criar tabela
                    table = bigquery.Table(table_ref, schema=table_config["schema"])
                    table.description = table_config["description"]
                    
                    # Configurar particionamento pela primeira coluna de data
                    date_field = table_config["schema"][0].name
                    table.time_partitioning = bigquery.TimePartitioning(
                        type_=bigquery.TimePartitioningType.DAY,
                        field=date_field
                    )
                    
                    table = self.client.create_table(table)
                    
                    self.logger.info(f"Tabela REFINED {table_name} criada")
                    created_tables.append({"name": table_name, "status": "created"})
                    
                except Exception as e:
                    self.logger.error(f"Erro ao criar tabela REFINED {table_name}: {str(e)}")
                    created_tables.append({"name": table_name, "status": "error", "error": str(e)})
            
            return {
                "success": True,
                "tables": created_tables,
                "dataset": self.dataset_refined,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na criação de tabelas REFINED: {str(e)}")
            return {"error": str(e)}
    
    def setup_complete_data_lake(self) -> Dict[str, Any]:
        """Configura o Data Lake completo"""
        try:
            self.logger.info("Iniciando configuração completa do Data Lake")
            
            results = {
                "datasets": None,
                "raw_tables": None,
                "trusted_tables": None,
                "refined_tables": None
            }
            
            # Criar datasets
            datasets_result = self.create_datasets()
            results["datasets"] = datasets_result
            
            if not datasets_result.get("success"):
                return {"error": "Falha na criação de datasets", "details": results}
            
            # Criar tabelas RAW
            raw_result = self.create_raw_tables()
            results["raw_tables"] = raw_result
            
            # Criar tabelas TRUSTED
            trusted_result = self.create_trusted_tables()
            results["trusted_tables"] = trusted_result
            
            # Criar tabelas REFINED
            refined_result = self.create_refined_tables()
            results["refined_tables"] = refined_result
            
            self.logger.info("Configuração do Data Lake concluída")
            
            return {
                "success": True,
                "message": "Data Lake configurado com sucesso",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na configuração do Data Lake: {str(e)}")
            return {"error": str(e)}
    
    def get_data_lake_info(self) -> Dict[str, Any]:
        """Retorna informações do Data Lake"""
        try:
            if not self.client:
                return {"error": "Cliente BigQuery não inicializado"}
            
            info = {
                "project_id": self.project_id,
                "datasets": {
                    "raw": self.dataset_raw,
                    "trusted": self.dataset_trusted,
                    "refined": self.dataset_refined
                },
                "status": "configured" if self.client else "not_configured"
            }
            
            # Verificar se datasets existem
            for layer, dataset_id in info["datasets"].items():
                try:
                    dataset_ref = self.client.dataset(dataset_id)
                    dataset = self.client.get_dataset(dataset_ref)
                    
                    # Contar tabelas
                    tables = list(self.client.list_tables(dataset))
                    info["datasets"][layer] = {
                        "name": dataset_id,
                        "exists": True,
                        "tables_count": len(tables),
                        "location": dataset.location,
                        "description": dataset.description
                    }
                    
                except:
                    info["datasets"][layer] = {
                        "name": dataset_id,
                        "exists": False
                    }
            
            return info
            
        except Exception as e:
            return {"error": str(e)}

def main():
    """Função principal para configurar o Data Lake"""
    data_lake = BigQueryDataLake()
    
    print("Configurando BigQuery Data Lake...")
    result = data_lake.setup_complete_data_lake()
    
    if result.get("success"):
        print("✅ Data Lake configurado com sucesso!")
        
        # Mostrar informações
        info = data_lake.get_data_lake_info()
        print(f"\nInformações do Data Lake:")
        print(f"Projeto: {info['project_id']}")
        print(f"Status: {info['status']}")
        
        for layer, details in info["datasets"].items():
            if isinstance(details, dict):
                status = "✅" if details.get("exists") else "❌"
                print(f"{layer.upper()}: {status} {details['name']} ({details.get('tables_count', 0)} tabelas)")
    else:
        print(f"❌ Erro na configuração: {result.get('error')}")

if __name__ == "__main__":
    main()

