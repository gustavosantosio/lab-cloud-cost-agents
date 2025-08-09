"""
Agente Coordenador de Conformidade
Responsável por verificação de conformidade técnica e regulatória
"""
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from crewai import Agent, Task
from crewai.tools import BaseTool
from config.project_config import config
from agents.base.logger import AgentLogger

class ComplianceCoordinatorAgent:
    """
    Agente Coordenador de Conformidade - Verificação de compliance técnico e regulatório
    """
    
    def __init__(self):
        self.logger = AgentLogger("ComplianceCoordinatorAgent")
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Cria o agente coordenador de conformidade"""
        return Agent(
            role="Coordenador de Conformidade e Compliance Cloud",
            goal="Verificar e garantir conformidade técnica e regulatória da infraestrutura cloud "
                 "com padrões internacionais, frameworks de segurança e regulamentações aplicáveis, "
                 "identificando gaps de compliance e desenvolvendo planos de adequação.",
            backstory="Você é um especialista em compliance e governança de TI com vasta experiência "
                     "em frameworks de conformidade como ISO 27001, SOC 2, PCI DSS, HIPAA, GDPR "
                     "e regulamentações brasileiras. Sua expertise inclui auditoria de segurança, "
                     "análise de riscos, implementação de controles de compliance e desenvolvimento "
                     "de políticas de governança para ambientes cloud multi-provedor.",
            verbose=True,
            allow_delegation=False,
            tools=self._get_tools(),
            max_iter=config.agents.max_iterations,
            max_execution_time=config.agents.timeout_seconds
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Retorna as ferramentas para análise de conformidade"""
        return [
            self._create_compliance_framework_checker(),
            self._create_security_controls_auditor(),
            self._create_data_governance_analyzer(),
            self._create_regulatory_compliance_checker(),
            self._create_risk_assessment_tool()
        ]
    
    def _create_compliance_framework_checker(self) -> BaseTool:
        """Ferramenta para verificação de frameworks de compliance"""
        class ComplianceFrameworkChecker(BaseTool):
            name: str = "compliance_framework_checker"
            description: str = "Verifica conformidade com frameworks padrão (ISO 27001, SOC 2, etc.)"
            
            def _run(self, framework: str = "iso27001") -> str:
                try:
                    compliance_frameworks = {
                        "iso27001": {
                            "name": "ISO/IEC 27001:2013",
                            "key_controls": [
                                "A.9 - Controle de acesso",
                                "A.10 - Criptografia",
                                "A.12 - Segurança operacional",
                                "A.13 - Segurança de comunicações",
                                "A.14 - Aquisição, desenvolvimento e manutenção de sistemas"
                            ],
                            "aws_compliance": "AWS oferece certificação ISO 27001",
                            "gcp_compliance": "GCP oferece certificação ISO 27001",
                            "gap_analysis": "Verificar implementação de controles específicos"
                        },
                        "soc2": {
                            "name": "SOC 2 Type II",
                            "key_controls": [
                                "Segurança - Proteção contra acesso não autorizado",
                                "Disponibilidade - Sistema disponível para operação",
                                "Integridade de processamento - Processamento completo e preciso",
                                "Confidencialidade - Proteção de informações confidenciais",
                                "Privacidade - Proteção de informações pessoais"
                            ],
                            "aws_compliance": "AWS SOC 2 Type II certificado",
                            "gcp_compliance": "GCP SOC 2 Type II certificado",
                            "gap_analysis": "Verificar controles de cliente vs. provedor"
                        },
                        "pci_dss": {
                            "name": "PCI DSS v3.2.1",
                            "key_controls": [
                                "Req 1 - Firewall e configuração de roteador",
                                "Req 2 - Não usar padrões fornecidos pelo fornecedor",
                                "Req 3 - Proteger dados de portadores de cartão armazenados",
                                "Req 4 - Criptografar transmissão de dados",
                                "Req 6 - Desenvolver e manter sistemas seguros"
                            ],
                            "aws_compliance": "AWS PCI DSS Level 1 certificado",
                            "gcp_compliance": "GCP PCI DSS Level 1 certificado",
                            "gap_analysis": "Verificar implementação de controles de aplicação"
                        }
                    }
                    
                    framework_data = compliance_frameworks.get(framework, {})
                    
                    return f"Verificação de conformidade {framework}: {framework_data}"
                    
                except Exception as e:
                    return f"Erro na verificação de framework: {str(e)}"
        
        return ComplianceFrameworkChecker()
    
    def _create_security_controls_auditor(self) -> BaseTool:
        """Ferramenta para auditoria de controles de segurança"""
        class SecurityControlsAuditor(BaseTool):
            name: str = "security_controls_auditor"
            description: str = "Audita implementação de controles de segurança na infraestrutura"
            
            def _run(self, control_category: str = "access_control") -> str:
                try:
                    security_controls = {
                        "access_control": {
                            "iam_policies": "Verificar princípio do menor privilégio",
                            "mfa_enforcement": "Verificar MFA obrigatório para usuários privilegiados",
                            "service_accounts": "Auditar service accounts e suas permissões",
                            "privileged_access": "Verificar controles de acesso privilegiado",
                            "access_reviews": "Verificar revisões periódicas de acesso"
                        },
                        "data_protection": {
                            "encryption_at_rest": "Verificar criptografia de dados em repouso",
                            "encryption_in_transit": "Verificar criptografia de dados em trânsito",
                            "key_management": "Auditar gerenciamento de chaves criptográficas",
                            "data_classification": "Verificar classificação de dados",
                            "data_retention": "Auditar políticas de retenção de dados"
                        },
                        "network_security": {
                            "firewall_rules": "Auditar regras de firewall e security groups",
                            "network_segmentation": "Verificar segmentação de rede",
                            "vpc_configuration": "Auditar configuração de VPC/VNet",
                            "ddos_protection": "Verificar proteção contra DDoS",
                            "intrusion_detection": "Auditar sistemas de detecção de intrusão"
                        },
                        "monitoring_logging": {
                            "audit_logging": "Verificar logs de auditoria habilitados",
                            "log_retention": "Auditar políticas de retenção de logs",
                            "monitoring_alerts": "Verificar alertas de segurança configurados",
                            "incident_response": "Auditar procedimentos de resposta a incidentes",
                            "log_integrity": "Verificar integridade e proteção de logs"
                        }
                    }
                    
                    controls_data = security_controls.get(control_category, {})
                    
                    return f"Auditoria de controles de {control_category}: {controls_data}"
                    
                except Exception as e:
                    return f"Erro na auditoria de controles: {str(e)}"
        
        return SecurityControlsAuditor()
    
    def _create_data_governance_analyzer(self) -> BaseTool:
        """Ferramenta para análise de governança de dados"""
        class DataGovernanceAnalyzer(BaseTool):
            name: str = "data_governance_analyzer"
            description: str = "Analisa práticas de governança de dados e proteção de privacidade"
            
            def _run(self, governance_aspect: str = "data_classification") -> str:
                try:
                    governance_aspects = {
                        "data_classification": {
                            "public_data": "Dados públicos - sem restrições",
                            "internal_data": "Dados internos - acesso restrito a funcionários",
                            "confidential_data": "Dados confidenciais - acesso restrito",
                            "restricted_data": "Dados restritos - máxima proteção",
                            "compliance_requirements": "Classificação conforme LGPD/GDPR"
                        },
                        "data_lifecycle": {
                            "data_creation": "Políticas de criação e coleta de dados",
                            "data_processing": "Controles de processamento e transformação",
                            "data_storage": "Políticas de armazenamento e retenção",
                            "data_archival": "Procedimentos de arquivamento",
                            "data_deletion": "Políticas de exclusão segura"
                        },
                        "privacy_protection": {
                            "consent_management": "Gerenciamento de consentimento (LGPD)",
                            "data_minimization": "Princípio da minimização de dados",
                            "purpose_limitation": "Limitação de finalidade",
                            "data_portability": "Direito à portabilidade de dados",
                            "right_to_erasure": "Direito ao esquecimento"
                        },
                        "data_quality": {
                            "accuracy": "Verificação de precisão dos dados",
                            "completeness": "Verificação de completude",
                            "consistency": "Verificação de consistência",
                            "timeliness": "Verificação de atualidade",
                            "validity": "Verificação de validade"
                        }
                    }
                    
                    governance_data = governance_aspects.get(governance_aspect, {})
                    
                    return f"Análise de governança - {governance_aspect}: {governance_data}"
                    
                except Exception as e:
                    return f"Erro na análise de governança: {str(e)}"
        
        return DataGovernanceAnalyzer()
    
    def _create_regulatory_compliance_checker(self) -> BaseTool:
        """Ferramenta para verificação de conformidade regulatória"""
        class RegulatoryComplianceChecker(BaseTool):
            name: str = "regulatory_compliance_checker"
            description: str = "Verifica conformidade com regulamentações específicas (LGPD, GDPR, etc.)"
            
            def _run(self, regulation: str = "lgpd") -> str:
                try:
                    regulatory_requirements = {
                        "lgpd": {
                            "name": "Lei Geral de Proteção de Dados (Brasil)",
                            "key_requirements": [
                                "Art. 6º - Princípios do tratamento de dados",
                                "Art. 9º - Consentimento do titular",
                                "Art. 18º - Direitos do titular",
                                "Art. 46º - Segurança e sigilo de dados",
                                "Art. 48º - Comunicação de incidente de segurança"
                            ],
                            "technical_measures": [
                                "Criptografia de dados pessoais",
                                "Controles de acesso granulares",
                                "Logs de auditoria detalhados",
                                "Procedimentos de resposta a incidentes",
                                "Avaliação de impacto à proteção de dados"
                            ],
                            "compliance_status": "Verificar implementação de controles técnicos"
                        },
                        "gdpr": {
                            "name": "General Data Protection Regulation (EU)",
                            "key_requirements": [
                                "Art. 5 - Princípios de processamento",
                                "Art. 7 - Condições para consentimento",
                                "Art. 17 - Direito ao apagamento",
                                "Art. 32 - Segurança do processamento",
                                "Art. 33 - Notificação de violação"
                            ],
                            "technical_measures": [
                                "Privacy by design",
                                "Data protection impact assessment",
                                "Pseudonymization e anonimização",
                                "Controles de transferência internacional",
                                "Registros de atividades de processamento"
                            ],
                            "compliance_status": "Verificar adequação para transferências internacionais"
                        },
                        "hipaa": {
                            "name": "Health Insurance Portability and Accountability Act (US)",
                            "key_requirements": [
                                "Administrative Safeguards",
                                "Physical Safeguards",
                                "Technical Safeguards",
                                "Breach Notification Rule",
                                "Business Associate Agreements"
                            ],
                            "technical_measures": [
                                "Criptografia de PHI",
                                "Controles de acesso baseados em função",
                                "Logs de auditoria de acesso a PHI",
                                "Backup e recovery de dados",
                                "Transmissão segura de dados"
                            ],
                            "compliance_status": "Aplicável apenas se processando dados de saúde"
                        }
                    }
                    
                    regulation_data = regulatory_requirements.get(regulation, {})
                    
                    return f"Verificação regulatória {regulation}: {regulation_data}"
                    
                except Exception as e:
                    return f"Erro na verificação regulatória: {str(e)}"
        
        return RegulatoryComplianceChecker()
    
    def _create_risk_assessment_tool(self) -> BaseTool:
        """Ferramenta para avaliação de riscos de compliance"""
        class RiskAssessmentTool(BaseTool):
            name: str = "risk_assessment"
            description: str = "Avalia riscos de compliance e não conformidade"
            
            def _run(self, risk_category: str = "data_breach") -> str:
                try:
                    risk_assessments = {
                        "data_breach": {
                            "risk_level": "Alto",
                            "probability": "Média",
                            "impact": "Muito Alto",
                            "mitigation_controls": [
                                "Criptografia end-to-end",
                                "Monitoramento de acesso",
                                "DLP (Data Loss Prevention)",
                                "Treinamento de segurança",
                                "Plano de resposta a incidentes"
                            ],
                            "regulatory_impact": "Multas LGPD até 2% do faturamento"
                        },
                        "unauthorized_access": {
                            "risk_level": "Alto",
                            "probability": "Média",
                            "impact": "Alto",
                            "mitigation_controls": [
                                "MFA obrigatório",
                                "Princípio do menor privilégio",
                                "Revisões periódicas de acesso",
                                "Monitoramento de atividades privilegiadas",
                                "Segregação de funções"
                            ],
                            "regulatory_impact": "Violação de controles de acesso"
                        },
                        "data_loss": {
                            "risk_level": "Médio",
                            "probability": "Baixa",
                            "impact": "Alto",
                            "mitigation_controls": [
                                "Backup automatizado",
                                "Replicação cross-region",
                                "Testes de recovery",
                                "Versionamento de dados",
                                "Políticas de retenção"
                            ],
                            "regulatory_impact": "Perda de disponibilidade de dados"
                        },
                        "non_compliance": {
                            "risk_level": "Alto",
                            "probability": "Média",
                            "impact": "Muito Alto",
                            "mitigation_controls": [
                                "Auditorias regulares",
                                "Monitoramento de compliance",
                                "Treinamento de equipes",
                                "Documentação de processos",
                                "Revisões de políticas"
                            ],
                            "regulatory_impact": "Multas e sanções regulatórias"
                        }
                    }
                    
                    risk_data = risk_assessments.get(risk_category, {})
                    
                    return f"Avaliação de risco - {risk_category}: {risk_data}"
                    
                except Exception as e:
                    return f"Erro na avaliação de risco: {str(e)}"
        
        return RiskAssessmentTool()
    
    def create_compliance_analysis_task(self, analysis_scope: Dict[str, Any]) -> Task:
        """Cria tarefa de análise de conformidade"""
        return Task(
            description=f"""
            Realize uma análise completa de conformidade e compliance com o seguinte escopo:
            
            Escopo da Análise de Conformidade:
            - Frameworks: {analysis_scope.get('frameworks', ['ISO 27001', 'SOC 2'])}
            - Regulamentações: {analysis_scope.get('regulations', ['LGPD', 'GDPR'])}
            - Provedores: {analysis_scope.get('providers', ['AWS', 'GCP'])}
            - Tipos de dados: {analysis_scope.get('data_types', 'dados pessoais, dados financeiros')}
            - Criticidade: {analysis_scope.get('criticality', 'alta')}
            
            Análises a realizar:
            1. Verificação de conformidade com frameworks padrão
            2. Auditoria de controles de segurança implementados
            3. Análise de práticas de governança de dados
            4. Verificação de conformidade regulatória específica
            5. Avaliação de riscos de compliance
            
            Entregue um relatório de conformidade com:
            - Status de conformidade por framework/regulamentação
            - Gaps identificados e sua criticidade
            - Controles de segurança implementados vs. requeridos
            - Análise de riscos de não conformidade
            - Plano de adequação priorizado
            - Cronograma de implementação de controles
            
            Use suas ferramentas especializadas para análise precisa de compliance.
            """,
            agent=self.agent,
            expected_output="Relatório completo de análise de conformidade com plano de adequação"
        )
    
    def analyze_compliance_landscape(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise completa do cenário de conformidade"""
        try:
            self.logger.info("Iniciando análise de conformidade", extra=analysis_scope)
            
            # Criar e executar tarefa de análise
            analysis_task = self.create_compliance_analysis_task(analysis_scope)
            
            # Simular execução da tarefa (em implementação real seria via CrewAI)
            result = {
                "framework_compliance": "Verificação de frameworks concluída",
                "security_controls_audit": "Auditoria de controles concluída",
                "data_governance_analysis": "Análise de governança concluída",
                "regulatory_compliance": "Verificação regulatória concluída",
                "risk_assessment": "Avaliação de riscos concluída"
            }
            
            # Log específico para compliance
            self.logger.log_compliance_check({
                "frameworks": analysis_scope.get('frameworks', ['ISO 27001', 'SOC 2']),
                "regulations": analysis_scope.get('regulations', ['LGPD', 'GDPR']),
                "providers": analysis_scope.get('providers', ['AWS', 'GCP']),
                "analysis_completed": True
            })
            
            self.logger.info("Análise de conformidade concluída com sucesso")
            
            return {
                "status": "success",
                "analysis_type": "Compliance",
                "timestamp": datetime.now().isoformat(),
                "analysis_scope": analysis_scope,
                "results": result
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de conformidade: {str(e)}")
            return {
                "status": "error",
                "analysis_type": "Compliance",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "analysis_scope": analysis_scope
            }

def main():
    """Função principal para teste do agente"""
    compliance_coordinator = ComplianceCoordinatorAgent()
    
    # Exemplo de análise
    analysis_scope = {
        "frameworks": ["ISO 27001", "SOC 2"],
        "regulations": ["LGPD", "GDPR"],
        "providers": ["AWS", "GCP"],
        "data_types": "dados pessoais, dados financeiros",
        "criticality": "alta"
    }
    
    result = compliance_coordinator.analyze_compliance_landscape(analysis_scope)
    print(f"Resultado da análise de conformidade: {result}")

if __name__ == "__main__":
    main()

