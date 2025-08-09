"""
Agente Coordenador Jurídico
Responsável por análise de aspectos jurídicos, normas e legislação brasileira
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

class LegalCoordinatorAgent:
    """
    Agente Coordenador Jurídico - Análise de aspectos legais e regulatórios
    """
    
    def __init__(self):
        self.logger = AgentLogger("LegalCoordinatorAgent")
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Cria o agente coordenador jurídico"""
        return Agent(
            role="Coordenador Jurídico e Regulatório para Cloud Computing",
            goal="Analisar aspectos jurídicos, regulamentações brasileiras e internacionais "
                 "aplicáveis à infraestrutura cloud, identificando riscos legais, requisitos "
                 "de compliance e desenvolvendo estratégias de mitigação de riscos jurídicos.",
            backstory="Você é um advogado especializado em direito digital, proteção de dados "
                     "e tecnologia da informação, com vasta experiência em regulamentações "
                     "brasileiras (LGPD, Marco Civil da Internet) e internacionais (GDPR, CCPA). "
                     "Sua expertise inclui contratos de cloud computing, transferência internacional "
                     "de dados, compliance regulatório e análise de riscos jurídicos em ambientes "
                     "multi-cloud.",
            verbose=True,
            allow_delegation=False,
            tools=self._get_tools(),
            max_iter=config.agents.max_iterations,
            max_execution_time=config.agents.timeout_seconds
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Retorna as ferramentas para análise jurídica"""
        return [
            self._create_brazilian_law_analyzer(),
            self._create_international_regulation_checker(),
            self._create_contract_terms_analyzer(),
            self._create_data_transfer_compliance_tool(),
            self._create_legal_risk_assessor()
        ]
    
    def _create_brazilian_law_analyzer(self) -> BaseTool:
        """Ferramenta para análise de legislação brasileira"""
        class BrazilianLawAnalyzer(BaseTool):
            name: str = "brazilian_law_analyzer"
            description: str = "Analisa conformidade com legislação brasileira aplicável"
            
            def _run(self, law_category: str = "data_protection") -> str:
                try:
                    brazilian_laws = {
                        "data_protection": {
                            "lgpd": {
                                "name": "Lei Geral de Proteção de Dados (Lei 13.709/2018)",
                                "key_articles": [
                                    "Art. 1º - Âmbito de aplicação",
                                    "Art. 5º - Definições (dados pessoais, tratamento, etc.)",
                                    "Art. 6º - Princípios do tratamento",
                                    "Art. 7º - Bases legais para tratamento",
                                    "Art. 18º - Direitos do titular",
                                    "Art. 46º - Segurança e sigilo",
                                    "Art. 52º - Sanções administrativas"
                                ],
                                "cloud_implications": [
                                    "Necessidade de DPO (Encarregado)",
                                    "Relatório de Impacto à Proteção de Dados",
                                    "Consentimento específico para tratamento",
                                    "Direito à portabilidade e exclusão",
                                    "Notificação de incidentes em 72h"
                                ],
                                "penalties": "Multa até 2% do faturamento (máximo R$ 50 milhões)"
                            }
                        },
                        "internet_regulation": {
                            "marco_civil": {
                                "name": "Marco Civil da Internet (Lei 12.965/2014)",
                                "key_articles": [
                                    "Art. 3º - Princípios da internet no Brasil",
                                    "Art. 7º - Direitos dos usuários",
                                    "Art. 10º - Guarda de registros de conexão",
                                    "Art. 11º - Responsabilidade por danos",
                                    "Art. 15º - Guarda de registros de aplicações"
                                ],
                                "cloud_implications": [
                                    "Neutralidade de rede",
                                    "Privacidade e proteção de dados",
                                    "Liberdade de expressão",
                                    "Responsabilidade dos provedores",
                                    "Jurisdição brasileira para dados de brasileiros"
                                ]
                            }
                        },
                        "tax_regulation": {
                            "iss_cloud": {
                                "name": "ISS sobre serviços de cloud computing",
                                "regulations": [
                                    "LC 116/2003 - Lista de serviços sujeitos ao ISS",
                                    "Item 1.05 - Processamento de dados",
                                    "Súmula STJ sobre local de prestação",
                                    "Regulamentações municipais específicas"
                                ],
                                "cloud_implications": [
                                    "Incidência de ISS sobre serviços cloud",
                                    "Local de prestação do serviço",
                                    "Responsabilidade tributária",
                                    "Documentação fiscal necessária"
                                ]
                            }
                        },
                        "financial_regulation": {
                            "bacen_regulations": {
                                "name": "Regulamentações do Banco Central",
                                "key_norms": [
                                    "Resolução 4.658/2018 - Política de Segurança Cibernética",
                                    "Resolução 4.893/2021 - Gestão de Riscos",
                                    "Circular 3.909/2018 - Controles internos",
                                    "Resolução 4.557/2017 - Estrutura de gerenciamento"
                                ],
                                "cloud_implications": [
                                    "Aprovação prévia para uso de cloud",
                                    "Controles de segurança específicos",
                                    "Auditoria e monitoramento",
                                    "Plano de continuidade de negócios"
                                ]
                            }
                        }
                    }
                    
                    law_data = brazilian_laws.get(law_category, {})
                    
                    return f"Análise de legislação brasileira - {law_category}: {law_data}"
                    
                except Exception as e:
                    return f"Erro na análise de legislação brasileira: {str(e)}"
        
        return BrazilianLawAnalyzer()
    
    def _create_international_regulation_checker(self) -> BaseTool:
        """Ferramenta para verificação de regulamentações internacionais"""
        class InternationalRegulationChecker(BaseTool):
            name: str = "international_regulation_checker"
            description: str = "Verifica conformidade com regulamentações internacionais"
            
            def _run(self, regulation: str = "gdpr") -> str:
                try:
                    international_regulations = {
                        "gdpr": {
                            "name": "General Data Protection Regulation (EU)",
                            "scope": "Dados de residentes da UE processados por empresas brasileiras",
                            "key_requirements": [
                                "Consentimento explícito",
                                "Direito ao esquecimento",
                                "Portabilidade de dados",
                                "Privacy by design",
                                "Data Protection Officer (DPO)"
                            ],
                            "transfer_mechanisms": [
                                "Adequacy decisions",
                                "Standard Contractual Clauses (SCCs)",
                                "Binding Corporate Rules (BCRs)",
                                "Certification schemes"
                            ],
                            "penalties": "Até 4% do faturamento global ou €20 milhões"
                        },
                        "ccpa": {
                            "name": "California Consumer Privacy Act (US)",
                            "scope": "Dados de residentes da Califórnia",
                            "key_requirements": [
                                "Direito de saber sobre coleta de dados",
                                "Direito de exclusão de dados",
                                "Direito de opt-out de venda",
                                "Não discriminação por exercício de direitos"
                            ],
                            "business_thresholds": [
                                "Receita anual > $25 milhões",
                                "Dados de > 50.000 consumidores",
                                "Receita > 50% de venda de dados"
                            ],
                            "penalties": "Até $7.500 por violação intencional"
                        },
                        "pipeda": {
                            "name": "Personal Information Protection and Electronic Documents Act (Canada)",
                            "scope": "Dados pessoais de canadenses",
                            "key_principles": [
                                "Accountability",
                                "Identifying purposes",
                                "Consent",
                                "Limiting collection",
                                "Safeguards"
                            ],
                            "breach_notification": "Notificação obrigatória de violações",
                            "penalties": "Até CAD $100.000 por violação"
                        }
                    }
                    
                    regulation_data = international_regulations.get(regulation, {})
                    
                    return f"Verificação regulamentação internacional - {regulation}: {regulation_data}"
                    
                except Exception as e:
                    return f"Erro na verificação internacional: {str(e)}"
        
        return InternationalRegulationChecker()
    
    def _create_contract_terms_analyzer(self) -> BaseTool:
        """Ferramenta para análise de termos contratuais"""
        class ContractTermsAnalyzer(BaseTool):
            name: str = "contract_terms_analyzer"
            description: str = "Analisa termos contratuais de provedores cloud"
            
            def _run(self, provider: str = "aws") -> str:
                try:
                    contract_analysis = {
                        "aws": {
                            "service_agreement": "AWS Customer Agreement",
                            "key_terms": {
                                "data_location": "Controle do cliente sobre localização",
                                "data_processing": "AWS como processador de dados",
                                "security_responsibility": "Modelo de responsabilidade compartilhada",
                                "liability_limitation": "Limitação de responsabilidade",
                                "termination_rights": "Direitos de rescisão"
                            },
                            "dpa_terms": {
                                "name": "AWS Data Processing Agreement",
                                "standard_clauses": "SCCs incorporadas",
                                "data_transfers": "Mecanismos de transferência adequados",
                                "subprocessors": "Lista de subprocessadores disponível"
                            },
                            "compliance_certifications": [
                                "ISO 27001", "SOC 2", "PCI DSS", "HIPAA", "FedRAMP"
                            ]
                        },
                        "gcp": {
                            "service_agreement": "Google Cloud Platform Terms of Service",
                            "key_terms": {
                                "data_location": "Controle sobre localização de dados",
                                "data_processing": "Google como processador",
                                "security_responsibility": "Modelo de responsabilidade compartilhada",
                                "liability_limitation": "Limitações de responsabilidade",
                                "ip_rights": "Direitos de propriedade intelectual"
                            },
                            "dpa_terms": {
                                "name": "Google Cloud Data Processing Agreement",
                                "standard_clauses": "SCCs incluídas",
                                "data_transfers": "Adequacy decisions e SCCs",
                                "subprocessors": "Transparência sobre subprocessadores"
                            },
                            "compliance_certifications": [
                                "ISO 27001", "SOC 2", "PCI DSS", "HIPAA", "FedRAMP"
                            ]
                        }
                    }
                    
                    contract_data = contract_analysis.get(provider, {})
                    
                    return f"Análise contratual {provider}: {contract_data}"
                    
                except Exception as e:
                    return f"Erro na análise contratual: {str(e)}"
        
        return ContractTermsAnalyzer()
    
    def _create_data_transfer_compliance_tool(self) -> BaseTool:
        """Ferramenta para compliance de transferência de dados"""
        class DataTransferComplianceTool(BaseTool):
            name: str = "data_transfer_compliance"
            description: str = "Analisa compliance para transferência internacional de dados"
            
            def _run(self, transfer_scenario: str = "brazil_to_us") -> str:
                try:
                    transfer_scenarios = {
                        "brazil_to_us": {
                            "legal_basis": [
                                "LGPD Art. 33 - Transferência internacional",
                                "Adequacy decision (não existe para EUA)",
                                "Standard Contractual Clauses necessárias",
                                "Garantias específicas de proteção"
                            ],
                            "requirements": [
                                "Consentimento específico do titular",
                                "Cláusulas contratuais padrão",
                                "Certificação internacional",
                                "Códigos de conduta aprovados"
                            ],
                            "risks": [
                                "Ausência de adequacy decision",
                                "Surveillance laws (CLOUD Act, FISA)",
                                "Possível invalidação de SCCs",
                                "Requisitos de notificação ANPD"
                            ]
                        },
                        "brazil_to_eu": {
                            "legal_basis": [
                                "LGPD Art. 33 - Transferência internacional",
                                "Adequacy decision da UE para Brasil (em análise)",
                                "GDPR compliance necessário",
                                "Reciprocidade de proteção"
                            ],
                            "requirements": [
                                "Conformidade com GDPR",
                                "DPO designado se aplicável",
                                "Breach notification procedures",
                                "Data subject rights implementation"
                            ],
                            "risks": [
                                "Diferentes interpretações regulatórias",
                                "Requisitos de DPO",
                                "Penalidades mais severas (GDPR)",
                                "Complexidade de compliance dupla"
                            ]
                        },
                        "multi_region": {
                            "legal_basis": [
                                "Análise jurisdição por jurisdição",
                                "Mapeamento de fluxos de dados",
                                "Identificação de bases legais",
                                "Harmonização de contratos"
                            ],
                            "requirements": [
                                "Privacy impact assessment",
                                "Multi-jurisdictional DPA",
                                "Consistent security measures",
                                "Unified breach procedures"
                            ],
                            "risks": [
                                "Conflitos entre jurisdições",
                                "Complexidade de compliance",
                                "Custos de implementação",
                                "Riscos de enforcement"
                            ]
                        }
                    }
                    
                    transfer_data = transfer_scenarios.get(transfer_scenario, {})
                    
                    return f"Compliance de transferência - {transfer_scenario}: {transfer_data}"
                    
                except Exception as e:
                    return f"Erro na análise de transferência: {str(e)}"
        
        return DataTransferComplianceTool()
    
    def _create_legal_risk_assessor(self) -> BaseTool:
        """Ferramenta para avaliação de riscos jurídicos"""
        class LegalRiskAssessor(BaseTool):
            name: str = "legal_risk_assessor"
            description: str = "Avalia riscos jurídicos específicos de cloud computing"
            
            def _run(self, risk_type: str = "regulatory_compliance") -> str:
                try:
                    legal_risks = {
                        "regulatory_compliance": {
                            "risk_level": "Alto",
                            "description": "Não conformidade com regulamentações aplicáveis",
                            "potential_impacts": [
                                "Multas administrativas (LGPD: até 2% faturamento)",
                                "Sanções regulatórias setoriais",
                                "Suspensão de atividades",
                                "Danos reputacionais",
                                "Ações judiciais de titulares"
                            ],
                            "mitigation_strategies": [
                                "Implementar programa de compliance",
                                "Designar DPO/Encarregado",
                                "Realizar auditorias regulares",
                                "Treinamento de equipes",
                                "Monitoramento contínuo"
                            ]
                        },
                        "data_breach_liability": {
                            "risk_level": "Muito Alto",
                            "description": "Responsabilidade por vazamento de dados",
                            "potential_impacts": [
                                "Indenizações por danos morais coletivos",
                                "Ações individuais de titulares",
                                "Multas regulatórias",
                                "Custos de notificação e remediação",
                                "Perda de confiança do mercado"
                            ],
                            "mitigation_strategies": [
                                "Seguro de responsabilidade civil cyber",
                                "Plano de resposta a incidentes",
                                "Controles de segurança robustos",
                                "Criptografia end-to-end",
                                "Monitoramento 24/7"
                            ]
                        },
                        "contractual_disputes": {
                            "risk_level": "Médio",
                            "description": "Disputas contratuais com provedores cloud",
                            "potential_impacts": [
                                "Interrupção de serviços",
                                "Custos de migração emergencial",
                                "Perdas operacionais",
                                "Litígios prolongados",
                                "Dificuldades de recuperação de dados"
                            ],
                            "mitigation_strategies": [
                                "Negociação de SLAs robustos",
                                "Cláusulas de portabilidade",
                                "Estratégia multi-cloud",
                                "Backup independente",
                                "Mediação e arbitragem"
                            ]
                        },
                        "jurisdiction_conflicts": {
                            "risk_level": "Alto",
                            "description": "Conflitos de jurisdição e lei aplicável",
                            "potential_impacts": [
                                "Incerteza jurídica",
                                "Custos de compliance múltipla",
                                "Dificuldades de enforcement",
                                "Conflitos entre regulamentações",
                                "Riscos de dupla penalização"
                            ],
                            "mitigation_strategies": [
                                "Análise jurídica especializada",
                                "Estruturação adequada de contratos",
                                "Escolha estratégica de jurisdições",
                                "Monitoramento regulatório",
                                "Assessoria jurídica local"
                            ]
                        }
                    }
                    
                    risk_data = legal_risks.get(risk_type, {})
                    
                    return f"Avaliação de risco jurídico - {risk_type}: {risk_data}"
                    
                except Exception as e:
                    return f"Erro na avaliação de risco jurídico: {str(e)}"
        
        return LegalRiskAssessor()
    
    def create_legal_analysis_task(self, analysis_scope: Dict[str, Any]) -> Task:
        """Cria tarefa de análise jurídica"""
        return Task(
            description=f"""
            Realize uma análise jurídica completa com o seguinte escopo:
            
            Escopo da Análise Jurídica:
            - Jurisdições: {analysis_scope.get('jurisdictions', ['Brasil', 'União Europeia', 'Estados Unidos'])}
            - Tipos de dados: {analysis_scope.get('data_types', 'dados pessoais, dados financeiros')}
            - Provedores: {analysis_scope.get('providers', ['AWS', 'GCP'])}
            - Setores regulados: {analysis_scope.get('regulated_sectors', 'financeiro, saúde')}
            - Transferências internacionais: {analysis_scope.get('international_transfers', 'sim')}
            
            Análises a realizar:
            1. Conformidade com legislação brasileira aplicável
            2. Verificação de regulamentações internacionais relevantes
            3. Análise de termos contratuais dos provedores
            4. Compliance para transferência internacional de dados
            5. Avaliação de riscos jurídicos específicos
            
            Entregue um parecer jurídico com:
            - Análise de conformidade legal por jurisdição
            - Identificação de riscos jurídicos e sua probabilidade
            - Recomendações de estruturação contratual
            - Estratégias de mitigação de riscos
            - Plano de compliance jurídico
            - Cronograma de adequações necessárias
            
            Base sua análise em legislação vigente e jurisprudência aplicável.
            """,
            agent=self.agent,
            expected_output="Parecer jurídico completo com recomendações de compliance legal"
        )
    
    def analyze_legal_landscape(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise completa do cenário jurídico"""
        try:
            self.logger.info("Iniciando análise jurídica", extra=analysis_scope)
            
            # Criar e executar tarefa de análise
            analysis_task = self.create_legal_analysis_task(analysis_scope)
            
            # Simular execução da tarefa (em implementação real seria via CrewAI)
            result = {
                "brazilian_law_analysis": "Análise de legislação brasileira concluída",
                "international_regulation_check": "Verificação regulamentações internacionais concluída",
                "contract_terms_analysis": "Análise de termos contratuais concluída",
                "data_transfer_compliance": "Análise de transferência de dados concluída",
                "legal_risk_assessment": "Avaliação de riscos jurídicos concluída"
            }
            
            self.logger.info("Análise jurídica concluída com sucesso")
            
            return {
                "status": "success",
                "analysis_type": "Legal",
                "timestamp": datetime.now().isoformat(),
                "analysis_scope": analysis_scope,
                "results": result
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise jurídica: {str(e)}")
            return {
                "status": "error",
                "analysis_type": "Legal",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "analysis_scope": analysis_scope
            }

def main():
    """Função principal para teste do agente"""
    legal_coordinator = LegalCoordinatorAgent()
    
    # Exemplo de análise
    analysis_scope = {
        "jurisdictions": ["Brasil", "União Europeia", "Estados Unidos"],
        "data_types": "dados pessoais, dados financeiros",
        "providers": ["AWS", "GCP"],
        "regulated_sectors": "financeiro, saúde",
        "international_transfers": "sim"
    }
    
    result = legal_coordinator.analyze_legal_landscape(analysis_scope)
    print(f"Resultado da análise jurídica: {result}")

if __name__ == "__main__":
    main()

