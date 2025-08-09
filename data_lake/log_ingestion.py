"""
Sistema de Ingestão de Logs para BigQuery
Coleta logs dos agentes e insere na camada RAW
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth import default
import threading
import queue
import time

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.project_config import config
from agents.base.logger import AgentLogger

class LogIngestion:
    """
    Sistema de ingestão de logs para BigQuery
    """
    
    def __init__(self):
        self.logger = AgentLogger("LogIngestion")
        self.client = None
        self.project_id = config.gcp.project_id
        self.dataset_raw = "cloud_agents_raw"
        self.log_queue = queue.Queue()
        self.batch_size = 100
        self.batch_timeout = 30  # segundos
        self.ingestion_thread = None
        self.running = False
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
            
            self.logger.info("Cliente BigQuery inicializado para ingestão")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar BigQuery: {str(e)}")
            self.client = None
    
    def start_ingestion(self):
        """Inicia o processo de ingestão em background"""
        if self.running:
            return
        
        self.running = True
        self.ingestion_thread = threading.Thread(target=self._ingestion_worker)
        self.ingestion_thread.daemon = True
        self.ingestion_thread.start()
        
        self.logger.info("Sistema de ingestão iniciado")
    
    def stop_ingestion(self):
        """Para o processo de ingestão"""
        self.running = False
        if self.ingestion_thread:
            self.ingestion_thread.join(timeout=5)
        
        # Processar logs restantes
        self._flush_logs()
        
        self.logger.info("Sistema de ingestão parado")
    
    def _ingestion_worker(self):
        """Worker thread para processar logs em lotes"""
        batch = []
        last_flush = time.time()
        
        while self.running:
            try:
                # Tentar obter log da fila
                try:
                    log_entry = self.log_queue.get(timeout=1)
                    batch.append(log_entry)
                except queue.Empty:
                    pass
                
                # Verificar se deve fazer flush
                current_time = time.time()
                should_flush = (
                    len(batch) >= self.batch_size or
                    (batch and current_time - last_flush >= self.batch_timeout)
                )
                
                if should_flush:
                    self._insert_batch(batch)
                    batch = []
                    last_flush = current_time
                    
            except Exception as e:
                self.logger.error(f"Erro no worker de ingestão: {str(e)}")
                time.sleep(1)
        
        # Processar batch final
        if batch:
            self._insert_batch(batch)
    
    def _insert_batch(self, batch: List[Dict[str, Any]]):
        """Insere lote de logs no BigQuery"""
        if not batch or not self.client:
            return
        
        try:
            # Agrupar logs por tabela
            tables_data = {}
            
            for log_entry in batch:
                table_name = log_entry.get("table", "agent_logs")
                if table_name not in tables_data:
                    tables_data[table_name] = []
                tables_data[table_name].append(log_entry["data"])
            
            # Inserir em cada tabela
            for table_name, rows in tables_data.items():
                table_ref = self.client.dataset(self.dataset_raw).table(table_name)
                
                errors = self.client.insert_rows_json(table_ref, rows)
                
                if errors:
                    self.logger.error(f"Erros na inserção em {table_name}: {errors}")
                else:
                    self.logger.debug(f"Inseridos {len(rows)} registros em {table_name}")
            
        except Exception as e:
            self.logger.error(f"Erro na inserção de lote: {str(e)}")
    
    def _flush_logs(self):
        """Força o processamento de todos os logs na fila"""
        batch = []
        
        while not self.log_queue.empty():
            try:
                log_entry = self.log_queue.get_nowait()
                batch.append(log_entry)
            except queue.Empty:
                break
        
        if batch:
            self._insert_batch(batch)
    
    def log_agent_activity(
        self,
        agent_name: str,
        agent_type: str,
        log_level: str,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Registra atividade de agente
        
        Args:
            agent_name: Nome do agente
            agent_type: Tipo do agente (operational, specialist, coordinator)
            log_level: Nível do log (INFO, WARNING, ERROR)
            message: Mensagem do log
            extra_data: Dados adicionais
            session_id: ID da sessão
            task_id: ID da tarefa
            execution_time_ms: Tempo de execução em ms
            error_details: Detalhes do erro se houver
        """
        log_entry = {
            "table": "agent_logs",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent_name,
                "agent_type": agent_type,
                "log_level": log_level,
                "message": message,
                "extra_data": json.dumps(extra_data) if extra_data else None,
                "session_id": session_id or str(uuid.uuid4()),
                "task_id": task_id,
                "execution_time_ms": execution_time_ms,
                "error_details": json.dumps(error_details) if error_details else None
            }
        }
        
        self.log_queue.put(log_entry)
    
    def log_mcp_request(
        self,
        mcp_server: str,
        tool_name: str,
        request_data: Dict[str, Any],
        response_data: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        requesting_agent: str = "unknown"
    ):
        """
        Registra requisição MCP
        
        Args:
            mcp_server: Nome do servidor MCP
            tool_name: Nome da ferramenta chamada
            request_data: Dados da requisição
            response_data: Dados da resposta
            response_time_ms: Tempo de resposta em ms
            status: Status da requisição (success, error)
            error_message: Mensagem de erro se houver
            requesting_agent: Agente que fez a requisição
        """
        log_entry = {
            "table": "mcp_requests",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "mcp_server": mcp_server,
                "tool_name": tool_name,
                "request_data": json.dumps(request_data),
                "response_data": json.dumps(response_data) if response_data else None,
                "response_time_ms": response_time_ms,
                "status": status,
                "error_message": error_message,
                "requesting_agent": requesting_agent
            }
        }
        
        self.log_queue.put(log_entry)
    
    def log_cost_analysis(
        self,
        provider: str,
        service: str,
        cost_data: Dict[str, Any],
        resource_id: Optional[str] = None,
        usage_data: Optional[Dict[str, Any]] = None,
        region: Optional[str] = None,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Registra dados de análise de custos
        
        Args:
            provider: Provedor cloud (aws, gcp)
            service: Nome do serviço
            cost_data: Dados de custo
            resource_id: ID do recurso
            usage_data: Dados de uso
            region: Região
            account_id: ID da conta
            tags: Tags do recurso
        """
        log_entry = {
            "table": "cost_analysis_raw",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "provider": provider,
                "service": service,
                "resource_id": resource_id,
                "cost_data": json.dumps(cost_data),
                "usage_data": json.dumps(usage_data) if usage_data else None,
                "region": region,
                "account_id": account_id,
                "tags": json.dumps(tags) if tags else None
            }
        }
        
        self.log_queue.put(log_entry)
    
    def log_sla_metric(
        self,
        provider: str,
        service: str,
        metric_type: str,
        metric_value: float,
        metric_unit: str,
        region: Optional[str] = None,
        availability_zone: Optional[str] = None,
        incident_id: Optional[str] = None
    ):
        """
        Registra métrica de SLA
        
        Args:
            provider: Provedor cloud
            service: Nome do serviço
            metric_type: Tipo da métrica (availability, latency, etc.)
            metric_value: Valor da métrica
            metric_unit: Unidade da métrica
            region: Região
            availability_zone: Zona de disponibilidade
            incident_id: ID do incidente se houver
        """
        log_entry = {
            "table": "sla_metrics_raw",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "provider": provider,
                "service": service,
                "metric_type": metric_type,
                "metric_value": metric_value,
                "metric_unit": metric_unit,
                "region": region,
                "availability_zone": availability_zone,
                "incident_id": incident_id
            }
        }
        
        self.log_queue.put(log_entry)
    
    def log_compliance_check(
        self,
        framework: str,
        control_id: str,
        resource_id: str,
        check_result: str,
        severity: str,
        provider: str,
        details: Optional[Dict[str, Any]] = None,
        remediation: Optional[str] = None
    ):
        """
        Registra resultado de verificação de compliance
        
        Args:
            framework: Framework de compliance (ISO27001, SOC2, etc.)
            control_id: ID do controle
            resource_id: ID do recurso verificado
            check_result: Resultado (PASS, FAIL, WARNING)
            severity: Severidade (LOW, MEDIUM, HIGH, CRITICAL)
            provider: Provedor cloud
            details: Detalhes da verificação
            remediation: Ação de remediação recomendada
        """
        log_entry = {
            "table": "compliance_checks_raw",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "framework": framework,
                "control_id": control_id,
                "resource_id": resource_id,
                "check_result": check_result,
                "severity": severity,
                "details": json.dumps(details) if details else None,
                "remediation": remediation,
                "provider": provider
            }
        }
        
        self.log_queue.put(log_entry)
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de ingestão"""
        return {
            "running": self.running,
            "queue_size": self.log_queue.qsize(),
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout,
            "client_connected": self.client is not None,
            "timestamp": datetime.now().isoformat()
        }

# Instância global para uso pelos agentes
log_ingestion = LogIngestion()

def start_log_ingestion():
    """Inicia o sistema de ingestão de logs"""
    log_ingestion.start_ingestion()

def stop_log_ingestion():
    """Para o sistema de ingestão de logs"""
    log_ingestion.stop_ingestion()

def main():
    """Função principal para teste do sistema de ingestão"""
    print("Iniciando sistema de ingestão de logs...")
    
    # Iniciar ingestão
    log_ingestion.start_ingestion()
    
    # Simular alguns logs
    log_ingestion.log_agent_activity(
        agent_name="TestAgent",
        agent_type="operational",
        log_level="INFO",
        message="Teste de ingestão de logs",
        extra_data={"test": True},
        execution_time_ms=150
    )
    
    log_ingestion.log_mcp_request(
        mcp_server="aws-cost-api",
        tool_name="get_cost_and_usage",
        request_data={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        response_data={"success": True, "data": []},
        response_time_ms=500,
        requesting_agent="CostCoordinator"
    )
    
    # Aguardar processamento
    time.sleep(5)
    
    # Mostrar estatísticas
    stats = log_ingestion.get_ingestion_stats()
    print(f"Estatísticas de ingestão: {stats}")
    
    # Parar ingestão
    log_ingestion.stop_ingestion()
    print("Sistema de ingestão parado")

if __name__ == "__main__":
    main()

