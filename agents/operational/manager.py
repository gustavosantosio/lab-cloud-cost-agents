"""
Agente Operacional - Gerente Principal
Responsável por coordenar toda a cadeia de agentes do sistema
"""
import os
import sys
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from config.project_config import config
from agents.base.logger import AgentLogger
from agents.base.cloud_connector import CloudConnector

class ManagerAgent:
    """
    Agente Gerente Principal - Coordena todo o sistema de análise de custos
    """
    
    def __init__(self):
        self.logger = AgentLogger("ManagerAgent")
        self.cloud_connector = CloudConnector()
        self.agent = self._create_agent()
        self.specialists = {}
        self.coordinators = {}
        
    def _create_agent(self) -> Agent:
        """Cria o agente gerente principal"""
        return Agent(
            role="Gerente Principal de Análise de Custos Cloud",
            goal="Coordenar e orquestrar a análise completa de custos e recursos entre AWS e Google Cloud, "
                 "garantindo que todos os agentes especialistas e coordenadores trabalhem de forma sincronizada "
                 "para produzir relatórios precisos e recomendações otimizadas.",
            backstory="Você é um gerente experiente em análise de custos de infraestrutura cloud, "
                     "responsável por coordenar equipes especializadas em AWS e Google Cloud. "
                     "Sua expertise inclui otimização de custos, análise de SLA, conformidade "
                     "e tomada de decisões estratégicas baseadas em dados.",
            verbose=True,
            allow_delegation=True,
            tools=self._get_tools(),
            max_iter=config.agents.max_iterations,
            max_execution_time=config.agents.timeout_seconds
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Retorna as ferramentas disponíveis para o agente"""
        return [
            self._create_aws_connection_tool(),
            self._create_gcp_connection_tool(),
            self._create_agent_coordination_tool(),
            self._create_report_compilation_tool()
        ]
    
    def _create_aws_connection_tool(self) -> BaseTool:
        """Ferramenta para conectar e obter dados da AWS"""
        class AWSConnectionTool(BaseTool):
            name: str = "aws_connection"
            description: str = "Conecta-se à AWS e obtém dados de custos e recursos"
            
            def _run(self, query: str) -> str:
                try:
                    # Conectar via MCP AWS
                    result = self.cloud_connector.connect_aws()
                    return f"Conexão AWS estabelecida: {result}"
                except Exception as e:
                    return f"Erro na conexão AWS: {str(e)}"
        
        return AWSConnectionTool()
    
    def _create_gcp_connection_tool(self) -> BaseTool:
        """Ferramenta para conectar e obter dados do GCP"""
        class GCPConnectionTool(BaseTool):
            name: str = "gcp_connection"
            description: str = "Conecta-se ao Google Cloud e obtém dados de custos e recursos"
            
            def _run(self, query: str) -> str:
                try:
                    # Conectar via MCP GCP
                    result = self.cloud_connector.connect_gcp()
                    return f"Conexão GCP estabelecida: {result}"
                except Exception as e:
                    return f"Erro na conexão GCP: {str(e)}"
        
        return GCPConnectionTool()
    
    def _create_agent_coordination_tool(self) -> BaseTool:
        """Ferramenta para coordenar outros agentes"""
        class AgentCoordinationTool(BaseTool):
            name: str = "coordinate_agents"
            description: str = "Coordena a execução de agentes especialistas e coordenadores"
            
            def _run(self, agents_to_coordinate: str) -> str:
                try:
                    # Lógica de coordenação de agentes
                    return f"Agentes coordenados: {agents_to_coordinate}"
                except Exception as e:
                    return f"Erro na coordenação: {str(e)}"
        
        return AgentCoordinationTool()
    
    def _create_report_compilation_tool(self) -> BaseTool:
        """Ferramenta para compilar relatórios finais"""
        class ReportCompilationTool(BaseTool):
            name: str = "compile_report"
            description: str = "Compila dados de todos os agentes em um relatório final"
            
            def _run(self, data_sources: str) -> str:
                try:
                    # Lógica de compilação de relatório
                    return f"Relatório compilado com dados de: {data_sources}"
                except Exception as e:
                    return f"Erro na compilação: {str(e)}"
        
        return ReportCompilationTool()
    
    def create_analysis_task(self, analysis_scope: Dict[str, Any]) -> Task:
        """Cria tarefa de análise completa"""
        return Task(
            description=f"""
            Coordene uma análise completa de custos e recursos cloud com o seguinte escopo:
            
            Escopo da Análise:
            - Provedores: {analysis_scope.get('providers', ['AWS', 'GCP'])}
            - Período: {analysis_scope.get('period', 'último mês')}
            - Recursos: {analysis_scope.get('resources', 'todos')}
            - Foco: {analysis_scope.get('focus', 'otimização de custos')}
            
            Etapas a executar:
            1. Estabelecer conexões com AWS e GCP
            2. Coordenar agentes especialistas para coleta de dados
            3. Coordenar agentes de análise (SLA, custos, conformidade, jurídico)
            4. Compilar relatório final com recomendações
            5. Registrar todos os logs no sistema BigQuery
            
            Entregue um relatório estruturado com:
            - Resumo executivo
            - Análise detalhada por provedor
            - Recomendações de otimização
            - Análise de conformidade e aspectos jurídicos
            - Plano de ação prioritizado
            """,
            agent=self.agent,
            expected_output="Relatório completo de análise de custos cloud com recomendações estratégicas"
        )
    
    async def execute_analysis(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise completa coordenando todos os agentes"""
        try:
            self.logger.info("Iniciando análise completa de custos cloud", extra=analysis_scope)
            
            # Criar tarefa de análise
            analysis_task = self.create_analysis_task(analysis_scope)
            
            # Criar crew com o agente gerente
            crew = Crew(
                agents=[self.agent],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Executar análise
            result = crew.kickoff()
            
            self.logger.info("Análise completa finalizada com sucesso")
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "analysis_scope": analysis_scope
            }
            
        except Exception as e:
            self.logger.error(f"Erro na execução da análise: {str(e)}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "analysis_scope": analysis_scope
            }
    
    def register_specialist_agent(self, agent_type: str, agent_instance):
        """Registra um agente especialista"""
        self.specialists[agent_type] = agent_instance
        self.logger.info(f"Agente especialista registrado: {agent_type}")
    
    def register_coordinator_agent(self, agent_type: str, agent_instance):
        """Registra um agente coordenador"""
        self.coordinators[agent_type] = agent_instance
        self.logger.info(f"Agente coordenador registrado: {agent_type}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status do sistema de agentes"""
        return {
            "manager_status": "active",
            "specialists_count": len(self.specialists),
            "coordinators_count": len(self.coordinators),
            "cloud_connections": {
                "aws": self.cloud_connector.is_aws_connected(),
                "gcp": self.cloud_connector.is_gcp_connected()
            },
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Função principal para teste do agente"""
    manager = ManagerAgent()
    
    # Exemplo de análise
    analysis_scope = {
        "providers": ["AWS", "GCP"],
        "period": "último mês",
        "resources": "compute, storage, networking",
        "focus": "otimização de custos e conformidade"
    }
    
    # Executar análise (em ambiente real seria async)
    result = asyncio.run(manager.execute_analysis(analysis_scope))
    print(f"Resultado da análise: {result}")

if __name__ == "__main__":
    main()

