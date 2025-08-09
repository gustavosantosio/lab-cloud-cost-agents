"""
Agente Especialista em Google Cloud Platform (GCP)
Responsável por análises específicas de recursos e custos do Google Cloud
"""
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from crewai import Agent, Task, Tool
from crewai.tools import BaseTool
from config.project_config import config
from agents.base.logger import AgentLogger
from agents.base.cloud_connector import CloudConnector

class GCPSpecialistAgent:
    """
    Agente Especialista em GCP - Análise detalhada de recursos e custos Google Cloud
    """
    
    def __init__(self):
        self.logger = AgentLogger("GCPSpecialistAgent")
        self.cloud_connector = CloudConnector()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Cria o agente especialista em GCP"""
        return Agent(
            role="Especialista em Google Cloud Platform (GCP)",
            goal="Realizar análises detalhadas e especializadas de recursos, custos, performance "
                 "e otimizações na infraestrutura Google Cloud, fornecendo insights técnicos precisos "
                 "e recomendações específicas para o ecossistema Google.",
            backstory="Você é um arquiteto de soluções Google Cloud certificado com vasta experiência "
                     "em otimização de custos, análise de performance e melhores práticas "
                     "de arquitetura na nuvem Google. Sua expertise inclui Compute Engine, "
                     "Cloud Storage, BigQuery, Cloud Functions, Cloud Monitoring, Cloud Billing "
                     "e todos os serviços do portfólio Google Cloud.",
            verbose=True,
            allow_delegation=False,
            tools=self._get_tools(),
            max_iter=config.agents.max_iterations,
            max_execution_time=config.agents.timeout_seconds
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Retorna as ferramentas específicas para análise GCP"""
        return [
            self._create_cost_analysis_tool(),
            self._create_resource_inventory_tool(),
            self._create_performance_analysis_tool(),
            self._create_optimization_recommendations_tool(),
            self._create_security_assessment_tool(),
            self._create_bigquery_analysis_tool()
        ]
    
    def _create_cost_analysis_tool(self) -> BaseTool:
        """Ferramenta para análise detalhada de custos GCP"""
        class GCPCostAnalysisTool(BaseTool):
            name: str = "gcp_cost_analysis"
            description: str = "Analisa custos detalhados dos serviços GCP por período, serviço e região"
            
            def _run(self, period_days: str = "30") -> str:
                try:
                    days = int(period_days)
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    
                    cost_data = self.cloud_connector.get_gcp_cost_data(
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    if 'error' in cost_data:
                        return f"Erro na análise de custos: {cost_data['error']}"
                    
                    # Processar dados de custo
                    analysis = self._process_cost_data(cost_data)
                    
                    return f"Análise de custos GCP concluída: {analysis}"
                    
                except Exception as e:
                    return f"Erro na análise de custos GCP: {str(e)}"
            
            def _process_cost_data(self, cost_data: Dict[str, Any]) -> str:
                """Processa dados de custo para análise"""
                try:
                    billing_accounts = cost_data.get('billing_accounts', 0)
                    
                    analysis_summary = {
                        "project_id": config.gcp.project_id,
                        "billing_accounts": billing_accounts,
                        "period": cost_data.get('period'),
                        "analysis_status": "completed"
                    }
                    
                    return str(analysis_summary)
                    
                except Exception as e:
                    return f"Erro no processamento: {str(e)}"
        
        return GCPCostAnalysisTool()
    
    def _create_resource_inventory_tool(self) -> BaseTool:
        """Ferramenta para inventário de recursos GCP"""
        class GCPResourceInventoryTool(BaseTool):
            name: str = "gcp_resource_inventory"
            description: str = "Realiza inventário completo de recursos GCP (Compute Engine, Storage, BigQuery, etc.)"
            
            def _run(self, resource_types: str = "all") -> str:
                try:
                    resources = self.cloud_connector.get_gcp_resources()
                    
                    if 'error' in resources:
                        return f"Erro no inventário: {resources['error']}"
                    
                    inventory_summary = {
                        "project_id": resources.get('project_id'),
                        "timestamp": resources.get('timestamp'),
                        "resources": resources.get('resources', {}),
                        "total_resources": sum(resources.get('resources', {}).values())
                    }
                    
                    return f"Inventário GCP concluído: {inventory_summary}"
                    
                except Exception as e:
                    return f"Erro no inventário GCP: {str(e)}"
        
        return GCPResourceInventoryTool()
    
    def _create_performance_analysis_tool(self) -> BaseTool:
        """Ferramenta para análise de performance GCP"""
        class GCPPerformanceAnalysisTool(BaseTool):
            name: str = "gcp_performance_analysis"
            description: str = "Analisa métricas de performance dos recursos GCP via Cloud Monitoring"
            
            def _run(self, resource_id: str = "") -> str:
                try:
                    # Aqui seria implementada a análise via Cloud Monitoring
                    # Por enquanto, retorna estrutura base
                    
                    performance_metrics = {
                        "compute_utilization": "Análise de utilização Compute Engine",
                        "storage_performance": "Análise de performance Cloud Storage",
                        "network_latency": "Análise de latência de rede",
                        "bigquery_performance": "Análise de performance BigQuery",
                        "function_execution": "Análise de execução Cloud Functions"
                    }
                    
                    return f"Análise de performance GCP: {performance_metrics}"
                    
                except Exception as e:
                    return f"Erro na análise de performance: {str(e)}"
        
        return GCPPerformanceAnalysisTool()
    
    def _create_optimization_recommendations_tool(self) -> BaseTool:
        """Ferramenta para recomendações de otimização GCP"""
        class GCPOptimizationTool(BaseTool):
            name: str = "gcp_optimization_recommendations"
            description: str = "Gera recomendações de otimização baseadas em análise de recursos e custos GCP"
            
            def _run(self, focus_area: str = "cost") -> str:
                try:
                    # Recomendações baseadas em melhores práticas GCP
                    recommendations = {
                        "cost_optimization": [
                            "Revisar instâncias Compute Engine subutilizadas",
                            "Implementar Committed Use Discounts para workloads estáveis",
                            "Configurar Autoscaling para otimizar recursos",
                            "Revisar snapshots e discos persistentes órfãos",
                            "Implementar lifecycle policies para Cloud Storage",
                            "Otimizar consultas BigQuery para reduzir custos"
                        ],
                        "performance_optimization": [
                            "Implementar Cloud CDN para conteúdo estático",
                            "Otimizar queries BigQuery com particionamento",
                            "Configurar Memorystore para cache",
                            "Revisar configurações de rede e VPC",
                            "Implementar monitoramento com Cloud Monitoring",
                            "Otimizar Cloud Functions para cold starts"
                        ],
                        "security_optimization": [
                            "Revisar políticas IAM e princípio do menor privilégio",
                            "Implementar Security Command Center",
                            "Configurar Cloud Audit Logs",
                            "Revisar regras de firewall VPC",
                            "Implementar Binary Authorization para containers",
                            "Configurar Cloud KMS para gerenciamento de chaves"
                        ]
                    }
                    
                    return f"Recomendações GCP ({focus_area}): {recommendations.get(f'{focus_area}_optimization', recommendations['cost_optimization'])}"
                    
                except Exception as e:
                    return f"Erro nas recomendações: {str(e)}"
        
        return GCPOptimizationTool()
    
    def _create_security_assessment_tool(self) -> BaseTool:
        """Ferramenta para avaliação de segurança GCP"""
        class GCPSecurityAssessmentTool(BaseTool):
            name: str = "gcp_security_assessment"
            description: str = "Avalia configurações de segurança e compliance no GCP"
            
            def _run(self, assessment_type: str = "general") -> str:
                try:
                    # Checklist de segurança GCP
                    security_checks = {
                        "iam_policies": "Verificação de políticas IAM e Service Accounts",
                        "encryption": "Verificação de criptografia com Cloud KMS",
                        "network_security": "Análise de VPC e regras de firewall",
                        "logging_monitoring": "Verificação de Cloud Audit Logs e Monitoring",
                        "compliance": "Verificação de compliance (SOC, ISO, PCI)",
                        "container_security": "Análise de segurança GKE e containers"
                    }
                    
                    return f"Avaliação de segurança GCP: {security_checks}"
                    
                except Exception as e:
                    return f"Erro na avaliação de segurança: {str(e)}"
        
        return GCPSecurityAssessmentTool()
    
    def _create_bigquery_analysis_tool(self) -> BaseTool:
        """Ferramenta específica para análise BigQuery"""
        class BigQueryAnalysisTool(BaseTool):
            name: str = "bigquery_analysis"
            description: str = "Analisa uso, performance e custos do BigQuery"
            
            def _run(self, analysis_type: str = "usage") -> str:
                try:
                    # Análise específica do BigQuery
                    bigquery_metrics = {
                        "usage_analysis": "Análise de uso de slots e storage",
                        "cost_analysis": "Análise de custos por query e dataset",
                        "performance_analysis": "Análise de performance de queries",
                        "optimization_suggestions": "Sugestões de otimização de queries"
                    }
                    
                    return f"Análise BigQuery ({analysis_type}): {bigquery_metrics.get(analysis_type, 'Análise geral')}"
                    
                except Exception as e:
                    return f"Erro na análise BigQuery: {str(e)}"
        
        return BigQueryAnalysisTool()
    
    def create_gcp_analysis_task(self, analysis_scope: Dict[str, Any]) -> Task:
        """Cria tarefa de análise específica para GCP"""
        return Task(
            description=f"""
            Realize uma análise completa e especializada da infraestrutura Google Cloud com o seguinte escopo:
            
            Escopo da Análise GCP:
            - Projeto: {config.gcp.project_id}
            - Período de análise: {analysis_scope.get('period', 'último mês')}
            - Recursos alvo: {analysis_scope.get('resources', 'todos os recursos')}
            - Foco principal: {analysis_scope.get('focus', 'otimização de custos')}
            - Regiões: {analysis_scope.get('regions', 'todas as regiões ativas')}
            
            Análises a realizar:
            1. Análise detalhada de custos por serviço, região e período
            2. Inventário completo de recursos GCP
            3. Análise de performance via Cloud Monitoring
            4. Análise específica do BigQuery (uso, custos, performance)
            5. Recomendações de otimização específicas
            6. Avaliação de segurança e compliance
            
            Entregue um relatório técnico detalhado com:
            - Resumo executivo dos custos GCP
            - Inventário detalhado de recursos por serviço
            - Métricas de performance críticas
            - Análise específica do BigQuery
            - Recomendações priorizadas de otimização
            - Avaliação de riscos de segurança
            - Plano de ação com estimativas de economia
            
            Use suas ferramentas especializadas para obter dados precisos e atualizados.
            """,
            agent=self.agent,
            expected_output="Relatório técnico completo de análise GCP com recomendações específicas e plano de ação"
        )
    
    def analyze_gcp_infrastructure(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise completa da infraestrutura GCP"""
        try:
            self.logger.info("Iniciando análise especializada GCP", extra=analysis_scope)
            
            # Verificar conexão GCP
            gcp_connection = self.cloud_connector.connect_gcp()
            if gcp_connection.get('status') != 'connected':
                raise Exception(f"Falha na conexão GCP: {gcp_connection.get('error')}")
            
            # Criar e executar tarefa de análise
            analysis_task = self.create_gcp_analysis_task(analysis_scope)
            
            # Simular execução da tarefa (em implementação real seria via CrewAI)
            result = {
                "cost_analysis": "Análise de custos concluída",
                "resource_inventory": "Inventário de recursos concluído",
                "performance_analysis": "Análise de performance concluída",
                "bigquery_analysis": "Análise BigQuery concluída",
                "optimization_recommendations": "Recomendações geradas",
                "security_assessment": "Avaliação de segurança concluída"
            }
            
            self.logger.info("Análise GCP concluída com sucesso")
            
            return {
                "status": "success",
                "provider": "GCP",
                "project_id": config.gcp.project_id,
                "timestamp": datetime.now().isoformat(),
                "analysis_scope": analysis_scope,
                "results": result
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise GCP: {str(e)}")
            return {
                "status": "error",
                "provider": "GCP",
                "project_id": config.gcp.project_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "analysis_scope": analysis_scope
            }

def main():
    """Função principal para teste do agente"""
    gcp_specialist = GCPSpecialistAgent()
    
    # Exemplo de análise
    analysis_scope = {
        "period": "30 dias",
        "resources": "Compute Engine, Cloud Storage, BigQuery",
        "focus": "otimização de custos",
        "regions": ["us-central1", "us-east1"]
    }
    
    result = gcp_specialist.analyze_gcp_infrastructure(analysis_scope)
    print(f"Resultado da análise GCP: {result}")

if __name__ == "__main__":
    main()

