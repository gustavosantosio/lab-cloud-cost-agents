"""
Cloud Cost Agent v2 - Master Operational Agent
Agente operacional que gerencia toda a cadeia de outros agentes do sistema
Compatível com Windows
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import os
import sys
from dataclasses import dataclass, asdict

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain.llms import OpenAI
from langchain.tools import Tool

# Cloud SDKs
import boto3
from google.cloud import monitoring_v3, bigquery
import requests

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_operational_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Solicitação de análise"""
    request_id: str
    user_id: str
    analysis_type: str  # 'compute', 'storage', 'comprehensive'
    requirements: Dict[str, Any]
    priority: str = 'MEDIUM'  # LOW, MEDIUM, HIGH, CRITICAL
    deadline: Optional[datetime] = None
    context: Dict[str, Any] = None


@dataclass
class AnalysisResult:
    """Resultado de análise"""
    request_id: str
    status: str  # 'COMPLETED', 'FAILED', 'IN_PROGRESS'
    results: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float
    execution_time_seconds: float
    agents_involved: List[str]
    timestamp: datetime


class CloudConnectionManager:
    """Gerenciador de conexões com provedores de nuvem"""
    
    def __init__(self):
        self.aws_session = None
        self.gcp_client = None
        self.connections_status = {}
    
    async def initialize_aws_connection(self) -> bool:
        """Inicializa conexão com AWS"""
        try:
            self.aws_session = boto3.Session(
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
            
            # Testar conexão
            sts = self.aws_session.client('sts')
            identity = sts.get_caller_identity()
            
            self.connections_status['aws'] = {
                'status': 'CONNECTED',
                'account_id': identity.get('Account'),
                'user_id': identity.get('UserId'),
                'arn': identity.get('Arn'),
                'connected_at': datetime.now().isoformat()
            }
            
            logger.info(f"AWS conectado: {identity.get('Account')}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar AWS: {e}")
            self.connections_status['aws'] = {
                'status': 'ERROR',
                'error': str(e),
                'attempted_at': datetime.now().isoformat()
            }
            return False
    
    async def initialize_gcp_connection(self) -> bool:
        """Inicializa conexão com GCP"""
        try:
            project_id = os.getenv('GCP_PROJECT_ID')
            if not project_id:
                raise ValueError("GCP_PROJECT_ID não configurado")
            
            # Testar conexão com BigQuery
            self.gcp_client = bigquery.Client(project=project_id)
            
            # Listar datasets para testar
            datasets = list(self.gcp_client.list_datasets())
            
            self.connections_status['gcp'] = {
                'status': 'CONNECTED',
                'project_id': project_id,
                'datasets_count': len(datasets),
                'connected_at': datetime.now().isoformat()
            }
            
            logger.info(f"GCP conectado: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar GCP: {e}")
            self.connections_status['gcp'] = {
                'status': 'ERROR',
                'error': str(e),
                'attempted_at': datetime.now().isoformat()
            }
            return False
    
    async def test_looker_connection(self) -> bool:
        """Testa conexão com Looker"""
        try:
            looker_url = os.getenv('LOOKER_BASE_URL')
            looker_client_id = os.getenv('LOOKER_CLIENT_ID')
            looker_client_secret = os.getenv('LOOKER_CLIENT_SECRET')
            
            if not all([looker_url, looker_client_id, looker_client_secret]):
                raise ValueError("Credenciais Looker não configuradas")
            
            # Testar autenticação
            auth_url = f"{looker_url}/api/4.0/login"
            auth_data = {
                'client_id': looker_client_id,
                'client_secret': looker_client_secret
            }
            
            response = requests.post(auth_url, data=auth_data, timeout=10)
            
            if response.status_code == 200:
                self.connections_status['looker'] = {
                    'status': 'CONNECTED',
                    'base_url': looker_url,
                    'connected_at': datetime.now().isoformat()
                }
                logger.info("Looker conectado com sucesso")
                return True
            else:
                raise Exception(f"Falha na autenticação: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao conectar Looker: {e}")
            self.connections_status['looker'] = {
                'status': 'ERROR',
                'error': str(e),
                'attempted_at': datetime.now().isoformat()
            }
            return False
    
    async def test_prometheus_connection(self) -> bool:
        """Testa conexão com Prometheus"""
        try:
            prometheus_url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
            
            # Testar endpoint de status
            response = requests.get(f"{prometheus_url}/api/v1/status/config", timeout=10)
            
            if response.status_code == 200:
                self.connections_status['prometheus'] = {
                    'status': 'CONNECTED',
                    'url': prometheus_url,
                    'connected_at': datetime.now().isoformat()
                }
                logger.info("Prometheus conectado com sucesso")
                return True
            else:
                raise Exception(f"Status não OK: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao conectar Prometheus: {e}")
            self.connections_status['prometheus'] = {
                'status': 'ERROR',
                'error': str(e),
                'attempted_at': datetime.now().isoformat()
            }
            return False
    
    async def test_grafana_connection(self) -> bool:
        """Testa conexão com Grafana"""
        try:
            grafana_url = os.getenv('GRAFANA_URL', 'http://localhost:3000')
            grafana_token = os.getenv('GRAFANA_API_TOKEN')
            
            headers = {}
            if grafana_token:
                headers['Authorization'] = f'Bearer {grafana_token}'
            
            # Testar endpoint de health
            response = requests.get(f"{grafana_url}/api/health", headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.connections_status['grafana'] = {
                    'status': 'CONNECTED',
                    'url': grafana_url,
                    'connected_at': datetime.now().isoformat()
                }
                logger.info("Grafana conectado com sucesso")
                return True
            else:
                raise Exception(f"Status não OK: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao conectar Grafana: {e}")
            self.connections_status['grafana'] = {
                'status': 'ERROR',
                'error': str(e),
                'attempted_at': datetime.now().isoformat()
            }
            return False
    
    async def initialize_all_connections(self) -> Dict[str, bool]:
        """Inicializa todas as conexões"""
        results = {}
        
        results['aws'] = await self.initialize_aws_connection()
        results['gcp'] = await self.initialize_gcp_connection()
        results['looker'] = await self.test_looker_connection()
        results['prometheus'] = await self.test_prometheus_connection()
        results['grafana'] = await self.test_grafana_connection()
        
        return results
    
    def get_connections_status(self) -> Dict[str, Any]:
        """Obtém status de todas as conexões"""
        return self.connections_status


class MasterOperationalAgent:
    """Agente operacional master que gerencia toda a cadeia de agentes"""
    
    def __init__(self):
        self.agent_name = "MasterOperationalAgent"
        self.connection_manager = CloudConnectionManager()
        self.active_analyses = {}
        self.agent_registry = {}
        
        # Configurar LLM
        self.llm = OpenAI(
            model_name="gpt-4",
            temperature=0.1,
            max_tokens=2000
        )
        
        # Criar agente CrewAI
        self.crew_agent = Agent(
            role='Master Operational Coordinator',
            goal='Coordenar e gerenciar todos os agentes do sistema de análise de custos de nuvem',
            backstory="""Você é o agente operacional master responsável por coordenar toda a cadeia de 
            agentes especializados em análise de custos de nuvem. Você tem acesso direto aos provedores 
            AWS, GCP, sistemas de monitoramento (Prometheus, Grafana), dashboards (Looker) e CrewAI.
            
            Suas responsabilidades incluem:
            - Orquestrar análises complexas entre múltiplos agentes
            - Gerenciar conexões com sistemas externos
            - Priorizar e distribuir tarefas
            - Consolidar resultados de diferentes especialistas
            - Garantir qualidade e consistência das análises
            - Monitorar performance do sistema
            """,
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        logger.info("Master Operational Agent inicializado")
    
    async def initialize_system(self) -> Dict[str, Any]:
        """Inicializa todo o sistema"""
        logger.info("Inicializando sistema completo...")
        
        start_time = datetime.now()
        
        # Inicializar conexões
        connection_results = await self.connection_manager.initialize_all_connections()
        
        # Registrar agentes disponíveis
        await self._register_available_agents()
        
        # Verificar saúde do sistema
        system_health = await self._check_system_health()
        
        initialization_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'INITIALIZED',
            'initialization_time_seconds': initialization_time,
            'connections': connection_results,
            'registered_agents': list(self.agent_registry.keys()),
            'system_health': system_health,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _register_available_agents(self):
        """Registra agentes disponíveis no sistema"""
        self.agent_registry = {
            'aws_specialist': {
                'name': 'AWS Specialist Agent',
                'capabilities': ['aws_pricing', 'ec2_analysis', 's3_analysis', 'cost_optimization'],
                'status': 'AVAILABLE',
                'mcp_server': 'aws_mcp_server'
            },
            'gcp_specialist': {
                'name': 'GCP Specialist Agent',
                'capabilities': ['gcp_pricing', 'compute_analysis', 'storage_analysis', 'recommendations'],
                'status': 'AVAILABLE',
                'mcp_server': 'gcp_mcp_server'
            },
            'sla_coordinator': {
                'name': 'SLA Coordinator Agent',
                'capabilities': ['sla_analysis', 'uptime_monitoring', 'penalty_calculation'],
                'status': 'AVAILABLE',
                'mcp_server': 'sla_analysis_mcp_server'
            },
            'cost_coordinator': {
                'name': 'Cost Coordinator Agent',
                'capabilities': ['cost_comparison', 'tco_analysis', 'optimization_recommendations'],
                'status': 'AVAILABLE',
                'mcp_server': 'multiple'
            },
            'compliance_coordinator': {
                'name': 'Compliance Coordinator Agent',
                'capabilities': ['compliance_check', 'security_analysis', 'certification_verification'],
                'status': 'AVAILABLE',
                'mcp_server': 'multiple'
            },
            'legal_coordinator': {
                'name': 'Legal Coordinator Agent',
                'capabilities': ['legal_analysis', 'lgpd_compliance', 'regulatory_guidance'],
                'status': 'AVAILABLE',
                'mcp_server': 'legal_rag_mcp_server'
            },
            'report_generator': {
                'name': 'Report Generator Agent',
                'capabilities': ['report_generation', 'data_visualization', 'executive_summary'],
                'status': 'AVAILABLE',
                'mcp_server': 'multiple'
            }
        }
        
        logger.info(f"Registrados {len(self.agent_registry)} agentes")
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Verifica saúde do sistema"""
        health_status = {
            'overall_status': 'HEALTHY',
            'components': {},
            'issues': [],
            'recommendations': []
        }
        
        # Verificar conexões
        connections = self.connection_manager.get_connections_status()
        for service, status in connections.items():
            if status.get('status') == 'ERROR':
                health_status['components'][service] = 'UNHEALTHY'
                health_status['issues'].append(f"{service} connection failed: {status.get('error')}")
            else:
                health_status['components'][service] = 'HEALTHY'
        
        # Verificar agentes
        available_agents = sum(1 for agent in self.agent_registry.values() 
                             if agent['status'] == 'AVAILABLE')
        total_agents = len(self.agent_registry)
        
        if available_agents < total_agents:
            health_status['issues'].append(f"Only {available_agents}/{total_agents} agents available")
        
        # Determinar status geral
        if health_status['issues']:
            if len(health_status['issues']) > 3:
                health_status['overall_status'] = 'CRITICAL'
            else:
                health_status['overall_status'] = 'DEGRADED'
        
        # Gerar recomendações
        if health_status['issues']:
            health_status['recommendations'].append("Check system logs for detailed error information")
            health_status['recommendations'].append("Verify all environment variables are properly set")
        
        return health_status
    
    async def process_analysis_request(self, request: AnalysisRequest) -> AnalysisResult:
        """Processa solicitação de análise"""
        logger.info(f"Processando análise: {request.request_id}")
        
        start_time = datetime.now()
        self.active_analyses[request.request_id] = {
            'status': 'IN_PROGRESS',
            'started_at': start_time,
            'request': request
        }
        
        try:
            # Determinar agentes necessários baseado no tipo de análise
            required_agents = self._determine_required_agents(request.analysis_type)
            
            # Criar plano de execução
            execution_plan = await self._create_execution_plan(request, required_agents)
            
            # Executar análise
            results = await self._execute_analysis_plan(execution_plan)
            
            # Consolidar resultados
            consolidated_results = await self._consolidate_results(results, request)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            analysis_result = AnalysisResult(
                request_id=request.request_id,
                status='COMPLETED',
                results=consolidated_results,
                recommendations=consolidated_results.get('recommendations', []),
                confidence_score=consolidated_results.get('confidence_score', 0.8),
                execution_time_seconds=execution_time,
                agents_involved=required_agents,
                timestamp=datetime.now()
            )
            
            self.active_analyses[request.request_id]['status'] = 'COMPLETED'
            self.active_analyses[request.request_id]['result'] = analysis_result
            
            logger.info(f"Análise concluída: {request.request_id} em {execution_time:.2f}s")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erro na análise {request.request_id}: {e}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            analysis_result = AnalysisResult(
                request_id=request.request_id,
                status='FAILED',
                results={'error': str(e)},
                recommendations=['Verifique os logs para mais detalhes', 'Tente novamente com parâmetros diferentes'],
                confidence_score=0.0,
                execution_time_seconds=execution_time,
                agents_involved=[],
                timestamp=datetime.now()
            )
            
            self.active_analyses[request.request_id]['status'] = 'FAILED'
            self.active_analyses[request.request_id]['result'] = analysis_result
            
            return analysis_result
    
    def _determine_required_agents(self, analysis_type: str) -> List[str]:
        """Determina agentes necessários baseado no tipo de análise"""
        agent_mapping = {
            'compute': ['aws_specialist', 'gcp_specialist', 'cost_coordinator', 'sla_coordinator'],
            'storage': ['aws_specialist', 'gcp_specialist', 'cost_coordinator'],
            'comprehensive': ['aws_specialist', 'gcp_specialist', 'sla_coordinator', 'cost_coordinator', 
                            'compliance_coordinator', 'legal_coordinator', 'report_generator'],
            'compliance': ['compliance_coordinator', 'legal_coordinator'],
            'legal': ['legal_coordinator'],
            'sla': ['sla_coordinator', 'aws_specialist', 'gcp_specialist']
        }
        
        return agent_mapping.get(analysis_type, ['cost_coordinator'])
    
    async def _create_execution_plan(self, request: AnalysisRequest, 
                                   required_agents: List[str]) -> Dict[str, Any]:
        """Cria plano de execução"""
        plan = {
            'request_id': request.request_id,
            'phases': [],
            'dependencies': {},
            'estimated_duration_minutes': 0
        }
        
        # Fase 1: Coleta de dados
        data_collection_agents = [agent for agent in required_agents 
                                if agent in ['aws_specialist', 'gcp_specialist']]
        
        if data_collection_agents:
            plan['phases'].append({
                'phase': 1,
                'name': 'Data Collection',
                'agents': data_collection_agents,
                'parallel': True,
                'estimated_minutes': 3
            })
            plan['estimated_duration_minutes'] += 3
        
        # Fase 2: Análise especializada
        analysis_agents = [agent for agent in required_agents 
                         if agent in ['sla_coordinator', 'compliance_coordinator', 'legal_coordinator']]
        
        if analysis_agents:
            plan['phases'].append({
                'phase': 2,
                'name': 'Specialized Analysis',
                'agents': analysis_agents,
                'parallel': True,
                'estimated_minutes': 5,
                'depends_on': [1] if data_collection_agents else []
            })
            plan['estimated_duration_minutes'] += 5
        
        # Fase 3: Coordenação e consolidação
        coordination_agents = [agent for agent in required_agents 
                             if agent in ['cost_coordinator']]
        
        if coordination_agents:
            plan['phases'].append({
                'phase': 3,
                'name': 'Cost Coordination',
                'agents': coordination_agents,
                'parallel': False,
                'estimated_minutes': 2,
                'depends_on': [1, 2] if len(plan['phases']) > 1 else [1]
            })
            plan['estimated_duration_minutes'] += 2
        
        # Fase 4: Geração de relatório
        if 'report_generator' in required_agents:
            plan['phases'].append({
                'phase': 4,
                'name': 'Report Generation',
                'agents': ['report_generator'],
                'parallel': False,
                'estimated_minutes': 2,
                'depends_on': list(range(1, len(plan['phases']) + 1))
            })
            plan['estimated_duration_minutes'] += 2
        
        return plan
    
    async def _execute_analysis_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Executa plano de análise"""
        results = {}
        
        for phase_info in plan['phases']:
            phase_num = phase_info['phase']
            agents = phase_info['agents']
            parallel = phase_info.get('parallel', False)
            
            logger.info(f"Executando fase {phase_num}: {phase_info['name']}")
            
            if parallel:
                # Executar agentes em paralelo
                tasks = []
                for agent_name in agents:
                    task = self._execute_agent_task(agent_name, plan['request_id'])
                    tasks.append(task)
                
                phase_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(phase_results):
                    agent_name = agents[i]
                    if isinstance(result, Exception):
                        logger.error(f"Erro no agente {agent_name}: {result}")
                        results[agent_name] = {'error': str(result)}
                    else:
                        results[agent_name] = result
            else:
                # Executar agentes sequencialmente
                for agent_name in agents:
                    try:
                        result = await self._execute_agent_task(agent_name, plan['request_id'])
                        results[agent_name] = result
                    except Exception as e:
                        logger.error(f"Erro no agente {agent_name}: {e}")
                        results[agent_name] = {'error': str(e)}
        
        return results
    
    async def _execute_agent_task(self, agent_name: str, request_id: str) -> Dict[str, Any]:
        """Executa tarefa de um agente específico"""
        # Simular execução de agente (na implementação real, chamaria o agente específico)
        await asyncio.sleep(1)  # Simular processamento
        
        # Retornar resultado simulado baseado no tipo de agente
        if agent_name == 'aws_specialist':
            return {
                'provider': 'aws',
                'monthly_cost': 1250.75,
                'performance_score': 88,
                'recommendations': ['Consider Reserved Instances', 'Optimize storage classes']
            }
        elif agent_name == 'gcp_specialist':
            return {
                'provider': 'gcp',
                'monthly_cost': 1180.50,
                'performance_score': 85,
                'recommendations': ['Use Sustained Use Discounts', 'Consider Preemptible instances']
            }
        elif agent_name == 'sla_coordinator':
            return {
                'sla_analysis': {
                    'aws_uptime': 99.99,
                    'gcp_uptime': 99.95,
                    'recommendation': 'AWS offers better SLA for critical workloads'
                }
            }
        elif agent_name == 'cost_coordinator':
            return {
                'cost_comparison': {
                    'winner': 'gcp',
                    'savings_amount': 70.25,
                    'savings_percentage': 5.6,
                    'confidence': 0.87
                }
            }
        else:
            return {
                'agent': agent_name,
                'status': 'completed',
                'data': f'Results from {agent_name}'
            }
    
    async def _consolidate_results(self, results: Dict[str, Any], 
                                 request: AnalysisRequest) -> Dict[str, Any]:
        """Consolida resultados de todos os agentes"""
        consolidated = {
            'request_id': request.request_id,
            'analysis_type': request.analysis_type,
            'summary': {},
            'detailed_results': results,
            'recommendations': [],
            'confidence_score': 0.0,
            'metadata': {
                'agents_executed': len(results),
                'successful_agents': len([r for r in results.values() if 'error' not in r]),
                'failed_agents': len([r for r in results.values() if 'error' in r])
            }
        }
        
        # Consolidar custos se disponível
        costs = {}
        for agent_name, result in results.items():
            if isinstance(result, dict) and 'monthly_cost' in result:
                provider = result.get('provider', agent_name.replace('_specialist', ''))
                costs[provider] = result['monthly_cost']
        
        if costs:
            consolidated['summary']['costs'] = costs
            consolidated['summary']['cheapest_provider'] = min(costs, key=costs.get)
            consolidated['summary']['most_expensive_provider'] = max(costs, key=costs.get)
            
            if len(costs) > 1:
                cost_values = list(costs.values())
                savings = max(cost_values) - min(cost_values)
                consolidated['summary']['potential_savings'] = savings
        
        # Consolidar recomendações
        all_recommendations = []
        for result in results.values():
            if isinstance(result, dict) and 'recommendations' in result:
                all_recommendations.extend(result['recommendations'])
        
        consolidated['recommendations'] = list(set(all_recommendations))
        
        # Calcular score de confiança
        successful_agents = consolidated['metadata']['successful_agents']
        total_agents = consolidated['metadata']['agents_executed']
        
        if total_agents > 0:
            base_confidence = successful_agents / total_agents
            
            # Ajustar baseado na qualidade dos dados
            if costs:
                base_confidence += 0.1  # Bonus por ter dados de custo
            
            consolidated['confidence_score'] = min(base_confidence, 0.95)
        
        return consolidated
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtém status completo do sistema"""
        return {
            'agent_name': self.agent_name,
            'status': 'OPERATIONAL',
            'connections': self.connection_manager.get_connections_status(),
            'registered_agents': self.agent_registry,
            'active_analyses': len(self.active_analyses),
            'system_health': await self._check_system_health(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Encerra o agente de forma limpa"""
        logger.info("Encerrando Master Operational Agent...")
        
        # Aguardar análises ativas terminarem
        if self.active_analyses:
            logger.info(f"Aguardando {len(self.active_analyses)} análises ativas...")
            # Na implementação real, aguardaria as análises terminarem
        
        logger.info("Master Operational Agent encerrado")


# Exemplo de uso
async def main():
    """Função principal para teste"""
    master_agent = MasterOperationalAgent()
    
    # Inicializar sistema
    init_result = await master_agent.initialize_system()
    print("Inicialização:", json.dumps(init_result, indent=2, default=str))
    
    # Criar solicitação de análise
    request = AnalysisRequest(
        request_id="test_001",
        user_id="user_123",
        analysis_type="comprehensive",
        requirements={
            "workload_type": "web_application",
            "expected_users": 10000,
            "storage_gb": 500,
            "backup_required": True
        },
        priority="HIGH"
    )
    
    # Processar análise
    result = await master_agent.process_analysis_request(request)
    print("Resultado:", json.dumps(asdict(result), indent=2, default=str))
    
    # Obter status do sistema
    status = await master_agent.get_system_status()
    print("Status:", json.dumps(status, indent=2, default=str))
    
    # Encerrar
    await master_agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

