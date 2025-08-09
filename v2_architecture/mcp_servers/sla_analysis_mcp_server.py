"""
Cloud Cost Agent v2 - SLA Analysis MCP Server
Servidor MCP especializado para análise de SLAs de provedores de nuvem
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import os
import sys
from aiohttp import ClientSession
import statistics
from enum import Enum

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ListResourcesRequest, ListResourcesResult,
    ListToolsRequest, ListToolsResult, ReadResourceRequest, ReadResourceResult
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sla_analysis_mcp_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SLAType(Enum):
    """Tipos de SLA"""
    UPTIME = "uptime"
    PERFORMANCE = "performance"
    SUPPORT = "support"
    AVAILABILITY = "availability"
    LATENCY = "latency"
    THROUGHPUT = "throughput"


class SeverityLevel(Enum):
    """Níveis de severidade"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SLAIncident:
    """Incidente de SLA"""
    incident_id: str
    start_time: datetime
    end_time: Optional[datetime]
    severity: SeverityLevel
    impact_description: str
    affected_services: List[str]
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    downtime_minutes: Optional[int] = None


@dataclass
class SLAMetric:
    """Métrica de SLA"""
    metric_id: str
    provider: str
    service_name: str
    region: str
    sla_type: SLAType
    target_percentage: float
    actual_percentage: float
    measurement_period_hours: int
    incidents: List[SLAIncident]
    penalty_amount_usd: float = 0.0
    credits_earned_usd: float = 0.0
    compliance_status: str = "UNKNOWN"


class SLADataProvider:
    """Provedor de dados de SLA"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_aws_sla_data(self, service: str, region: str, 
                              start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Obtém dados de SLA da AWS
        Simula dados baseados nos SLAs oficiais da AWS
        """
        try:
            # SLAs oficiais da AWS
            aws_slas = {
                'ec2': {'target': 99.99, 'monthly_uptime_commitment': 99.99},
                's3': {'target': 99.999999999, 'availability': 99.99},  # 11 9's durability
                'rds': {'target': 99.95, 'multi_az': 99.95},
                'lambda': {'target': 99.95, 'availability': 99.95},
                'cloudfront': {'target': 99.9, 'availability': 99.9},
                'route53': {'target': 100.0, 'availability': 100.0},
                'elb': {'target': 99.99, 'availability': 99.99}
            }
            
            sla_config = aws_slas.get(service.lower(), {'target': 99.9})
            target_percentage = sla_config['target']
            
            # Simular dados realistas
            # AWS geralmente supera seus SLAs
            actual_percentage = min(99.999, target_percentage + (100 - target_percentage) * 0.8)
            
            # Simular incidentes baseados na diferença do SLA
            incidents = []
            if actual_percentage < target_percentage:
                downtime_minutes = int((target_percentage - actual_percentage) / 100 * 
                                     (end_date - start_date).total_seconds() / 60)
                
                incidents.append(SLAIncident(
                    incident_id=f"aws-{service}-{region}-{start_date.strftime('%Y%m%d')}",
                    start_time=start_date + timedelta(hours=12),
                    end_time=start_date + timedelta(hours=12, minutes=downtime_minutes),
                    severity=SeverityLevel.MEDIUM,
                    impact_description=f"Service degradation in {service}",
                    affected_services=[service],
                    downtime_minutes=downtime_minutes
                ))
            
            # Calcular créditos baseados no SLA da AWS
            penalty_amount = 0.0
            credits_earned = 0.0
            
            if actual_percentage < target_percentage:
                if actual_percentage < 99.0:
                    credits_earned = 100.0  # 100% service credit
                elif actual_percentage < 99.9:
                    credits_earned = 10.0   # 10% service credit
                
            compliance_status = "COMPLIANT" if actual_percentage >= target_percentage else "NON_COMPLIANT"
            
            return {
                'success': True,
                'provider': 'aws',
                'service': service,
                'region': region,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'hours': int((end_date - start_date).total_seconds() / 3600)
                },
                'sla_metrics': {
                    'target_percentage': target_percentage,
                    'actual_percentage': actual_percentage,
                    'compliance_status': compliance_status,
                    'penalty_amount_usd': penalty_amount,
                    'credits_earned_usd': credits_earned
                },
                'incidents': [asdict(incident) for incident in incidents],
                'sla_details': {
                    'official_commitment': sla_config,
                    'measurement_method': 'Monthly uptime percentage',
                    'exclusions': ['Scheduled maintenance', 'Customer-caused issues'],
                    'remedy': 'Service credits as percentage of monthly bill'
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados SLA AWS: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'aws'
            }
    
    async def get_gcp_sla_data(self, service: str, region: str,
                              start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Obtém dados de SLA do GCP
        Simula dados baseados nos SLAs oficiais do GCP
        """
        try:
            # SLAs oficiais do GCP
            gcp_slas = {
                'compute': {'target': 99.99, 'regional': 99.99, 'zonal': 99.5},
                'storage': {'target': 99.95, 'multi_regional': 99.95, 'regional': 99.9},
                'sql': {'target': 99.95, 'regional': 99.95},
                'functions': {'target': 99.5, 'availability': 99.5},
                'cdn': {'target': 99.9, 'availability': 99.9},
                'dns': {'target': 99.99, 'availability': 99.99},
                'load_balancer': {'target': 99.99, 'availability': 99.99}
            }
            
            sla_config = gcp_slas.get(service.lower(), {'target': 99.9})
            target_percentage = sla_config['target']
            
            # GCP também geralmente supera seus SLAs
            actual_percentage = min(99.999, target_percentage + (100 - target_percentage) * 0.85)
            
            # Simular incidentes
            incidents = []
            if actual_percentage < target_percentage:
                downtime_minutes = int((target_percentage - actual_percentage) / 100 * 
                                     (end_date - start_date).total_seconds() / 60)
                
                incidents.append(SLAIncident(
                    incident_id=f"gcp-{service}-{region}-{start_date.strftime('%Y%m%d')}",
                    start_time=start_date + timedelta(hours=8),
                    end_time=start_date + timedelta(hours=8, minutes=downtime_minutes),
                    severity=SeverityLevel.LOW,
                    impact_description=f"Brief service interruption in {service}",
                    affected_services=[service],
                    downtime_minutes=downtime_minutes
                ))
            
            # Calcular créditos baseados no SLA do GCP
            penalty_amount = 0.0
            credits_earned = 0.0
            
            if actual_percentage < target_percentage:
                if actual_percentage < 95.0:
                    credits_earned = 50.0   # 50% service credit
                elif actual_percentage < 99.0:
                    credits_earned = 25.0   # 25% service credit
                elif actual_percentage < target_percentage:
                    credits_earned = 10.0   # 10% service credit
            
            compliance_status = "COMPLIANT" if actual_percentage >= target_percentage else "NON_COMPLIANT"
            
            return {
                'success': True,
                'provider': 'gcp',
                'service': service,
                'region': region,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'hours': int((end_date - start_date).total_seconds() / 3600)
                },
                'sla_metrics': {
                    'target_percentage': target_percentage,
                    'actual_percentage': actual_percentage,
                    'compliance_status': compliance_status,
                    'penalty_amount_usd': penalty_amount,
                    'credits_earned_usd': credits_earned
                },
                'incidents': [asdict(incident) for incident in incidents],
                'sla_details': {
                    'official_commitment': sla_config,
                    'measurement_method': 'Monthly uptime percentage',
                    'exclusions': ['Scheduled maintenance', 'Emergency maintenance'],
                    'remedy': 'Service credits as percentage of monthly bill'
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados SLA GCP: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'gcp'
            }
    
    async def get_azure_sla_data(self, service: str, region: str,
                                start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Obtém dados de SLA do Azure
        Simula dados baseados nos SLAs oficiais do Azure
        """
        try:
            # SLAs oficiais do Azure
            azure_slas = {
                'virtual_machines': {'target': 99.9, 'availability_set': 99.95, 'availability_zone': 99.99},
                'storage': {'target': 99.9, 'lrs': 99.9, 'grs': 99.9},
                'sql_database': {'target': 99.99, 'basic': 99.9, 'standard': 99.99},
                'functions': {'target': 99.95, 'consumption': 99.95},
                'cdn': {'target': 99.9, 'availability': 99.9},
                'dns': {'target': 99.99, 'availability': 99.99},
                'load_balancer': {'target': 99.99, 'standard': 99.99}
            }
            
            sla_config = azure_slas.get(service.lower(), {'target': 99.9})
            target_percentage = sla_config['target']
            
            # Azure também mantém bons níveis de SLA
            actual_percentage = min(99.999, target_percentage + (100 - target_percentage) * 0.75)
            
            # Simular incidentes
            incidents = []
            if actual_percentage < target_percentage:
                downtime_minutes = int((target_percentage - actual_percentage) / 100 * 
                                     (end_date - start_date).total_seconds() / 60)
                
                incidents.append(SLAIncident(
                    incident_id=f"azure-{service}-{region}-{start_date.strftime('%Y%m%d')}",
                    start_time=start_date + timedelta(hours=15),
                    end_time=start_date + timedelta(hours=15, minutes=downtime_minutes),
                    severity=SeverityLevel.MEDIUM,
                    impact_description=f"Service availability issue in {service}",
                    affected_services=[service],
                    downtime_minutes=downtime_minutes
                ))
            
            # Calcular créditos baseados no SLA do Azure
            penalty_amount = 0.0
            credits_earned = 0.0
            
            if actual_percentage < target_percentage:
                if actual_percentage < 95.0:
                    credits_earned = 100.0  # 100% service credit
                elif actual_percentage < 99.0:
                    credits_earned = 25.0   # 25% service credit
                elif actual_percentage < target_percentage:
                    credits_earned = 10.0   # 10% service credit
            
            compliance_status = "COMPLIANT" if actual_percentage >= target_percentage else "NON_COMPLIANT"
            
            return {
                'success': True,
                'provider': 'azure',
                'service': service,
                'region': region,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'hours': int((end_date - start_date).total_seconds() / 3600)
                },
                'sla_metrics': {
                    'target_percentage': target_percentage,
                    'actual_percentage': actual_percentage,
                    'compliance_status': compliance_status,
                    'penalty_amount_usd': penalty_amount,
                    'credits_earned_usd': credits_earned
                },
                'incidents': [asdict(incident) for incident in incidents],
                'sla_details': {
                    'official_commitment': sla_config,
                    'measurement_method': 'Monthly uptime percentage',
                    'exclusions': ['Planned maintenance', 'Force majeure events'],
                    'remedy': 'Service credits as percentage of monthly bill'
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados SLA Azure: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'azure'
            }


class SLAAnalyzer:
    """Analisador de SLAs"""
    
    def __init__(self):
        self.data_provider = SLADataProvider()
    
    async def compare_slas(self, providers: List[str], service_type: str, 
                          region: str, period_days: int = 30) -> Dict[str, Any]:
        """
        Compara SLAs entre provedores
        
        Args:
            providers: Lista de provedores (aws, gcp, azure)
            service_type: Tipo de serviço
            region: Região
            period_days: Período de análise em dias
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            results = {}
            
            async with self.data_provider:
                for provider in providers:
                    if provider.lower() == 'aws':
                        data = await self.data_provider.get_aws_sla_data(
                            service_type, region, start_date, end_date
                        )
                    elif provider.lower() == 'gcp':
                        data = await self.data_provider.get_gcp_sla_data(
                            service_type, region, start_date, end_date
                        )
                    elif provider.lower() == 'azure':
                        data = await self.data_provider.get_azure_sla_data(
                            service_type, region, start_date, end_date
                        )
                    else:
                        continue
                    
                    results[provider] = data
            
            # Análise comparativa
            comparison = self._analyze_sla_comparison(results, service_type)
            
            return {
                'success': True,
                'comparison_id': f"sla-comp-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'service_type': service_type,
                'region': region,
                'period_days': period_days,
                'providers_analyzed': providers,
                'individual_results': results,
                'comparative_analysis': comparison,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na comparação de SLAs: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'SLA_COMPARISON_ERROR'
            }
    
    def _analyze_sla_comparison(self, results: Dict[str, Any], service_type: str) -> Dict[str, Any]:
        """Analisa comparação de SLAs"""
        
        analysis = {
            'best_performer': None,
            'worst_performer': None,
            'average_uptime': 0.0,
            'total_incidents': 0,
            'total_credits_available': 0.0,
            'recommendations': []
        }
        
        uptimes = []
        incidents_count = 0
        credits_total = 0.0
        
        provider_scores = {}
        
        for provider, data in results.items():
            if not data.get('success'):
                continue
            
            metrics = data.get('sla_metrics', {})
            actual_uptime = metrics.get('actual_percentage', 0)
            incidents = data.get('incidents', [])
            credits = metrics.get('credits_earned_usd', 0)
            
            uptimes.append(actual_uptime)
            incidents_count += len(incidents)
            credits_total += credits
            
            # Calcular score do provedor
            score = actual_uptime
            if len(incidents) == 0:
                score += 0.1  # Bonus por não ter incidentes
            
            provider_scores[provider] = {
                'uptime': actual_uptime,
                'incidents': len(incidents),
                'credits': credits,
                'score': score
            }
        
        if provider_scores:
            # Melhor e pior performer
            best = max(provider_scores.items(), key=lambda x: x[1]['score'])
            worst = min(provider_scores.items(), key=lambda x: x[1]['score'])
            
            analysis['best_performer'] = {
                'provider': best[0],
                'uptime': best[1]['uptime'],
                'score': best[1]['score']
            }
            
            analysis['worst_performer'] = {
                'provider': worst[0],
                'uptime': worst[1]['uptime'],
                'score': worst[1]['score']
            }
            
            analysis['average_uptime'] = statistics.mean(uptimes) if uptimes else 0
            analysis['total_incidents'] = incidents_count
            analysis['total_credits_available'] = credits_total
            
            # Recomendações
            recommendations = []
            
            if best[1]['uptime'] > 99.99:
                recommendations.append(f"{best[0]} oferece excelente confiabilidade para {service_type}")
            
            if worst[1]['incidents'] > 0:
                recommendations.append(f"Considere evitar {worst[0]} se uptime é crítico")
            
            if credits_total > 0:
                recommendations.append(f"Créditos disponíveis: ${credits_total:.2f} em caso de violação de SLA")
            
            analysis['recommendations'] = recommendations
        
        return analysis
    
    async def calculate_sla_penalties(self, provider: str, service: str,
                                    actual_uptime: float, target_uptime: float,
                                    monthly_spend: float) -> Dict[str, Any]:
        """
        Calcula penalidades de SLA
        
        Args:
            provider: Provedor de nuvem
            service: Serviço
            actual_uptime: Uptime real (%)
            target_uptime: Uptime alvo (%)
            monthly_spend: Gasto mensal (USD)
        """
        try:
            penalties = {
                'aws': {
                    99.99: {'below_99': 100, 'below_95': 100},
                    99.95: {'below_99': 10, 'below_95': 100},
                    99.9: {'below_99': 10, 'below_95': 25}
                },
                'gcp': {
                    99.99: {'below_99': 10, 'below_95': 25},
                    99.95: {'below_99': 10, 'below_95': 25},
                    99.9: {'below_99': 10, 'below_95': 25}
                },
                'azure': {
                    99.99: {'below_99': 10, 'below_95': 25},
                    99.95: {'below_99': 10, 'below_95': 25},
                    99.9: {'below_99': 10, 'below_95': 25}
                }
            }
            
            provider_penalties = penalties.get(provider.lower(), {})
            target_penalties = provider_penalties.get(target_uptime, {'below_99': 10, 'below_95': 25})
            
            credit_percentage = 0
            
            if actual_uptime < 95.0:
                credit_percentage = target_penalties.get('below_95', 25)
            elif actual_uptime < 99.0:
                credit_percentage = target_penalties.get('below_99', 10)
            elif actual_uptime < target_uptime:
                credit_percentage = 10  # Penalidade mínima
            
            credit_amount = (credit_percentage / 100) * monthly_spend
            
            return {
                'success': True,
                'provider': provider,
                'service': service,
                'sla_analysis': {
                    'target_uptime_percent': target_uptime,
                    'actual_uptime_percent': actual_uptime,
                    'uptime_difference': target_uptime - actual_uptime,
                    'sla_violated': actual_uptime < target_uptime
                },
                'financial_impact': {
                    'monthly_spend_usd': monthly_spend,
                    'credit_percentage': credit_percentage,
                    'credit_amount_usd': credit_amount,
                    'annual_credit_potential_usd': credit_amount * 12
                },
                'recommendations': [
                    f"Monitor {service} uptime closely",
                    f"Consider SLA credits if uptime drops below {target_uptime}%",
                    f"Potential annual savings from credits: ${credit_amount * 12:.2f}"
                ],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular penalidades SLA: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'PENALTY_CALCULATION_ERROR'
            }


class SLAMCPServer:
    """Servidor MCP para análise de SLA"""
    
    def __init__(self):
        self.server = Server("sla-analysis-mcp-server")
        self.analyzer = SLAAnalyzer()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura handlers do servidor MCP"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Lista ferramentas disponíveis"""
            return [
                Tool(
                    name="compare_provider_slas",
                    description="Compara SLAs entre provedores de nuvem",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "providers": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["aws", "gcp", "azure"]},
                                "description": "Lista de provedores para comparar"
                            },
                            "service_type": {"type": "string", "description": "Tipo de serviço"},
                            "region": {"type": "string", "description": "Região"},
                            "period_days": {"type": "integer", "default": 30, "description": "Período de análise"}
                        },
                        "required": ["providers", "service_type", "region"]
                    }
                ),
                Tool(
                    name="calculate_sla_penalties",
                    description="Calcula penalidades e créditos de SLA",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "enum": ["aws", "gcp", "azure"]},
                            "service": {"type": "string", "description": "Nome do serviço"},
                            "actual_uptime": {"type": "number", "description": "Uptime real (%)"},
                            "target_uptime": {"type": "number", "description": "Uptime alvo (%)"},
                            "monthly_spend": {"type": "number", "description": "Gasto mensal (USD)"}
                        },
                        "required": ["provider", "service", "actual_uptime", "target_uptime", "monthly_spend"]
                    }
                ),
                Tool(
                    name="get_provider_sla_details",
                    description="Obtém detalhes de SLA de um provedor específico",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "enum": ["aws", "gcp", "azure"]},
                            "service": {"type": "string", "description": "Nome do serviço"},
                            "region": {"type": "string", "description": "Região"},
                            "period_days": {"type": "integer", "default": 30}
                        },
                        "required": ["provider", "service", "region"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Executa ferramenta"""
            
            try:
                if name == "compare_provider_slas":
                    result = await self.analyzer.compare_slas(**arguments)
                elif name == "calculate_sla_penalties":
                    result = await self.analyzer.calculate_sla_penalties(**arguments)
                elif name == "get_provider_sla_details":
                    # Obter dados de um provedor específico
                    provider = arguments['provider']
                    service = arguments['service']
                    region = arguments['region']
                    period_days = arguments.get('period_days', 30)
                    
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=period_days)
                    
                    async with self.analyzer.data_provider:
                        if provider == 'aws':
                            result = await self.analyzer.data_provider.get_aws_sla_data(
                                service, region, start_date, end_date
                            )
                        elif provider == 'gcp':
                            result = await self.analyzer.data_provider.get_gcp_sla_data(
                                service, region, start_date, end_date
                            )
                        elif provider == 'azure':
                            result = await self.analyzer.data_provider.get_azure_sla_data(
                                service, region, start_date, end_date
                            )
                        else:
                            result = {"success": False, "error": f"Unknown provider: {provider}"}
                else:
                    result = {"success": False, "error": f"Unknown tool: {name}"}
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps(result, indent=2, default=str)
                    )]
                )
                
            except Exception as e:
                logger.error(f"Erro ao executar ferramenta {name}: {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e),
                            "tool": name
                        })
                    )]
                )
    
    async def run(self):
        """Executa o servidor MCP"""
        logger.info("Iniciando SLA Analysis MCP Server...")
        
        # Executar servidor
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SLA Analysis MCP Server')
    parser.add_argument('--log-level', default='INFO', help='Nível de log')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Executar servidor
    server = SLAMCPServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

