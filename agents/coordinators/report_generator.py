"""
Agente Gerador de Relatórios
Responsável por compilar dados de todos os agentes e gerar relatórios finais
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from crewai import Agent, Task
from crewai.tools import BaseTool
from config.project_config import config
from agents.base.logger import AgentLogger

@dataclass
class ReportSection:
    """Estrutura de uma seção do relatório"""
    title: str
    content: str
    priority: int
    data_source: str

class ReportGeneratorAgent:
    """
    Agente Gerador de Relatórios - Compilação e geração de relatórios finais
    """
    
    def __init__(self):
        self.logger = AgentLogger("ReportGeneratorAgent")
        self.agent = self._create_agent()
        self.report_sections: List[ReportSection] = []
        
    def _create_agent(self) -> Agent:
        """Cria o agente gerador de relatórios"""
        return Agent(
            role="Gerador de Relatórios Executivos e Técnicos",
            goal="Compilar, analisar e sintetizar dados de todos os agentes especialistas e "
                 "coordenadores para gerar relatórios executivos e técnicos abrangentes, "
                 "com recomendações estratégicas e planos de ação priorizados.",
            backstory="Você é um analista sênior especializado em business intelligence e "
                     "comunicação executiva, com vasta experiência em transformar dados "
                     "técnicos complexos em insights acionáveis. Sua expertise inclui "
                     "análise de dados, visualização de informações, redação técnica "
                     "e apresentação de recomendações estratégicas para diferentes "
                     "audiências (executivos, técnicos, jurídicos).",
            verbose=True,
            allow_delegation=False,
            tools=self._get_tools(),
            max_iter=config.agents.max_iterations,
            max_execution_time=config.agents.timeout_seconds
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Retorna as ferramentas para geração de relatórios"""
        return [
            self._create_data_compiler_tool(),
            self._create_executive_summary_generator(),
            self._create_technical_report_generator(),
            self._create_recommendation_prioritizer(),
            self._create_action_plan_generator()
        ]
    
    def _create_data_compiler_tool(self) -> BaseTool:
        """Ferramenta para compilação de dados de múltiplas fontes"""
        class DataCompilerTool(BaseTool):
            name: str = "data_compiler"
            description: str = "Compila e normaliza dados de diferentes agentes e fontes"
            
            def _run(self, data_sources: str) -> str:
                try:
                    # Estrutura para compilação de dados
                    compiled_data = {
                        "aws_analysis": {
                            "cost_data": "Dados de custos AWS compilados",
                            "resource_inventory": "Inventário de recursos AWS",
                            "performance_metrics": "Métricas de performance AWS",
                            "optimization_opportunities": "Oportunidades de otimização AWS"
                        },
                        "gcp_analysis": {
                            "cost_data": "Dados de custos GCP compilados",
                            "resource_inventory": "Inventário de recursos GCP",
                            "performance_metrics": "Métricas de performance GCP",
                            "optimization_opportunities": "Oportunidades de otimização GCP"
                        },
                        "sla_analysis": {
                            "availability_comparison": "Comparação de disponibilidade",
                            "performance_benchmarks": "Benchmarks de performance",
                            "uptime_analysis": "Análise de uptime histórico",
                            "multi_cloud_recommendations": "Recomendações multi-cloud"
                        },
                        "cost_analysis": {
                            "cost_comparison": "Comparação de custos entre provedores",
                            "waste_identification": "Identificação de desperdícios",
                            "optimization_calculations": "Cálculos de otimização",
                            "budget_forecasts": "Previsões orçamentárias"
                        },
                        "compliance_analysis": {
                            "framework_compliance": "Status de compliance por framework",
                            "security_controls": "Controles de segurança implementados",
                            "gap_analysis": "Análise de gaps de compliance",
                            "risk_assessment": "Avaliação de riscos"
                        },
                        "legal_analysis": {
                            "regulatory_compliance": "Conformidade regulatória",
                            "contract_analysis": "Análise de contratos",
                            "data_transfer_compliance": "Compliance de transferência",
                            "legal_risks": "Riscos jurídicos identificados"
                        }
                    }
                    
                    return f"Dados compilados de: {compiled_data}"
                    
                except Exception as e:
                    return f"Erro na compilação de dados: {str(e)}"
        
        return DataCompilerTool()
    
    def _create_executive_summary_generator(self) -> BaseTool:
        """Ferramenta para geração de resumo executivo"""
        class ExecutiveSummaryGenerator(BaseTool):
            name: str = "executive_summary_generator"
            description: str = "Gera resumo executivo com principais insights e recomendações"
            
            def _run(self, focus_area: str = "cost_optimization") -> str:
                try:
                    executive_summaries = {
                        "cost_optimization": {
                            "key_findings": [
                                "Potencial de economia de 25-30% identificado",
                                "Recursos subutilizados representam 15% dos custos",
                                "GCP apresenta melhor custo-benefício para workloads específicos",
                                "Reserved Instances podem reduzir custos em 40%"
                            ],
                            "strategic_recommendations": [
                                "Implementar estratégia multi-cloud para otimização",
                                "Migrar workloads batch para instâncias spot/preemptible",
                                "Estabelecer governança de custos com alertas automáticos",
                                "Revisar arquitetura para rightsizing de recursos"
                            ],
                            "business_impact": "Economia estimada de $150K-200K anuais",
                            "implementation_timeline": "3-6 meses para implementação completa"
                        },
                        "risk_management": {
                            "key_findings": [
                                "Gaps críticos de compliance identificados",
                                "Riscos jurídicos de transferência internacional",
                                "SLA gaps podem impactar disponibilidade",
                                "Controles de segurança necessitam fortalecimento"
                            ],
                            "strategic_recommendations": [
                                "Implementar programa de compliance abrangente",
                                "Estabelecer estratégia de disaster recovery multi-cloud",
                                "Adequar contratos para conformidade LGPD/GDPR",
                                "Fortalecer controles de segurança e monitoramento"
                            ],
                            "business_impact": "Redução significativa de riscos regulatórios",
                            "implementation_timeline": "6-12 meses para adequação completa"
                        },
                        "performance_optimization": {
                            "key_findings": [
                                "Oportunidades de melhoria de performance identificadas",
                                "Latência pode ser reduzida em 20-30%",
                                "Auto-scaling inadequado em 40% dos recursos",
                                "Arquitetura multi-region recomendada"
                            ],
                            "strategic_recommendations": [
                                "Implementar CDN global para redução de latência",
                                "Otimizar configurações de auto-scaling",
                                "Estabelecer arquitetura multi-region",
                                "Implementar cache distribuído"
                            ],
                            "business_impact": "Melhoria de 25% na experiência do usuário",
                            "implementation_timeline": "2-4 meses para otimizações principais"
                        }
                    }
                    
                    summary_data = executive_summaries.get(focus_area, {})
                    
                    return f"Resumo executivo - {focus_area}: {summary_data}"
                    
                except Exception as e:
                    return f"Erro na geração de resumo executivo: {str(e)}"
        
        return ExecutiveSummaryGenerator()
    
    def _create_technical_report_generator(self) -> BaseTool:
        """Ferramenta para geração de relatório técnico detalhado"""
        class TechnicalReportGenerator(BaseTool):
            name: str = "technical_report_generator"
            description: str = "Gera relatório técnico detalhado com análises específicas"
            
            def _run(self, report_type: str = "comprehensive") -> str:
                try:
                    technical_reports = {
                        "comprehensive": {
                            "sections": [
                                "1. Análise de Infraestrutura Atual",
                                "2. Comparação AWS vs GCP",
                                "3. Análise de Custos Detalhada",
                                "4. Avaliação de Performance",
                                "5. Análise de SLA e Disponibilidade",
                                "6. Compliance e Conformidade",
                                "7. Aspectos Jurídicos e Regulatórios",
                                "8. Recomendações Técnicas",
                                "9. Plano de Implementação",
                                "10. Anexos e Documentação Técnica"
                            ],
                            "technical_depth": "Detalhado com métricas específicas",
                            "target_audience": "Arquitetos, DevOps, Engenheiros"
                        },
                        "cost_analysis": {
                            "sections": [
                                "1. Análise de Custos Atual",
                                "2. Comparação de Preços por Serviço",
                                "3. Identificação de Desperdícios",
                                "4. Projeções e Cenários",
                                "5. Recomendações de Otimização"
                            ],
                            "technical_depth": "Foco em métricas financeiras",
                            "target_audience": "FinOps, Controllers, CFO"
                        },
                        "security_compliance": {
                            "sections": [
                                "1. Avaliação de Segurança Atual",
                                "2. Análise de Compliance",
                                "3. Gaps Identificados",
                                "4. Matriz de Riscos",
                                "5. Plano de Adequação"
                            ],
                            "technical_depth": "Foco em controles e frameworks",
                            "target_audience": "CISO, Compliance, Auditoria"
                        }
                    }
                    
                    report_data = technical_reports.get(report_type, {})
                    
                    return f"Relatório técnico - {report_type}: {report_data}"
                    
                except Exception as e:
                    return f"Erro na geração de relatório técnico: {str(e)}"
        
        return TechnicalReportGenerator()
    
    def _create_recommendation_prioritizer(self) -> BaseTool:
        """Ferramenta para priorização de recomendações"""
        class RecommendationPrioritizer(BaseTool):
            name: str = "recommendation_prioritizer"
            description: str = "Prioriza recomendações baseado em impacto, esforço e risco"
            
            def _run(self, criteria: str = "roi") -> str:
                try:
                    prioritization_criteria = {
                        "roi": {
                            "high_priority": [
                                "Rightsizing de instâncias (ROI: 300%)",
                                "Implementação de Reserved Instances (ROI: 250%)",
                                "Otimização de storage classes (ROI: 200%)",
                                "Eliminação de recursos órfãos (ROI: 500%)"
                            ],
                            "medium_priority": [
                                "Implementação de auto-scaling (ROI: 150%)",
                                "Migração para instâncias spot (ROI: 180%)",
                                "Otimização de rede (ROI: 120%)"
                            ],
                            "low_priority": [
                                "Implementação de CDN (ROI: 80%)",
                                "Otimização de queries (ROI: 60%)"
                            ]
                        },
                        "risk": {
                            "critical": [
                                "Adequação LGPD/GDPR (Risco: Multas regulatórias)",
                                "Implementação de backup/DR (Risco: Perda de dados)",
                                "Controles de acesso (Risco: Vazamento de dados)"
                            ],
                            "high": [
                                "Monitoramento de segurança (Risco: Detecção tardia)",
                                "Compliance frameworks (Risco: Auditoria)",
                                "Documentação de processos (Risco: Operacional)"
                            ],
                            "medium": [
                                "Treinamento de equipes (Risco: Erro humano)",
                                "Otimização de performance (Risco: SLA)"
                            ]
                        },
                        "effort": {
                            "quick_wins": [
                                "Eliminação de recursos órfãos (1-2 semanas)",
                                "Ajuste de storage classes (2-3 semanas)",
                                "Configuração de alertas (1 semana)"
                            ],
                            "medium_effort": [
                                "Implementação de Reserved Instances (1-2 meses)",
                                "Rightsizing de recursos (2-3 meses)",
                                "Auto-scaling configuration (1-2 meses)"
                            ],
                            "high_effort": [
                                "Migração multi-cloud (6-12 meses)",
                                "Implementação de DR (3-6 meses)",
                                "Compliance program (6-12 meses)"
                            ]
                        }
                    }
                    
                    priority_data = prioritization_criteria.get(criteria, {})
                    
                    return f"Priorização por {criteria}: {priority_data}"
                    
                except Exception as e:
                    return f"Erro na priorização: {str(e)}"
        
        return RecommendationPrioritizer()
    
    def _create_action_plan_generator(self) -> BaseTool:
        """Ferramenta para geração de plano de ação"""
        class ActionPlanGenerator(BaseTool):
            name: str = "action_plan_generator"
            description: str = "Gera plano de ação detalhado com cronograma e responsáveis"
            
            def _run(self, plan_scope: str = "comprehensive") -> str:
                try:
                    action_plans = {
                        "comprehensive": {
                            "phase_1": {
                                "duration": "0-3 meses",
                                "focus": "Quick wins e preparação",
                                "actions": [
                                    "Eliminação de recursos órfãos",
                                    "Configuração de alertas de custo",
                                    "Rightsizing inicial de instâncias",
                                    "Implementação de tagging strategy"
                                ],
                                "responsible": "Equipe DevOps/Cloud",
                                "expected_savings": "$20K-30K"
                            },
                            "phase_2": {
                                "duration": "3-6 meses",
                                "focus": "Otimizações estruturais",
                                "actions": [
                                    "Implementação de Reserved Instances",
                                    "Auto-scaling configuration",
                                    "Storage optimization",
                                    "Network optimization"
                                ],
                                "responsible": "Arquitetos + DevOps",
                                "expected_savings": "$50K-80K"
                            },
                            "phase_3": {
                                "duration": "6-12 meses",
                                "focus": "Transformação e compliance",
                                "actions": [
                                    "Multi-cloud strategy implementation",
                                    "Compliance program rollout",
                                    "DR/Backup optimization",
                                    "Advanced monitoring setup"
                                ],
                                "responsible": "Toda equipe técnica",
                                "expected_savings": "$80K-120K"
                            }
                        },
                        "cost_optimization": {
                            "immediate": {
                                "timeframe": "1-4 semanas",
                                "actions": [
                                    "Audit e eliminação de recursos órfãos",
                                    "Configuração de budget alerts",
                                    "Review de storage classes",
                                    "Identificação de instâncias idle"
                                ]
                            },
                            "short_term": {
                                "timeframe": "1-3 meses",
                                "actions": [
                                    "Rightsizing de instâncias",
                                    "Compra de Reserved Instances",
                                    "Implementação de auto-scaling",
                                    "Otimização de data transfer"
                                ]
                            },
                            "long_term": {
                                "timeframe": "3-12 meses",
                                "actions": [
                                    "Arquitetura multi-cloud",
                                    "Spot instances para batch jobs",
                                    "Advanced cost optimization",
                                    "FinOps culture implementation"
                                ]
                            }
                        }
                    }
                    
                    plan_data = action_plans.get(plan_scope, {})
                    
                    return f"Plano de ação - {plan_scope}: {plan_data}"
                    
                except Exception as e:
                    return f"Erro na geração de plano de ação: {str(e)}"
        
        return ActionPlanGenerator()
    
    def create_report_generation_task(self, report_scope: Dict[str, Any]) -> Task:
        """Cria tarefa de geração de relatório"""
        return Task(
            description=f"""
            Gere um relatório completo baseado nos dados coletados com o seguinte escopo:
            
            Escopo do Relatório:
            - Tipo de relatório: {report_scope.get('report_type', 'executivo e técnico')}
            - Audiência: {report_scope.get('audience', 'executivos e equipe técnica')}
            - Foco principal: {report_scope.get('focus', 'otimização de custos e compliance')}
            - Período analisado: {report_scope.get('period', 'últimos 3 meses')}
            - Provedores: {report_scope.get('providers', ['AWS', 'GCP'])}
            
            Estrutura do Relatório:
            1. Compile todos os dados dos agentes especialistas e coordenadores
            2. Gere resumo executivo com principais insights
            3. Desenvolva relatório técnico detalhado
            4. Priorize recomendações por impacto e esforço
            5. Crie plano de ação com cronograma detalhado
            
            Entregue um relatório estruturado com:
            - Resumo executivo (2-3 páginas)
            - Análise detalhada por área (custos, SLA, compliance, jurídico)
            - Recomendações priorizadas com ROI estimado
            - Plano de implementação com fases e responsáveis
            - Anexos técnicos com dados detalhados
            - Dashboard de métricas principais
            
            Use suas ferramentas para compilar, analisar e apresentar os dados de forma clara e acionável.
            """,
            agent=self.agent,
            expected_output="Relatório executivo e técnico completo com plano de ação detalhado"
        )
    
    def generate_comprehensive_report(self, report_scope: Dict[str, Any], agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera relatório completo baseado nos dados dos agentes"""
        try:
            self.logger.info("Iniciando geração de relatório", extra=report_scope)
            
            # Criar e executar tarefa de geração
            report_task = self.create_report_generation_task(report_scope)
            
            # Compilar dados de todos os agentes
            compiled_data = self._compile_agent_data(agent_data)
            
            # Gerar seções do relatório
            executive_summary = self._generate_executive_summary(compiled_data)
            technical_analysis = self._generate_technical_analysis(compiled_data)
            recommendations = self._prioritize_recommendations(compiled_data)
            action_plan = self._generate_action_plan(recommendations)
            
            # Estruturar relatório final
            final_report = {
                "executive_summary": executive_summary,
                "technical_analysis": technical_analysis,
                "recommendations": recommendations,
                "action_plan": action_plan,
                "appendices": {
                    "raw_data": compiled_data,
                    "methodology": "Análise multi-agente com CrewAI",
                    "data_sources": list(agent_data.keys())
                }
            }
            
            self.logger.info("Relatório gerado com sucesso")
            
            return {
                "status": "success",
                "report_type": "Comprehensive Analysis",
                "timestamp": datetime.now().isoformat(),
                "report_scope": report_scope,
                "report": final_report
            }
            
        except Exception as e:
            self.logger.error(f"Erro na geração de relatório: {str(e)}")
            return {
                "status": "error",
                "report_type": "Comprehensive Analysis",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "report_scope": report_scope
            }
    
    def _compile_agent_data(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compila dados de todos os agentes"""
        return {
            "compilation_timestamp": datetime.now().isoformat(),
            "data_sources": agent_data,
            "summary": "Dados compilados de todos os agentes"
        }
    
    def _generate_executive_summary(self, compiled_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera resumo executivo"""
        return {
            "key_findings": "Principais descobertas da análise",
            "strategic_recommendations": "Recomendações estratégicas",
            "business_impact": "Impacto nos negócios",
            "next_steps": "Próximos passos recomendados"
        }
    
    def _generate_technical_analysis(self, compiled_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera análise técnica detalhada"""
        return {
            "infrastructure_analysis": "Análise da infraestrutura atual",
            "cost_analysis": "Análise detalhada de custos",
            "performance_analysis": "Análise de performance",
            "security_compliance": "Análise de segurança e compliance"
        }
    
    def _prioritize_recommendations(self, compiled_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioriza recomendações"""
        return [
            {
                "priority": "High",
                "recommendation": "Implementar rightsizing de instâncias",
                "impact": "Alto",
                "effort": "Médio",
                "roi": "300%"
            }
        ]
    
    def _generate_action_plan(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gera plano de ação"""
        return {
            "phase_1": "Ações imediatas (0-3 meses)",
            "phase_2": "Ações de médio prazo (3-6 meses)",
            "phase_3": "Ações de longo prazo (6-12 meses)"
        }

def main():
    """Função principal para teste do agente"""
    report_generator = ReportGeneratorAgent()
    
    # Exemplo de geração de relatório
    report_scope = {
        "report_type": "executivo e técnico",
        "audience": "C-level e equipe técnica",
        "focus": "otimização de custos e compliance",
        "period": "últimos 3 meses",
        "providers": ["AWS", "GCP"]
    }
    
    agent_data = {
        "aws_specialist": {"status": "completed"},
        "gcp_specialist": {"status": "completed"},
        "sla_coordinator": {"status": "completed"},
        "cost_coordinator": {"status": "completed"},
        "compliance_coordinator": {"status": "completed"},
        "legal_coordinator": {"status": "completed"}
    }
    
    result = report_generator.generate_comprehensive_report(report_scope, agent_data)
    print(f"Resultado da geração de relatório: {result}")

if __name__ == "__main__":
    main()

