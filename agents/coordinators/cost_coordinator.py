"""
Agente Coordenador de Custos
Responsável por análise e otimização de custos entre provedores cloud
"""
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from crewai import Agent, Task
from crewai.tools import BaseTool
from config.project_config import config
from agents.base.logger import AgentLogger

class CostCoordinatorAgent:
    """
    Agente Coordenador de Custos - Análise e otimização de custos cloud
    """
    
    def __init__(self):
        self.logger = AgentLogger("CostCoordinatorAgent")
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Cria o agente coordenador de custos"""
        return Agent(
            role="Coordenador de Análise e Otimização de Custos Cloud",
            goal="Analisar, comparar e otimizar custos entre AWS e Google Cloud, "
                 "identificando oportunidades de economia, padrões de uso ineficiente "
                 "e desenvolvendo estratégias de otimização financeira para infraestrutura cloud.",
            backstory="Você é um especialista em FinOps (Financial Operations) com vasta experiência "
                     "em otimização de custos cloud. Sua expertise inclui análise de billing, "
                     "identificação de recursos subutilizados, estratégias de Reserved Instances, "
                     "Spot Instances, análise de TCO (Total Cost of Ownership) e desenvolvimento "
                     "de políticas de governança financeira para ambientes multi-cloud.",
            verbose=True,
            allow_delegation=False,
            tools=self._get_tools(),
            max_iter=config.agents.max_iterations,
            max_execution_time=config.agents.timeout_seconds
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Retorna as ferramentas para análise de custos"""
        return [
            self._create_cost_comparison_tool(),
            self._create_waste_identification_tool(),
            self._create_optimization_calculator_tool(),
            self._create_pricing_model_analyzer_tool(),
            self._create_budget_forecasting_tool()
        ]
    
    def _create_cost_comparison_tool(self) -> BaseTool:
        """Ferramenta para comparação de custos entre provedores"""
        class CostComparisonTool(BaseTool):
            name: str = "cost_comparison"
            description: str = "Compara custos entre AWS e GCP para diferentes serviços e configurações"
            
            def _run(self, service_type: str = "compute") -> str:
                try:
                    # Comparação baseada em preços públicos dos provedores
                    cost_comparison = {
                        "compute": {
                            "aws_ec2": {
                                "t3.medium": "$0.0416/hour",
                                "m5.large": "$0.096/hour",
                                "c5.xlarge": "$0.17/hour",
                                "reserved_discount": "up to 72%"
                            },
                            "gcp_compute": {
                                "e2-medium": "$0.0335/hour",
                                "n2-standard-2": "$0.0971/hour",
                                "c2-standard-4": "$0.1592/hour",
                                "committed_discount": "up to 57%"
                            }
                        },
                        "storage": {
                            "aws_s3": {
                                "standard": "$0.023/GB/month",
                                "ia": "$0.0125/GB/month",
                                "glacier": "$0.004/GB/month",
                                "deep_archive": "$0.00099/GB/month"
                            },
                            "gcp_storage": {
                                "standard": "$0.020/GB/month",
                                "nearline": "$0.010/GB/month",
                                "coldline": "$0.004/GB/month",
                                "archive": "$0.0012/GB/month"
                            }
                        },
                        "database": {
                            "aws_rds": {
                                "mysql_t3.micro": "$0.017/hour",
                                "postgres_m5.large": "$0.192/hour",
                                "reserved_discount": "up to 69%"
                            },
                            "gcp_sql": {
                                "mysql_db-f1-micro": "$0.0150/hour",
                                "postgres_db-n1-standard-2": "$0.1840/hour",
                                "committed_discount": "up to 57%"
                            }
                        }
                    }
                    
                    comparison_result = cost_comparison.get(service_type, {})
                    
                    return f"Comparação de custos para {service_type}: {comparison_result}"
                    
                except Exception as e:
                    return f"Erro na comparação de custos: {str(e)}"
        
        return CostComparisonTool()
    
    def _create_waste_identification_tool(self) -> BaseTool:
        """Ferramenta para identificação de desperdícios"""
        class WasteIdentificationTool(BaseTool):
            name: str = "waste_identification"
            description: str = "Identifica recursos subutilizados e oportunidades de economia"
            
            def _run(self, resource_type: str = "all") -> str:
                try:
                    waste_patterns = {
                        "compute": {
                            "idle_instances": "Instâncias com CPU < 5% por 7+ dias",
                            "oversized_instances": "Instâncias com utilização < 25%",
                            "unattached_volumes": "Volumes EBS/Persistent Disk órfãos",
                            "old_snapshots": "Snapshots > 90 dias sem uso"
                        },
                        "storage": {
                            "duplicate_data": "Dados duplicados em múltiplas regiões",
                            "old_backups": "Backups > 1 ano sem política de retenção",
                            "unused_buckets": "Buckets sem acesso > 6 meses",
                            "wrong_storage_class": "Dados em classe de storage inadequada"
                        },
                        "network": {
                            "unused_load_balancers": "Load balancers sem targets",
                            "idle_nat_gateways": "NAT Gateways com tráfego < 1GB/mês",
                            "cross_region_traffic": "Tráfego desnecessário entre regiões",
                            "unused_elastic_ips": "IPs elásticos não associados"
                        },
                        "database": {
                            "oversized_databases": "Databases com utilização < 30%",
                            "unused_read_replicas": "Read replicas sem queries",
                            "old_automated_backups": "Backups automáticos > 35 dias",
                            "idle_connections": "Conexões de database ociosas"
                        }
                    }
                    
                    if resource_type == "all":
                        return f"Padrões de desperdício identificados: {waste_patterns}"
                    else:
                        return f"Desperdícios em {resource_type}: {waste_patterns.get(resource_type, 'Tipo não encontrado')}"
                    
                except Exception as e:
                    return f"Erro na identificação de desperdícios: {str(e)}"
        
        return WasteIdentificationTool()
    
    def _create_optimization_calculator_tool(self) -> BaseTool:
        """Ferramenta para cálculo de otimizações"""
        class OptimizationCalculatorTool(BaseTool):
            name: str = "optimization_calculator"
            description: str = "Calcula potencial de economia com diferentes estratégias de otimização"
            
            def _run(self, optimization_type: str = "rightsizing") -> str:
                try:
                    optimization_scenarios = {
                        "rightsizing": {
                            "description": "Ajuste de tamanho de instâncias",
                            "potential_savings": "15-30%",
                            "implementation_effort": "Baixo",
                            "risk_level": "Baixo",
                            "timeframe": "1-2 semanas"
                        },
                        "reserved_instances": {
                            "description": "Compra de instâncias reservadas",
                            "potential_savings": "30-70%",
                            "implementation_effort": "Médio",
                            "risk_level": "Baixo",
                            "timeframe": "1 mês"
                        },
                        "spot_instances": {
                            "description": "Uso de instâncias spot/preemptible",
                            "potential_savings": "50-90%",
                            "implementation_effort": "Alto",
                            "risk_level": "Médio",
                            "timeframe": "2-3 meses"
                        },
                        "storage_optimization": {
                            "description": "Otimização de classes de storage",
                            "potential_savings": "20-60%",
                            "implementation_effort": "Baixo",
                            "risk_level": "Baixo",
                            "timeframe": "2-4 semanas"
                        },
                        "auto_scaling": {
                            "description": "Implementação de auto scaling",
                            "potential_savings": "20-40%",
                            "implementation_effort": "Médio",
                            "risk_level": "Médio",
                            "timeframe": "1-2 meses"
                        }
                    }
                    
                    calculation_result = optimization_scenarios.get(optimization_type, {})
                    
                    return f"Cálculo de otimização para {optimization_type}: {calculation_result}"
                    
                except Exception as e:
                    return f"Erro no cálculo de otimização: {str(e)}"
        
        return OptimizationCalculatorTool()
    
    def _create_pricing_model_analyzer_tool(self) -> BaseTool:
        """Ferramenta para análise de modelos de preços"""
        class PricingModelAnalyzerTool(BaseTool):
            name: str = "pricing_model_analyzer"
            description: str = "Analisa diferentes modelos de preços e recomenda a melhor estratégia"
            
            def _run(self, workload_type: str = "steady_state") -> str:
                try:
                    pricing_recommendations = {
                        "steady_state": {
                            "aws_recommendation": "Reserved Instances (1-3 anos)",
                            "gcp_recommendation": "Committed Use Discounts",
                            "savings_potential": "50-70%",
                            "best_for": "Workloads previsíveis e estáveis"
                        },
                        "variable": {
                            "aws_recommendation": "Savings Plans + On-Demand",
                            "gcp_recommendation": "Sustained Use Discounts + On-Demand",
                            "savings_potential": "20-40%",
                            "best_for": "Workloads com variação moderada"
                        },
                        "batch_processing": {
                            "aws_recommendation": "Spot Instances",
                            "gcp_recommendation": "Preemptible VMs",
                            "savings_potential": "60-90%",
                            "best_for": "Processamento em lote tolerante a interrupções"
                        },
                        "development": {
                            "aws_recommendation": "On-Demand + Scheduled Scaling",
                            "gcp_recommendation": "On-Demand + Custom Machine Types",
                            "savings_potential": "30-50%",
                            "best_for": "Ambientes de desenvolvimento e teste"
                        }
                    }
                    
                    recommendation = pricing_recommendations.get(workload_type, {})
                    
                    return f"Recomendação de preços para {workload_type}: {recommendation}"
                    
                except Exception as e:
                    return f"Erro na análise de preços: {str(e)}"
        
        return PricingModelAnalyzerTool()
    
    def _create_budget_forecasting_tool(self) -> BaseTool:
        """Ferramenta para previsão de orçamento"""
        class BudgetForecastingTool(BaseTool):
            name: str = "budget_forecasting"
            description: str = "Prevê custos futuros baseado em tendências e crescimento planejado"
            
            def _run(self, forecast_period: str = "12_months") -> str:
                try:
                    forecast_scenarios = {
                        "3_months": {
                            "growth_assumption": "5% ao mês",
                            "seasonal_factors": "Considerados",
                            "confidence_level": "Alto (85%)",
                            "key_variables": ["Uso atual", "Projetos planejados"]
                        },
                        "6_months": {
                            "growth_assumption": "3% ao mês",
                            "seasonal_factors": "Considerados",
                            "confidence_level": "Médio (70%)",
                            "key_variables": ["Tendências históricas", "Roadmap de produtos"]
                        },
                        "12_months": {
                            "growth_assumption": "2% ao mês",
                            "seasonal_factors": "Estimados",
                            "confidence_level": "Baixo (60%)",
                            "key_variables": ["Estratégia de negócio", "Expansão planejada"]
                        }
                    }
                    
                    forecast_data = forecast_scenarios.get(forecast_period, {})
                    
                    return f"Previsão orçamentária para {forecast_period}: {forecast_data}"
                    
                except Exception as e:
                    return f"Erro na previsão orçamentária: {str(e)}"
        
        return BudgetForecastingTool()
    
    def create_cost_analysis_task(self, analysis_scope: Dict[str, Any]) -> Task:
        """Cria tarefa de análise de custos"""
        return Task(
            description=f"""
            Realize uma análise completa de custos cloud com o seguinte escopo:
            
            Escopo da Análise de Custos:
            - Provedores: {analysis_scope.get('providers', ['AWS', 'GCP'])}
            - Período: {analysis_scope.get('period', 'últimos 3 meses')}
            - Orçamento atual: {analysis_scope.get('budget', 'a ser determinado')}
            - Meta de economia: {analysis_scope.get('savings_target', '20%')}
            - Serviços prioritários: {analysis_scope.get('priority_services', 'compute, storage, database')}
            
            Análises a realizar:
            1. Comparação detalhada de custos entre AWS e GCP
            2. Identificação de desperdícios e recursos subutilizados
            3. Cálculo de potencial de economia com diferentes estratégias
            4. Análise de modelos de preços mais adequados
            5. Previsão orçamentária para os próximos 12 meses
            
            Entregue um relatório de custos com:
            - Análise comparativa de custos por serviço
            - Identificação de oportunidades de economia imediata
            - Recomendações de otimização priorizadas por ROI
            - Estratégia de pricing model por tipo de workload
            - Previsão orçamentária com cenários otimista/pessimista
            - Plano de implementação com cronograma e responsáveis
            
            Use suas ferramentas especializadas para análise precisa de custos.
            """,
            agent=self.agent,
            expected_output="Relatório completo de análise de custos com plano de otimização detalhado"
        )
    
    def analyze_cost_landscape(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise completa do cenário de custos"""
        try:
            self.logger.info("Iniciando análise de custos", extra=analysis_scope)
            
            # Criar e executar tarefa de análise
            analysis_task = self.create_cost_analysis_task(analysis_scope)
            
            # Simular execução da tarefa (em implementação real seria via CrewAI)
            result = {
                "cost_comparison": "Comparação de custos concluída",
                "waste_identification": "Identificação de desperdícios concluída",
                "optimization_calculation": "Cálculos de otimização concluídos",
                "pricing_analysis": "Análise de modelos de preços concluída",
                "budget_forecast": "Previsão orçamentária concluída"
            }
            
            # Log específico para custos
            self.logger.log_cost_analysis("Multi-Cloud", {
                "providers": analysis_scope.get('providers', ['AWS', 'GCP']),
                "period": analysis_scope.get('period', 'últimos 3 meses'),
                "analysis_completed": True
            })
            
            self.logger.info("Análise de custos concluída com sucesso")
            
            return {
                "status": "success",
                "analysis_type": "Cost",
                "timestamp": datetime.now().isoformat(),
                "analysis_scope": analysis_scope,
                "results": result
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de custos: {str(e)}")
            return {
                "status": "error",
                "analysis_type": "Cost",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "analysis_scope": analysis_scope
            }

def main():
    """Função principal para teste do agente"""
    cost_coordinator = CostCoordinatorAgent()
    
    # Exemplo de análise
    analysis_scope = {
        "providers": ["AWS", "GCP"],
        "period": "últimos 3 meses",
        "budget": "$50,000/mês",
        "savings_target": "25%",
        "priority_services": "compute, storage, database"
    }
    
    result = cost_coordinator.analyze_cost_landscape(analysis_scope)
    print(f"Resultado da análise de custos: {result}")

if __name__ == "__main__":
    main()

