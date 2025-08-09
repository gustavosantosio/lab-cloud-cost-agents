"""
Sistema completo de logging e analytics para agentes de IA
"""

import json
import time
import uuid
import psutil
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# GCP imports
from google.cloud import logging as cloud_logging
from google.cloud import pubsub_v1
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

# Local imports
import logging
import os


@dataclass
class AgentExecution:
    """Estrutura para log de execução de agente"""
    execution_id: str
    timestamp: str
    agent_type: str
    agent_name: str
    task_type: str
    input_parameters: Dict[str, Any]
    execution_duration_ms: int
    status: str
    error_message: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class CostComparison:
    """Estrutura para log de comparação de custos"""
    comparison_id: str
    timestamp: str
    analysis_type: str
    providers: List[str]
    input_requirements: Dict[str, Any]
    aws_results: Optional[Dict[str, Any]] = None
    gcp_results: Optional[Dict[str, Any]] = None
    azure_results: Optional[Dict[str, Any]] = None
    onpremise_results: Optional[Dict[str, Any]] = None
    final_recommendation: str = ""
    confidence_score: Optional[float] = None
    cost_savings_percentage: Optional[float] = None
    cost_savings_amount_usd: Optional[float] = None
    reasoning: Optional[str] = None
    execution_time_ms: Optional[int] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class AgentInteraction:
    """Estrutura para log de interação entre agentes"""
    interaction_id: str
    timestamp: str
    source_agent: str
    target_agent: Optional[str]
    interaction_type: str
    message_content: Dict[str, Any]
    response_time_ms: Optional[int] = None
    success: Optional[bool] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class MCPServerCall:
    """Estrutura para log de chamadas MCP"""
    call_id: str
    timestamp: str
    server_type: str
    method_name: str
    input_parameters: Dict[str, Any]
    response_data: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    cache_hit: Optional[bool] = None
    api_cost_usd: Optional[float] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None


class CloudCostLogger:
    """
    Sistema completo de logging para Cloud Cost Agent
    Integra com Cloud Logging, Pub/Sub e BigQuery
    """
    
    def __init__(self, project_id: str = None, dataset_id: str = "agent_analytics"):
        """
        Inicializa o logger com configurações GCP
        
        Args:
            project_id: ID do projeto GCP
            dataset_id: ID do dataset BigQuery
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.dataset_id = dataset_id
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID deve ser definido")
        
        # Configurar clientes GCP
        self._setup_gcp_clients()
        
        # Configurar logging local
        self._setup_local_logging()
        
        # Buffer para batch processing
        self._log_buffer = []
        self._buffer_lock = threading.Lock()
        self._buffer_size = 100
        
        # Métricas internas
        self._metrics = {
            'logs_sent': 0,
            'errors': 0,
            'last_flush': time.time()
        }
    
    def _setup_gcp_clients(self):
        """Configura clientes GCP"""
        try:
            # Cloud Logging
            self.cloud_logging_client = cloud_logging.Client(project=self.project_id)
            self.cloud_logging_client.setup_logging()
            
            # Pub/Sub
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(
                self.project_id, 
                os.getenv('PUBSUB_TOPIC_NAME', 'agent-analysis-events')
            )
            
            # BigQuery
            self.bigquery_client = bigquery.Client(project=self.project_id)
            
            # Verificar se dataset existe
            try:
                self.bigquery_client.get_dataset(f"{self.project_id}.{self.dataset_id}")
            except Exception:
                logging.warning(f"Dataset {self.dataset_id} não encontrado. Verifique a configuração.")
                
        except GoogleCloudError as e:
            logging.error(f"Erro ao configurar clientes GCP: {e}")
            raise
    
    def _setup_local_logging(self):
        """Configura logging local para fallback"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cloud_cost_agent.log'),
                logging.StreamHandler()
            ]
        )
        self.local_logger = logging.getLogger('CloudCostAgent')
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Obtém métricas do sistema"""
        try:
            process = psutil.Process()
            return {
                'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_usage_percent': process.cpu_percent()
            }
        except Exception:
            return {'memory_usage_mb': None, 'cpu_usage_percent': None}
    
    def _generate_id(self) -> str:
        """Gera ID único"""
        return str(uuid.uuid4())
    
    def _get_timestamp(self) -> str:
        """Obtém timestamp ISO"""
        return datetime.now(timezone.utc).isoformat()
    
    def _send_to_pubsub(self, data: Dict[str, Any], message_type: str):
        """Envia dados para Pub/Sub"""
        try:
            message_data = {
                'type': message_type,
                'data': data,
                'timestamp': self._get_timestamp()
            }
            
            message_json = json.dumps(message_data, default=str)
            message_bytes = message_json.encode('utf-8')
            
            future = self.publisher.publish(
                self.topic_path, 
                message_bytes,
                message_type=message_type
            )
            
            # Não bloquear - fire and forget
            return future
            
        except Exception as e:
            self.local_logger.error(f"Erro ao enviar para Pub/Sub: {e}")
            return None
    
    def _log_to_cloud_logging(self, data: Dict[str, Any], log_name: str, severity: str = 'INFO'):
        """Envia log para Cloud Logging"""
        try:
            logger = self.cloud_logging_client.logger(log_name)
            logger.log_struct(data, severity=severity)
            
        except Exception as e:
            self.local_logger.error(f"Erro ao enviar para Cloud Logging: {e}")
    
    def _add_to_buffer(self, data: Dict[str, Any]):
        """Adiciona dados ao buffer para batch processing"""
        with self._buffer_lock:
            self._log_buffer.append(data)
            
            if len(self._log_buffer) >= self._buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush do buffer para BigQuery"""
        if not self._log_buffer:
            return
        
        try:
            # Agrupar por tipo de tabela
            tables_data = {}
            
            for item in self._log_buffer:
                table_name = item.get('_table_name', 'agent_executions')
                if table_name not in tables_data:
                    tables_data[table_name] = []
                
                # Remover metadados internos
                clean_item = {k: v for k, v in item.items() if not k.startswith('_')}
                tables_data[table_name].append(clean_item)
            
            # Inserir em cada tabela
            for table_name, rows in tables_data.items():
                table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_name)
                
                try:
                    errors = self.bigquery_client.insert_rows_json(table_ref, rows)
                    if errors:
                        self.local_logger.error(f"Erros ao inserir em {table_name}: {errors}")
                    else:
                        self._metrics['logs_sent'] += len(rows)
                        
                except Exception as e:
                    self.local_logger.error(f"Erro ao inserir em {table_name}: {e}")
            
            # Limpar buffer
            self._log_buffer.clear()
            self._metrics['last_flush'] = time.time()
            
        except Exception as e:
            self.local_logger.error(f"Erro no flush do buffer: {e}")
            self._metrics['errors'] += 1
    
    @contextmanager
    def log_agent_execution_context(self, agent_type: str, agent_name: str, 
                                   task_type: str, session_id: str = None, 
                                   user_id: str = None, **kwargs):
        """
        Context manager para log automático de execução de agente
        
        Usage:
            with logger.log_agent_execution_context('aws_specialist', 'analyze_costs', 'cost_analysis') as ctx:
                # Código do agente
                result = agent.execute()
                ctx.set_result(result)
        """
        execution_id = self._generate_id()
        start_time = time.time()
        
        class ExecutionContext:
            def __init__(self, logger_instance):
                self.logger = logger_instance
                self.result = None
                self.error = None
                
            def set_result(self, result):
                self.result = result
                
            def set_error(self, error):
                self.error = error
        
        context = ExecutionContext(self)
        
        try:
            yield context
            
            # Log de sucesso
            duration_ms = int((time.time() - start_time) * 1000)
            system_metrics = self._get_system_metrics()
            
            execution = AgentExecution(
                execution_id=execution_id,
                timestamp=self._get_timestamp(),
                agent_type=agent_type,
                agent_name=agent_name,
                task_type=task_type,
                input_parameters=kwargs,
                execution_duration_ms=duration_ms,
                status='success',
                memory_usage_mb=system_metrics.get('memory_usage_mb'),
                cpu_usage_percent=system_metrics.get('cpu_usage_percent'),
                session_id=session_id,
                user_id=user_id,
                request_id=self._generate_id()
            )
            
            self._log_execution(execution)
            
        except Exception as e:
            # Log de erro
            duration_ms = int((time.time() - start_time) * 1000)
            system_metrics = self._get_system_metrics()
            
            execution = AgentExecution(
                execution_id=execution_id,
                timestamp=self._get_timestamp(),
                agent_type=agent_type,
                agent_name=agent_name,
                task_type=task_type,
                input_parameters=kwargs,
                execution_duration_ms=duration_ms,
                status='error',
                error_message=str(e),
                memory_usage_mb=system_metrics.get('memory_usage_mb'),
                cpu_usage_percent=system_metrics.get('cpu_usage_percent'),
                session_id=session_id,
                user_id=user_id,
                request_id=self._generate_id()
            )
            
            self._log_execution(execution)
            raise
    
    def _log_execution(self, execution: AgentExecution):
        """Log interno de execução"""
        data = asdict(execution)
        data['_table_name'] = 'agent_executions'
        
        # Cloud Logging
        self._log_to_cloud_logging(data, 'agent-executions')
        
        # Pub/Sub
        self._send_to_pubsub(data, 'agent_execution')
        
        # Buffer para BigQuery
        self._add_to_buffer(data)
    
    def log_cost_comparison(self, analysis_type: str, providers: List[str],
                          input_requirements: Dict[str, Any],
                          results_by_provider: Dict[str, Any],
                          recommendation: str, confidence: float,
                          savings_pct: float, savings_amount: float,
                          reasoning: str, execution_time: int,
                          session_id: str = None, user_id: str = None) -> str:
        """
        Log de comparação de custos
        
        Returns:
            comparison_id: ID único da comparação
        """
        comparison = CostComparison(
            comparison_id=self._generate_id(),
            timestamp=self._get_timestamp(),
            analysis_type=analysis_type,
            providers=providers,
            input_requirements=input_requirements,
            aws_results=results_by_provider.get('aws'),
            gcp_results=results_by_provider.get('gcp'),
            azure_results=results_by_provider.get('azure'),
            onpremise_results=results_by_provider.get('onpremise'),
            final_recommendation=recommendation,
            confidence_score=confidence,
            cost_savings_percentage=savings_pct,
            cost_savings_amount_usd=savings_amount,
            reasoning=reasoning,
            execution_time_ms=execution_time,
            session_id=session_id,
            user_id=user_id
        )
        
        data = asdict(comparison)
        data['_table_name'] = 'cost_comparisons'
        
        # Cloud Logging
        self._log_to_cloud_logging(data, 'cost-comparisons')
        
        # Pub/Sub
        self._send_to_pubsub(data, 'cost_comparison')
        
        # Buffer para BigQuery
        self._add_to_buffer(data)
        
        return comparison.comparison_id
    
    def log_agent_interaction(self, source_agent: str, target_agent: str,
                            interaction_type: str, message_content: Dict[str, Any],
                            response_time: int = None, success: bool = None,
                            session_id: str = None) -> str:
        """
        Log de interação entre agentes
        
        Returns:
            interaction_id: ID único da interação
        """
        interaction = AgentInteraction(
            interaction_id=self._generate_id(),
            timestamp=self._get_timestamp(),
            source_agent=source_agent,
            target_agent=target_agent,
            interaction_type=interaction_type,
            message_content=message_content,
            response_time_ms=response_time,
            success=success,
            session_id=session_id,
            correlation_id=self._generate_id()
        )
        
        data = asdict(interaction)
        data['_table_name'] = 'agent_interactions'
        
        # Cloud Logging
        self._log_to_cloud_logging(data, 'agent-interactions')
        
        # Pub/Sub
        self._send_to_pubsub(data, 'agent_interaction')
        
        # Buffer para BigQuery
        self._add_to_buffer(data)
        
        return interaction.interaction_id
    
    def log_mcp_server_call(self, server_type: str, method_name: str,
                          input_params: Dict[str, Any],
                          response_data: Dict[str, Any] = None,
                          response_time: int = None, status_code: int = None,
                          error_msg: str = None, cache_hit: bool = None,
                          api_cost: float = None, agent_id: str = None,
                          session_id: str = None) -> str:
        """
        Log de chamada para servidor MCP
        
        Returns:
            call_id: ID único da chamada
        """
        call = MCPServerCall(
            call_id=self._generate_id(),
            timestamp=self._get_timestamp(),
            server_type=server_type,
            method_name=method_name,
            input_parameters=input_params,
            response_data=response_data,
            response_time_ms=response_time,
            status_code=status_code,
            error_message=error_msg,
            cache_hit=cache_hit,
            api_cost_usd=api_cost,
            agent_id=agent_id,
            session_id=session_id
        )
        
        data = asdict(call)
        data['_table_name'] = 'mcp_server_calls'
        
        # Cloud Logging
        self._log_to_cloud_logging(data, 'mcp-server-calls')
        
        # Pub/Sub
        self._send_to_pubsub(data, 'mcp_call')
        
        # Buffer para BigQuery
        self._add_to_buffer(data)
        
        return call.call_id
    
    def log_user_feedback(self, session_id: str, comparison_id: str = None,
                         recommendation_followed: bool = None,
                         actual_savings: float = None,
                         satisfaction_score: int = None,
                         feedback_text: str = None,
                         improvement_suggestions: str = None,
                         user_id: str = None) -> str:
        """
        Log de feedback do usuário
        
        Returns:
            feedback_id: ID único do feedback
        """
        feedback_data = {
            'feedback_id': self._generate_id(),
            'timestamp': self._get_timestamp(),
            'session_id': session_id,
            'comparison_id': comparison_id,
            'recommendation_followed': recommendation_followed,
            'actual_savings_usd': actual_savings,
            'satisfaction_score': satisfaction_score,
            'feedback_text': feedback_text,
            'improvement_suggestions': improvement_suggestions,
            'user_id': user_id,
            '_table_name': 'user_feedback'
        }
        
        # Cloud Logging
        self._log_to_cloud_logging(feedback_data, 'user-feedback')
        
        # Pub/Sub
        self._send_to_pubsub(feedback_data, 'user_feedback')
        
        # Buffer para BigQuery
        self._add_to_buffer(feedback_data)
        
        return feedback_data['feedback_id']
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas internas do logger"""
        return {
            **self._metrics,
            'buffer_size': len(self._log_buffer),
            'time_since_last_flush': time.time() - self._metrics['last_flush']
        }
    
    def flush(self):
        """Força flush do buffer"""
        with self._buffer_lock:
            self._flush_buffer()
    
    def close(self):
        """Fecha o logger e faz flush final"""
        self.flush()
        
        # Fechar clientes
        if hasattr(self, 'publisher'):
            self.publisher.close()


# Instância global do logger
_global_logger = None

def get_logger() -> CloudCostLogger:
    """Obtém instância global do logger"""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = CloudCostLogger()
    
    return _global_logger

def initialize_logger(project_id: str = None, dataset_id: str = "agent_analytics"):
    """Inicializa logger global"""
    global _global_logger
    _global_logger = CloudCostLogger(project_id, dataset_id)
    return _global_logger

