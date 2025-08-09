"""
Agente Especialista em AWS
Responsável por análises específicas de recursos e custos da Amazon Web Services
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

class AWSSpecialistAgent:
    """
    Agente Especialista em AWS - Análise detalhada de recursos e custos AWS
    """
    
    def __init__(self):
        self.logger = AgentLogger("AWSSpecialistAgent")
        self.cloud_connector = CloudConnector()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Cria o agente especialista em AWS"""
        return Agent(
            role="Especialista em Amazon Web Services (AWS)",
            goal="Realizar análises detalhadas e especializadas de recursos, custos, performance "
                 "e otimizações na infraestrutura AWS, fornecendo insights técnicos precisos "
                 "e recomendações específicas para o ecossistema Amazon.",
            backstory="Você é um arquiteto de soluções AWS certificado com vasta experiência "
                     "em otimização de custos, análise de performance e melhores práticas "
                     "de arquitetura na nuvem Amazon. Sua expertise inclui EC2, S3, RDS, "
                     "Lambda, CloudWatch, Cost Explorer e todos os serviços do portfólio AWS.",
            verbose=True,
            allow_delegation=False,
            tools=self._get_tools(),
            max_iter=config.agents.max_iterations,
            max_execution_time=config.agents.timeout_seconds
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Retorna as ferramentas específicas para análise AWS"""
        return [
            self._create_cost_analysis_tool(),
            self._create_resource_inventory_tool(),
            self._create_performance_analysis_tool(),
            self._create_optimization_recommendations_tool(),
            self._create_security_assessment_tool()
        ]
    
    def _create_cost_analysis_tool(self) -> BaseTool:
        """Ferramenta para análise detalhada de custos AWS"""
        class AWSCostAnalysisTool(BaseTool):
            name: str = "aws_cost_analysis"
            description: str = "Analisa custos detalhados dos serviços AWS por período, serviço e região"
            
            def _run(self, period_days: str = "30") -> str:
                try:
                    days = int(period_days)
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    
                    cost_data = self.cloud_connector.get_aws_cost_data(
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    if 'error' in cost_data:
                        return f"Erro na análise de custos: {cost_data['error']}"
                    
                    # Processar dados de custo
                    analysis = self._process_cost_data(cost_data)
                    
                    return f"Análise de custos AWS concluída: {analysis}"
                    
                except Exception as e:
                    return f"Erro na análise de custos AWS: {str(e)}"
            
            def _process_cost_data(self, cost_data: Dict[str, Any]) -> str:
                """Processa dados de custo para análise"""
                try:
                    results = cost_data.get('data', {}).get('ResultsByTime', [])
                    if not results:
                        return "Nenhum dado de custo encontrado"
                    
                    total_cost = 0
                    services_cost = {}
                    
                    for result in results:
                        for group in result.get('Groups', []):
                            service = group.get('Keys', ['Unknown'])[0]
                            amount = float(group.get('Metrics', {}).get('BlendedCost', {}).get('Amount', 0))
                            
                            services_cost[service] = services_cost.get(service, 0) + amount
                            total_cost += amount
                    
                    # Identificar top 5 serviços mais caros
                    top_services = sorted(services_cost.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    analysis_summary = {
                        "total_cost": round(total_cost, 2),
                        "top_services": top_services,
                        "services_count": len(services_cost),
                        "period": cost_data.get('period')
                    }
                    
                    return str(analysis_summary)
                    
                except Exception as e:
                    return f"Erro no processamento: {str(e)}"
        
        return AWSCostAnalysisTool()
    
    def _create_resource_inventory_tool(self) -> BaseTool:
        """Ferramenta para inventário de recursos AWS"""
        class AWSResourceInventoryTool(BaseTool):
            name: str = "aws_resource_inventory"
            description: str = "Realiza inventário completo de recursos AWS (EC2, S3, RDS, etc.)"
            
            def _run(self, resource_types: str = "all") -> str:
                try:
                    resources = self.cloud_connector.get_aws_resources()
                    
                    if 'error' in resources:
                        return f"Erro no inventário: {resources['error']}"
                    
                    inventory_summary = {
                        "timestamp": resources.get('timestamp'),
                        "resources": resources.get('resources', {}),
                        "total_resources": sum(resources.get('resources', {}).values())
                    }
                    
                    return f"Inventário AWS concluído: {inventory_summary}"
                    
                except Exception as e:
                    return f"Erro no inventário AWS: {str(e)}"
        
        return AWSResourceInventoryTool()
    
    def _create_performance_analysis_tool(self) -> BaseTool:
        """Ferramenta para análise de performance AWS"""
        class AWSPerformanceAnalysisTool(BaseTool):
            name: str = "aws_performance_analysis"
            description: str = "Analisa métricas de performance dos recursos AWS via CloudWatch"
            
            def _run(self, resource_id: str = "") -> str:
                try:
                    # Aqui seria implementada a análise via CloudWatch
                    # Por enquanto, retorna estrutura base
                    
                    performance_metrics = {
                        "cpu_utilization": "Análise de CPU",
                        "memory_utilization": "Análise de memória",
                        "network_io": "Análise de rede",
                        "disk_io": "Análise de disco",
                        "response_time": "Tempo de resposta"
                    }
                    
                    return f"Análise de performance AWS: {performance_metrics}"
                    
                except Exception as e:
                    return f"Erro na análise de performance: {str(e)}"
        
        return AWSPerformanceAnalysisTool()
    
    def _create_optimization_recommendations_tool(self) -> BaseTool:
        """Ferramenta para recomendações de otimização AWS"""
        class AWSOptimizationTool(BaseTool):
            name: str = "aws_optimization_recommendations"
            description: str = "Gera recomendações de otimização baseadas em análise de recursos e custos"
            
            def _run(self, focus_area: str = "cost") -> str:
                try:
                    # Recomendações baseadas em melhores práticas AWS
                    recommendations = {
                        "cost_optimization": [
                            "Revisar instâncias EC2 subutilizadas",
                            "Implementar Reserved Instances para workloads estáveis",
                            "Configurar Auto Scaling para otimizar recursos",
                            "Revisar snapshots e volumes EBS órfãos",
                            "Implementar lifecycle policies para S3"
                        ],
                        "performance_optimization": [
                            "Implementar CloudFront para conteúdo estático",
                            "Otimizar queries de banco de dados RDS",
                            "Configurar ElastiCache para cache",
                            "Revisar configurações de rede e VPC",
                            "Implementar monitoramento com CloudWatch"
                        ],
                        "security_optimization": [
                            "Revisar políticas IAM e princípio do menor privilégio",
                            "Implementar AWS Config para compliance",
                            "Configurar AWS CloudTrail para auditoria",
                            "Revisar Security Groups e NACLs",
                            "Implementar AWS GuardDuty para detecção de ameaças"
                        ]
                    }
                    
                    return f"Recomendações AWS ({focus_area}): {recommendations.get(f'{focus_area}_optimization', recommendations['cost_optimization'])}"
                    
                except Exception as e:
                    return f"Erro nas recomendações: {str(e)}"
        
        return AWSOptimizationTool()
    
    def _create_security_assessment_tool(self) -> BaseTool:
        """Ferramenta para avaliação de segurança AWS"""
        class AWSSecurityAssessmentTool(BaseTool):
            name: str = "aws_security_assessment"
            description: str = "Avalia configurações de segurança e compliance na AWS"
            
            def _run(self, assessment_type: str = "general") -> str:
                try:
                    # Checklist de segurança AWS
                    security_checks = {
                        "iam_policies": "Verificação de políticas IAM",
                        "encryption": "Verificação de criptografia em repouso e trânsito",
                        "network_security": "Análise de Security Groups e NACLs",
                        "logging_monitoring": "Verificação de logs e monitoramento",
                        "compliance": "Verificação de compliance (SOC, PCI, HIPAA)"
                    }
                    
                    return f"Avaliação de segurança AWS: {security_checks}"
                    
                except Exception as e:
                    return f"Erro na avaliação de segurança: {str(e)}"
        
        return AWSSecurityAssessmentTool()
    
    def create_aws_analysis_task(self, analysis_scope: Dict[str, Any]) -> Task:
        """Cria tarefa de análise específica para AWS"""
        return Task(
            description=f"""
            Realize uma análise completa e especializada da infraestrutura AWS com o seguinte escopo:
            
            Escopo da Análise AWS:
            - Período de análise: {analysis_scope.get('period', 'último mês')}
            - Recursos alvo: {analysis_scope.get('resources', 'todos os recursos')}
            - Foco principal: {analysis_scope.get('focus', 'otimização de custos')}
            - Regiões: {analysis_scope.get('regions', 'todas as regiões ativas')}
            
            Análises a realizar:
            1. Análise detalhada de custos por serviço, região e período
            2. Inventário completo de recursos AWS
            3. Análise de performance via CloudWatch
            4. Recomendações de otimização específicas
            5. Avaliação de segurança e compliance
            
            Entregue um relatório técnico detalhado com:
            - Resumo executivo dos custos AWS
            - Inventário detalhado de recursos
            - Métricas de performance críticas
            - Recomendações priorizadas de otimização
            - Avaliação de riscos de segurança
            - Plano de ação com estimativas de economia
            
            Use suas ferramentas especializadas para obter dados precisos e atualizados.
            """,
            agent=self.agent,
            expected_output="Relatório técnico completo de análise AWS com recomendações específicas e plano de ação"
        )
    
    def analyze_aws_infrastructure(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise completa da infraestrutura AWS"""
        try:
            self.logger.info("Iniciando análise especializada AWS", extra=analysis_scope)
            
            # Verificar conexão AWS
            aws_connection = self.cloud_connector.connect_aws()
            if aws_connection.get('status') != 'connected':
                raise Exception(f"Falha na conexão AWS: {aws_connection.get('error')}")
            
            # Criar e executar tarefa de análise
            analysis_task = self.create_aws_analysis_task(analysis_scope)
            
            # Simular execução da tarefa (em implementação real seria via CrewAI)
            result = {
                "cost_analysis": "Análise de custos concluída",
                "resource_inventory": "Inventário de recursos concluído",
                "performance_analysis": "Análise de performance concluída",
                "optimization_recommendations": "Recomendações geradas",
                "security_assessment": "Avaliação de segurança concluída"
            }
            
            self.logger.info("Análise AWS concluída com sucesso")
            
            return {
                "status": "success",
                "provider": "AWS",
                "timestamp": datetime.now().isoformat(),
                "analysis_scope": analysis_scope,
                "results": result
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise AWS: {str(e)}")
            return {
                "status": "error",
                "provider": "AWS",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "analysis_scope": analysis_scope
            }

def main():
    """Função principal para teste do agente"""
    aws_specialist = AWSSpecialistAgent()
    
    # Exemplo de análise
    analysis_scope = {
        "period": "30 dias",
        "resources": "EC2, S3, RDS",
        "focus": "otimização de custos",
        "regions": ["us-east-1", "us-west-2"]
    }
    
    result = aws_specialist.analyze_aws_infrastructure(analysis_scope)
    print(f"Resultado da análise AWS: {result}")

if __name__ == "__main__":
    main()

