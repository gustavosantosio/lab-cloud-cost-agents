"""
Servidor MCP para SLA - Model Context Protocol
Responsável por comparação e análise de SLA entre provedores
"""
import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mcp import MCPServer, Tool, Resource
from config.project_config import config
from agents.base.logger import AgentLogger

class SLAMCPServer:
    """
    Servidor MCP para SLA - Fornece análise e comparação de SLA entre provedores
    """
    
    def __init__(self):
        self.logger = AgentLogger("SLAMCPServer")
        self.server = MCPServer("sla-analysis-api")
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Registra ferramentas MCP para análise de SLA"""
        
        @self.server.tool("compare_sla_metrics")
        async def compare_sla_metrics(
            service_type: str = "compute",
            providers: List[str] = ["aws", "gcp"]
        ) -> Dict[str, Any]:
            """
            Compara métricas de SLA entre provedores
            
            Args:
                service_type: Tipo de serviço (compute, storage, database, etc.)
                providers: Lista de provedores para comparar
            """
            try:
                sla_database = {
                    "compute": {
                        "aws": {
                            "service_name": "Amazon EC2",
                            "availability_sla": "99.99%",
                            "monthly_uptime_percentage": 99.99,
                            "service_credit_policy": {
                                "99.0_to_99.99": "10%",
                                "95.0_to_99.0": "30%",
                                "below_95.0": "100%"
                            },
                            "measurement_period": "Monthly",
                            "exclusions": [
                                "Scheduled maintenance",
                                "Customer-initiated actions",
                                "Force majeure events"
                            ]
                        },
                        "gcp": {
                            "service_name": "Compute Engine",
                            "availability_sla": "99.99%",
                            "monthly_uptime_percentage": 99.99,
                            "service_credit_policy": {
                                "99.0_to_99.99": "10%",
                                "95.0_to_99.0": "25%",
                                "below_95.0": "50%"
                            },
                            "measurement_period": "Monthly",
                            "exclusions": [
                                "Scheduled maintenance",
                                "Customer configuration issues",
                                "Force majeure events"
                            ]
                        }
                    },
                    "storage": {
                        "aws": {
                            "service_name": "Amazon S3",
                            "availability_sla": "99.9%",
                            "durability_sla": "99.999999999%",
                            "monthly_uptime_percentage": 99.9,
                            "service_credit_policy": {
                                "99.0_to_99.9": "10%",
                                "95.0_to_99.0": "25%",
                                "below_95.0": "100%"
                            }
                        },
                        "gcp": {
                            "service_name": "Cloud Storage",
                            "availability_sla": "99.9%",
                            "durability_sla": "99.999999999%",
                            "monthly_uptime_percentage": 99.9,
                            "service_credit_policy": {
                                "99.0_to_99.9": "5%",
                                "95.0_to_99.0": "10%",
                                "below_95.0": "25%"
                            }
                        }
                    },
                    "database": {
                        "aws": {
                            "service_name": "Amazon RDS (Multi-AZ)",
                            "availability_sla": "99.95%",
                            "monthly_uptime_percentage": 99.95,
                            "service_credit_policy": {
                                "99.0_to_99.95": "10%",
                                "95.0_to_99.0": "25%",
                                "below_95.0": "100%"
                            }
                        },
                        "gcp": {
                            "service_name": "Cloud SQL (Regional)",
                            "availability_sla": "99.95%",
                            "monthly_uptime_percentage": 99.95,
                            "service_credit_policy": {
                                "99.0_to_99.95": "10%",
                                "95.0_to_99.0": "25%",
                                "below_95.0": "50%"
                            }
                        }
                    }
                }
                
                comparison_result = {}
                service_data = sla_database.get(service_type, {})
                
                for provider in providers:
                    if provider in service_data:
                        comparison_result[provider] = service_data[provider]
                
                self.logger.info("Comparação de SLA realizada", {
                    "service_type": service_type,
                    "providers": providers,
                    "metrics_compared": len(comparison_result)
                })
                
                return {
                    "success": True,
                    "service_type": service_type,
                    "providers_compared": providers,
                    "comparison_data": comparison_result,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro na comparação de SLA: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_historical_uptime")
        async def get_historical_uptime(
            provider: str,
            service: str,
            period_months: int = 12
        ) -> Dict[str, Any]:
            """
            Obtém dados históricos de uptime
            
            Args:
                provider: Provedor (aws, gcp)
                service: Serviço específico
                period_months: Período em meses para análise
            """
            try:
                # Dados simulados baseados em relatórios públicos de status
                historical_data = {
                    "aws": {
                        "ec2": {
                            "last_12_months": [
                                {"month": "2024-01", "uptime": 99.98},
                                {"month": "2024-02", "uptime": 99.99},
                                {"month": "2024-03", "uptime": 99.97},
                                {"month": "2024-04", "uptime": 99.99},
                                {"month": "2024-05", "uptime": 99.98},
                                {"month": "2024-06", "uptime": 99.99},
                                {"month": "2024-07", "uptime": 99.96},
                                {"month": "2024-08", "uptime": 99.99},
                                {"month": "2024-09", "uptime": 99.98},
                                {"month": "2024-10", "uptime": 99.99},
                                {"month": "2024-11", "uptime": 99.97},
                                {"month": "2024-12", "uptime": 99.98}
                            ],
                            "average_uptime": 99.98,
                            "incidents_count": 3,
                            "major_incidents": 1
                        },
                        "s3": {
                            "last_12_months": [
                                {"month": "2024-01", "uptime": 99.95},
                                {"month": "2024-02", "uptime": 99.98},
                                {"month": "2024-03", "uptime": 99.99},
                                {"month": "2024-04", "uptime": 99.97},
                                {"month": "2024-05", "uptime": 99.99},
                                {"month": "2024-06", "uptime": 99.98},
                                {"month": "2024-07", "uptime": 99.99},
                                {"month": "2024-08", "uptime": 99.96},
                                {"month": "2024-09", "uptime": 99.99},
                                {"month": "2024-10", "uptime": 99.98},
                                {"month": "2024-11", "uptime": 99.99},
                                {"month": "2024-12", "uptime": 99.97}
                            ],
                            "average_uptime": 99.97,
                            "incidents_count": 2,
                            "major_incidents": 0
                        }
                    },
                    "gcp": {
                        "compute": {
                            "last_12_months": [
                                {"month": "2024-01", "uptime": 99.97},
                                {"month": "2024-02", "uptime": 99.98},
                                {"month": "2024-03", "uptime": 99.96},
                                {"month": "2024-04", "uptime": 99.99},
                                {"month": "2024-05", "uptime": 99.97},
                                {"month": "2024-06", "uptime": 99.98},
                                {"month": "2024-07", "uptime": 99.99},
                                {"month": "2024-08", "uptime": 99.95},
                                {"month": "2024-09", "uptime": 99.98},
                                {"month": "2024-10", "uptime": 99.99},
                                {"month": "2024-11", "uptime": 99.96},
                                {"month": "2024-12", "uptime": 99.98}
                            ],
                            "average_uptime": 99.97,
                            "incidents_count": 4,
                            "major_incidents": 2
                        },
                        "storage": {
                            "last_12_months": [
                                {"month": "2024-01", "uptime": 99.98},
                                {"month": "2024-02", "uptime": 99.99},
                                {"month": "2024-03", "uptime": 99.97},
                                {"month": "2024-04", "uptime": 99.98},
                                {"month": "2024-05", "uptime": 99.99},
                                {"month": "2024-06", "uptime": 99.96},
                                {"month": "2024-07", "uptime": 99.98},
                                {"month": "2024-08", "uptime": 99.99},
                                {"month": "2024-09", "uptime": 99.97},
                                {"month": "2024-10", "uptime": 99.98},
                                {"month": "2024-11", "uptime": 99.99},
                                {"month": "2024-12", "uptime": 99.96}
                            ],
                            "average_uptime": 99.98,
                            "incidents_count": 2,
                            "major_incidents": 1
                        }
                    }
                }
                
                provider_data = historical_data.get(provider, {})
                service_data = provider_data.get(service, {})
                
                if not service_data:
                    return {"error": f"Dados não encontrados para {provider}/{service}"}
                
                # Filtrar dados pelo período solicitado
                filtered_data = service_data["last_12_months"][-period_months:]
                
                self.logger.info("Dados históricos de uptime obtidos", {
                    "provider": provider,
                    "service": service,
                    "period_months": period_months,
                    "data_points": len(filtered_data)
                })
                
                return {
                    "success": True,
                    "provider": provider,
                    "service": service,
                    "period_months": period_months,
                    "historical_data": filtered_data,
                    "summary": {
                        "average_uptime": service_data["average_uptime"],
                        "incidents_count": service_data["incidents_count"],
                        "major_incidents": service_data["major_incidents"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao obter dados históricos: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("calculate_sla_impact")
        async def calculate_sla_impact(
            current_uptime: float,
            target_uptime: float,
            monthly_revenue: float
        ) -> Dict[str, Any]:
            """
            Calcula impacto financeiro de não cumprimento de SLA
            
            Args:
                current_uptime: Uptime atual (%)
                target_uptime: Uptime alvo do SLA (%)
                monthly_revenue: Receita mensal afetada
            """
            try:
                # Calcular downtime
                current_downtime_minutes = (100 - current_uptime) * 43200 / 100  # 43200 min/mês
                target_downtime_minutes = (100 - target_uptime) * 43200 / 100
                
                # Calcular impacto
                sla_breach = current_uptime < target_uptime
                downtime_difference = current_downtime_minutes - target_downtime_minutes if sla_breach else 0
                
                # Estimar perdas (simplificado)
                revenue_per_minute = monthly_revenue / 43200
                estimated_loss = downtime_difference * revenue_per_minute if sla_breach else 0
                
                # Calcular créditos de serviço baseado em faixas típicas
                service_credit_percentage = 0
                if sla_breach:
                    if current_uptime >= 99.0:
                        service_credit_percentage = 10
                    elif current_uptime >= 95.0:
                        service_credit_percentage = 25
                    else:
                        service_credit_percentage = 100
                
                service_credit_amount = (service_credit_percentage / 100) * monthly_revenue
                
                impact_analysis = {
                    "sla_breach": sla_breach,
                    "current_uptime": current_uptime,
                    "target_uptime": target_uptime,
                    "current_downtime_minutes": round(current_downtime_minutes, 2),
                    "target_downtime_minutes": round(target_downtime_minutes, 2),
                    "excess_downtime_minutes": round(downtime_difference, 2),
                    "estimated_revenue_loss": round(estimated_loss, 2),
                    "service_credit_percentage": service_credit_percentage,
                    "service_credit_amount": round(service_credit_amount, 2),
                    "total_financial_impact": round(estimated_loss + service_credit_amount, 2)
                }
                
                self.logger.info("Impacto de SLA calculado", {
                    "sla_breach": sla_breach,
                    "financial_impact": impact_analysis["total_financial_impact"]
                })
                
                return {
                    "success": True,
                    "impact_analysis": impact_analysis,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro no cálculo de impacto: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("generate_sla_report")
        async def generate_sla_report(
            providers: List[str] = ["aws", "gcp"],
            services: List[str] = ["compute", "storage", "database"]
        ) -> Dict[str, Any]:
            """
            Gera relatório comparativo de SLA
            
            Args:
                providers: Lista de provedores
                services: Lista de serviços
            """
            try:
                report_data = {
                    "report_metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "providers_analyzed": providers,
                        "services_analyzed": services,
                        "analysis_period": "Last 12 months"
                    },
                    "sla_comparisons": {},
                    "historical_performance": {},
                    "recommendations": []
                }
                
                # Comparar SLAs para cada serviço
                for service in services:
                    comparison = await self.server.tools["compare_sla_metrics"](service, providers)
                    if comparison.get("success"):
                        report_data["sla_comparisons"][service] = comparison["comparison_data"]
                
                # Obter dados históricos
                for provider in providers:
                    provider_historical = {}
                    for service in services:
                        service_map = {"compute": "ec2" if provider == "aws" else "compute",
                                     "storage": "s3" if provider == "aws" else "storage",
                                     "database": "rds" if provider == "aws" else "sql"}
                        
                        historical = await self.server.tools["get_historical_uptime"](
                            provider, service_map.get(service, service), 12
                        )
                        if historical.get("success"):
                            provider_historical[service] = historical["summary"]
                    
                    report_data["historical_performance"][provider] = provider_historical
                
                # Gerar recomendações
                recommendations = [
                    "Implementar monitoramento proativo de SLA",
                    "Estabelecer alertas para degradação de performance",
                    "Considerar estratégia multi-cloud para alta disponibilidade",
                    "Revisar contratos de SLA com foco em créditos de serviço",
                    "Implementar testes regulares de disaster recovery"
                ]
                
                report_data["recommendations"] = recommendations
                
                self.logger.info("Relatório de SLA gerado", {
                    "providers_count": len(providers),
                    "services_count": len(services),
                    "recommendations_count": len(recommendations)
                })
                
                return {
                    "success": True,
                    "report": report_data,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro na geração de relatório: {str(e)}")
                return {"error": str(e)}
    
    def _register_resources(self):
        """Registra recursos MCP para SLA"""
        
        @self.server.resource("sla://comparison/all-services")
        async def all_services_comparison() -> Dict[str, Any]:
            """
            Recurso que fornece comparação de todos os serviços
            """
            try:
                services = ["compute", "storage", "database"]
                providers = ["aws", "gcp"]
                
                comparisons = {}
                for service in services:
                    comparison = await self.server.tools["compare_sla_metrics"](service, providers)
                    if comparison.get("success"):
                        comparisons[service] = comparison["comparison_data"]
                
                return {
                    "resource_type": "sla_comparison",
                    "data": comparisons,
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"error": str(e)}
        
        @self.server.resource("sla://performance/summary")
        async def performance_summary() -> Dict[str, Any]:
            """
            Recurso que fornece resumo de performance
            """
            try:
                providers = ["aws", "gcp"]
                services = ["compute", "storage"]
                
                performance_data = {}
                for provider in providers:
                    provider_data = {}
                    for service in services:
                        service_map = {"compute": "ec2" if provider == "aws" else "compute",
                                     "storage": "s3" if provider == "aws" else "storage"}
                        
                        historical = await self.server.tools["get_historical_uptime"](
                            provider, service_map[service], 3
                        )
                        if historical.get("success"):
                            provider_data[service] = historical["summary"]
                    
                    performance_data[provider] = provider_data
                
                return {
                    "resource_type": "performance_summary",
                    "data": performance_data,
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"error": str(e)}
    
    async def start_server(self, host: str = "0.0.0.0", port: int = None):
        """Inicia o servidor MCP"""
        server_port = port or config.mcp.sla_port
        
        try:
            self.logger.info(f"Iniciando SLA MCP Server em {host}:{server_port}")
            await self.server.start(host=host, port=server_port)
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar SLA MCP Server: {str(e)}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """Retorna informações do servidor"""
        return {
            "name": "SLA MCP Server",
            "version": "1.0.0",
            "description": "Servidor MCP para análise e comparação de SLA",
            "port": config.mcp.sla_port,
            "tools_count": len(self.server.tools),
            "resources_count": len(self.server.resources)
        }

async def main():
    """Função principal para executar o servidor"""
    sla_mcp = SLAMCPServer()
    
    try:
        await sla_mcp.start_server()
    except KeyboardInterrupt:
        print("Servidor SLA MCP interrompido pelo usuário")
    except Exception as e:
        print(f"Erro no servidor SLA MCP: {e}")

if __name__ == "__main__":
    asyncio.run(main())

