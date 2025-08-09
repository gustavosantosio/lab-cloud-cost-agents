"""
Sistema de logging para agentes com integração BigQuery
"""
import os
import sys
import json
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from config.project_config import config

class AgentLogger:
    """
    Logger especializado para agentes com integração BigQuery
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.bigquery_client = None
        self.logger = self._setup_logger()
        self._setup_bigquery()
    
    def _setup_logger(self) -> structlog.BoundLogger:
        """Configura o logger estruturado"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        return structlog.get_logger(self.agent_name)
    
    def _setup_bigquery(self):
        """Configura cliente BigQuery para logs"""
        try:
            if config.gcp.credentials_path and os.path.exists(config.gcp.credentials_path):
                self.bigquery_client = bigquery.Client(
                    project=config.bigquery.project_id
                )
                self._ensure_datasets_exist()
            else:
                self.logger.warning("Credenciais GCP não encontradas, logs não serão enviados ao BigQuery")
        except Exception as e:
            self.logger.error(f"Erro ao configurar BigQuery: {str(e)}")
    
    def _ensure_datasets_exist(self):
        """Garante que os datasets do BigQuery existam"""
        datasets = [
            config.bigquery.dataset_raw,
            config.bigquery.dataset_trusted,
            config.bigquery.dataset_refined
        ]
        
        for dataset_id in datasets:
            try:
                dataset_ref = self.bigquery_client.dataset(dataset_id)
                self.bigquery_client.get_dataset(dataset_ref)
            except NotFound:
                # Criar dataset se não existir
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = config.bigquery.location
                dataset.description = f"Dataset para logs de agentes - camada {dataset_id.split('_')[-1].upper()}"
                self.bigquery_client.create_dataset(dataset)
                self.logger.info(f"Dataset criado: {dataset_id}")
    
    def _log_to_bigquery(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """Envia log para BigQuery (camada RAW)"""
        if not self.bigquery_client:
            return
        
        try:
            table_id = f"{config.bigquery.project_id}.{config.bigquery.dataset_raw}.agent_logs"
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent_name": self.agent_name,
                "level": level,
                "message": message,
                "extra_data": json.dumps(extra) if extra else None,
                "session_id": os.getenv("SESSION_ID", "default"),
                "execution_id": os.getenv("EXECUTION_ID", "default")
            }
            
            # Inserir no BigQuery
            errors = self.bigquery_client.insert_rows_json(
                self.bigquery_client.get_table(table_id), 
                [log_entry]
            )
            
            if errors:
                self.logger.error(f"Erro ao inserir log no BigQuery: {errors}")
                
        except Exception as e:
            # Não falhar se o BigQuery não estiver disponível
            self.logger.error(f"Erro ao enviar log para BigQuery: {str(e)}")
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log de informação"""
        self.logger.info(message, **extra if extra else {})
        self._log_to_bigquery("INFO", message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log de aviso"""
        self.logger.warning(message, **extra if extra else {})
        self._log_to_bigquery("WARNING", message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log de erro"""
        self.logger.error(message, **extra if extra else {})
        self._log_to_bigquery("ERROR", message, extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log de debug"""
        self.logger.debug(message, **extra if extra else {})
        self._log_to_bigquery("DEBUG", message, extra)
    
    def log_agent_action(self, action: str, input_data: Any, output_data: Any, duration: float):
        """Log específico para ações de agentes"""
        extra_data = {
            "action": action,
            "input_data": str(input_data)[:1000],  # Limitar tamanho
            "output_data": str(output_data)[:1000],  # Limitar tamanho
            "duration_seconds": duration,
            "agent_type": "operational" if "manager" in self.agent_name.lower() else "specialist"
        }
        
        self.info(f"Ação executada: {action}", extra_data)
    
    def log_cost_analysis(self, provider: str, cost_data: Dict[str, Any]):
        """Log específico para análise de custos"""
        extra_data = {
            "provider": provider,
            "cost_data": cost_data,
            "analysis_type": "cost_analysis"
        }
        
        self.info(f"Análise de custos realizada para {provider}", extra_data)
    
    def log_sla_analysis(self, sla_data: Dict[str, Any]):
        """Log específico para análise de SLA"""
        extra_data = {
            "sla_data": sla_data,
            "analysis_type": "sla_analysis"
        }
        
        self.info("Análise de SLA realizada", extra_data)
    
    def log_compliance_check(self, compliance_result: Dict[str, Any]):
        """Log específico para verificação de conformidade"""
        extra_data = {
            "compliance_result": compliance_result,
            "analysis_type": "compliance_check"
        }
        
        self.info("Verificação de conformidade realizada", extra_data)

