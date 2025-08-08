"""
Cloud Cost Agent - Decoradores para Logging Automático
Instrumentação automática de agentes e funções MCP
"""

import time
import functools
import inspect
from typing import Dict, Any, Callable, Optional
from .gcp_logger import get_logger


def log_agent_execution(agent_type: str, task_type: str, 
                       auto_session: bool = True):
    """
    Decorador para log automático de execução de agentes
    
    Args:
        agent_type: Tipo do agente (aws_specialist, gcp_specialist, etc.)
        task_type: Tipo da tarefa (cost_analysis, sla_check, etc.)
        auto_session: Se deve extrair session_id automaticamente dos kwargs
    
    Usage:
        @log_agent_execution('aws_specialist', 'cost_analysis')
        def analyze_aws_costs(instance_type, region, session_id=None):
            # Código do agente
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            agent_name = func.__name__
            
            # Extrair session_id e user_id dos kwargs se disponível
            session_id = kwargs.get('session_id') if auto_session else None
            user_id = kwargs.get('user_id') if auto_session else None
            
            # Usar context manager para log automático
            with logger.log_agent_execution_context(
                agent_type=agent_type,
                agent_name=agent_name,
                task_type=task_type,
                session_id=session_id,
                user_id=user_id,
                **_extract_serializable_kwargs(kwargs)
            ) as ctx:
                result = func(*args, **kwargs)
                ctx.set_result(result)
                return result
                
        return wrapper
    return decorator


def log_mcp_call(server_type: str, estimate_cost: bool = False):
    """
    Decorador para log de chamadas MCP
    
    Args:
        server_type: Tipo do servidor MCP (aws_pricing, gcp_pricing, etc.)
        estimate_cost: Se deve estimar custo da API
    
    Usage:
        @log_mcp_call('aws_pricing', estimate_cost=True)
        def get_ec2_pricing(instance_type, region):
            # Chamada para API AWS
            return pricing_data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.time()
            method_name = func.__name__
            
            # Extrair IDs dos kwargs
            agent_id = kwargs.get('agent_id')
            session_id = kwargs.get('session_id')
            
            try:
                result = func(*args, **kwargs)
                response_time = int((time.time() - start_time) * 1000)
                
                # Estimar custo se solicitado
                api_cost = _estimate_api_cost(server_type, method_name, kwargs) if estimate_cost else None
                
                logger.log_mcp_server_call(
                    server_type=server_type,
                    method_name=method_name,
                    input_params=_extract_serializable_kwargs(kwargs),
                    response_data=_serialize_response(result),
                    response_time=response_time,
                    status_code=200,
                    error_msg=None,
                    cache_hit=_check_cache_hit(kwargs),
                    api_cost=api_cost,
                    agent_id=agent_id,
                    session_id=session_id
                )
                
                return result
                
            except Exception as e:
                response_time = int((time.time() - start_time) * 1000)
                
                logger.log_mcp_server_call(
                    server_type=server_type,
                    method_name=method_name,
                    input_params=_extract_serializable_kwargs(kwargs),
                    response_data=None,
                    response_time=response_time,
                    status_code=500,
                    error_msg=str(e),
                    cache_hit=False,
                    api_cost=0.0,
                    agent_id=agent_id,
                    session_id=session_id
                )
                
                raise
                
        return wrapper
    return decorator


def log_agent_interaction(interaction_type: str = 'collaboration'):
    """
    Decorador para log de interações entre agentes
    
    Args:
        interaction_type: Tipo de interação (request, response, collaboration)
    
    Usage:
        @log_agent_interaction('request')
        def request_aws_analysis(self, target_agent, requirements):
            # Código de interação
            return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            logger = get_logger()
            start_time = time.time()
            
            # Extrair informações do agente
            source_agent = getattr(self, 'agent_name', self.__class__.__name__)
            target_agent = kwargs.get('target_agent') or (args[0] if args else None)
            session_id = kwargs.get('session_id')
            
            try:
                result = func(self, *args, **kwargs)
                response_time = int((time.time() - start_time) * 1000)
                
                logger.log_agent_interaction(
                    source_agent=source_agent,
                    target_agent=str(target_agent) if target_agent else None,
                    interaction_type=interaction_type,
                    message_content=_extract_serializable_kwargs(kwargs),
                    response_time=response_time,
                    success=True,
                    session_id=session_id
                )
                
                return result
                
            except Exception as e:
                response_time = int((time.time() - start_time) * 1000)
                
                logger.log_agent_interaction(
                    source_agent=source_agent,
                    target_agent=str(target_agent) if target_agent else None,
                    interaction_type=interaction_type,
                    message_content=_extract_serializable_kwargs(kwargs),
                    response_time=response_time,
                    success=False,
                    session_id=session_id
                )
                
                raise
                
        return wrapper
    return decorator


def log_cost_comparison_result(analysis_type: str):
    """
    Decorador para log de resultados de comparação de custos
    
    Args:
        analysis_type: Tipo de análise (compute, storage, comprehensive)
    
    Usage:
        @log_cost_comparison_result('comprehensive')
        def perform_comprehensive_analysis(self, requirements, session_id=None):
            # Análise completa
            return {
                'providers': ['aws', 'gcp'],
                'results_by_provider': {...},
                'recommendation': 'aws',
                'confidence': 0.85,
                'savings_pct': 25.5,
                'savings_amount': 1200.0,
                'reasoning': '...',
                'execution_time': 5000
            }
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.time()
            
            result = func(*args, **kwargs)
            execution_time = int((time.time() - start_time) * 1000)
            
            # Extrair dados do resultado
            if isinstance(result, dict):
                providers = result.get('providers', [])
                results_by_provider = result.get('results_by_provider', {})
                recommendation = result.get('recommendation', '')
                confidence = result.get('confidence', 0.0)
                savings_pct = result.get('savings_pct', 0.0)
                savings_amount = result.get('savings_amount', 0.0)
                reasoning = result.get('reasoning', '')
                
                # Extrair requirements dos kwargs
                input_requirements = kwargs.get('requirements', {})
                session_id = kwargs.get('session_id')
                user_id = kwargs.get('user_id')
                
                logger.log_cost_comparison(
                    analysis_type=analysis_type,
                    providers=providers,
                    input_requirements=input_requirements,
                    results_by_provider=results_by_provider,
                    recommendation=recommendation,
                    confidence=confidence,
                    savings_pct=savings_pct,
                    savings_amount=savings_amount,
                    reasoning=reasoning,
                    execution_time=execution_time,
                    session_id=session_id,
                    user_id=user_id
                )
            
            return result
                
        return wrapper
    return decorator


def log_performance_metrics(track_memory: bool = True, track_cpu: bool = True):
    """
    Decorador para tracking de métricas de performance
    
    Args:
        track_memory: Se deve trackear uso de memória
        track_cpu: Se deve trackear uso de CPU
    
    Usage:
        @log_performance_metrics(track_memory=True, track_cpu=True)
        def heavy_computation():
            # Código pesado
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import psutil
            import threading
            
            # Métricas iniciais
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024 if track_memory else None
            
            # Tracking de CPU em thread separada
            cpu_samples = []
            stop_cpu_tracking = threading.Event()
            
            def track_cpu():
                while not stop_cpu_tracking.is_set():
                    cpu_samples.append(process.cpu_percent())
                    time.sleep(0.1)
            
            cpu_thread = None
            if track_cpu:
                cpu_thread = threading.Thread(target=track_cpu)
                cpu_thread.start()
            
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Parar tracking de CPU
                if cpu_thread:
                    stop_cpu_tracking.set()
                    cpu_thread.join()
                
                # Métricas finais
                final_memory = process.memory_info().rss / 1024 / 1024 if track_memory else None
                avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else None
                
                # Log das métricas
                logger = get_logger()
                logger.local_logger.info(
                    f"Performance metrics for {func.__name__}: "
                    f"execution_time={execution_time:.3f}s, "
                    f"memory_delta={final_memory - initial_memory if initial_memory and final_memory else 'N/A'}MB, "
                    f"avg_cpu={avg_cpu:.1f}%" if avg_cpu else "avg_cpu=N/A"
                )
                
                return result
                
            except Exception as e:
                # Parar tracking mesmo em caso de erro
                if cpu_thread:
                    stop_cpu_tracking.set()
                    cpu_thread.join()
                raise
                
        return wrapper
    return decorator


# Funções auxiliares

def _extract_serializable_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai apenas kwargs serializáveis para JSON"""
    serializable = {}
    
    for key, value in kwargs.items():
        try:
            # Tentar serializar para verificar se é válido
            import json
            json.dumps(value, default=str)
            serializable[key] = value
        except (TypeError, ValueError):
            # Se não conseguir serializar, converter para string
            serializable[key] = str(value)
    
    return serializable


def _serialize_response(response: Any) -> Dict[str, Any]:
    """Serializa resposta para log"""
    if response is None:
        return None
    
    try:
        import json
        # Tentar serializar diretamente
        json.dumps(response, default=str)
        return response if isinstance(response, dict) else {'result': response}
    except (TypeError, ValueError):
        # Se não conseguir, converter para string
        return {'result': str(response)}


def _check_cache_hit(kwargs: Dict[str, Any]) -> bool:
    """Verifica se foi cache hit (implementação básica)"""
    # Implementar lógica de cache específica
    return kwargs.get('_cache_hit', False)


def _estimate_api_cost(server_type: str, method_name: str, kwargs: Dict[str, Any]) -> float:
    """Estima custo da chamada de API"""
    # Tabela de custos estimados por tipo de chamada
    cost_table = {
        'aws_pricing': {
            'get_ec2_pricing': 0.001,
            'get_s3_pricing': 0.0005,
            'get_rds_pricing': 0.002,
        },
        'gcp_pricing': {
            'get_compute_pricing': 0.001,
            'get_storage_pricing': 0.0005,
            'get_sql_pricing': 0.002,
        },
        'azure_pricing': {
            'get_vm_pricing': 0.001,
            'get_blob_pricing': 0.0005,
            'get_sql_pricing': 0.002,
        }
    }
    
    return cost_table.get(server_type, {}).get(method_name, 0.0)


# Decorador composto para agentes completos

def log_complete_agent(agent_type: str, task_type: str, 
                      server_type: str = None,
                      track_performance: bool = True):
    """
    Decorador composto que combina logging de execução, MCP e performance
    
    Usage:
        @log_complete_agent('aws_specialist', 'cost_analysis', 'aws_pricing')
        def analyze_aws_costs(instance_type, region):
            # Código completo do agente
            return result
    """
    def decorator(func: Callable) -> Callable:
        # Aplicar decoradores em sequência
        decorated_func = func
        
        if track_performance:
            decorated_func = log_performance_metrics()(decorated_func)
        
        if server_type:
            decorated_func = log_mcp_call(server_type, estimate_cost=True)(decorated_func)
        
        decorated_func = log_agent_execution(agent_type, task_type)(decorated_func)
        
        return decorated_func
    
    return decorator

