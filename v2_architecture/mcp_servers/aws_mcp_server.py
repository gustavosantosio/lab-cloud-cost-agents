"""
Cloud Cost Agent v2 - AWS MCP Server
Servidor MCP especializado para conectar com APIs da AWS
Compatível com Windows
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
import sys

# AWS SDK
import boto3
from botocore.exceptions import ClientError, BotoCoreError

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
        logging.FileHandler('aws_mcp_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class AWSCredentials:
    """Credenciais AWS"""
    access_key_id: str
    secret_access_key: str
    region: str = 'us-east-1'
    session_token: Optional[str] = None


class AWSCostAnalyzer:
    """Analisador de custos AWS"""
    
    def __init__(self, credentials: AWSCredentials):
        self.credentials = credentials
        self.session = boto3.Session(
            aws_access_key_id=credentials.access_key_id,
            aws_secret_access_key=credentials.secret_access_key,
            aws_session_token=credentials.session_token,
            region_name=credentials.region
        )
        
        # Clientes AWS
        self.cost_explorer = self.session.client('ce')
        self.pricing = self.session.client('pricing', region_name='us-east-1')  # Pricing API só funciona em us-east-1
        self.ec2 = self.session.client('ec2')
        self.cloudwatch = self.session.client('cloudwatch')
        self.support = None  # Requer Business/Enterprise support
        
        try:
            self.support = self.session.client('support', region_name='us-east-1')
        except Exception as e:
            logger.warning(f"Support API não disponível: {e}")
    
    async def get_cost_and_usage(self, start_date: str, end_date: str, 
                                granularity: str = 'MONTHLY',
                                group_by: List[Dict] = None) -> Dict[str, Any]:
        """
        Obtém dados de custo e uso do Cost Explorer
        
        Args:
            start_date: Data início (YYYY-MM-DD)
            end_date: Data fim (YYYY-MM-DD)
            granularity: DAILY, MONTHLY, HOURLY
            group_by: Lista de agrupamentos
        """
        try:
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': granularity,
                'Metrics': ['BlendedCost', 'UsageQuantity', 'UnblendedCost']
            }
            
            if group_by:
                params['GroupBy'] = group_by
            
            response = self.cost_explorer.get_cost_and_usage(**params)
            
            return {
                'success': True,
                'data': response,
                'total_cost': self._calculate_total_cost(response),
                'period': f"{start_date} to {end_date}",
                'granularity': granularity
            }
            
        except ClientError as e:
            logger.error(f"Erro ao obter custo e uso: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }
    
    async def get_ec2_pricing(self, instance_type: str, region: str = None,
                             operating_system: str = 'Linux',
                             tenancy: str = 'Shared') -> Dict[str, Any]:
        """
        Obtém preços de instâncias EC2
        
        Args:
            instance_type: Tipo da instância (ex: t3.medium)
            region: Região AWS
            operating_system: Sistema operacional
            tenancy: Tipo de tenancy
        """
        try:
            if not region:
                region = self.credentials.region
            
            # Mapear região para nome usado na API de preços
            region_mapping = {
                'us-east-1': 'US East (N. Virginia)',
                'us-east-2': 'US East (Ohio)',
                'us-west-1': 'US West (N. California)',
                'us-west-2': 'US West (Oregon)',
                'eu-west-1': 'Europe (Ireland)',
                'eu-central-1': 'Europe (Frankfurt)',
                'ap-southeast-1': 'Asia Pacific (Singapore)',
                'ap-northeast-1': 'Asia Pacific (Tokyo)'
            }
            
            location = region_mapping.get(region, region)
            
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonEC2'},
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': operating_system},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': tenancy},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
            ]
            
            response = self.pricing.get_products(
                ServiceCode='AmazonEC2',
                Filters=filters,
                MaxResults=100
            )
            
            pricing_data = []
            for price_item in response.get('PriceList', []):
                price_info = json.loads(price_item)
                
                # Extrair informações de preço
                terms = price_info.get('terms', {})
                on_demand = terms.get('OnDemand', {})
                
                for term_key, term_data in on_demand.items():
                    price_dimensions = term_data.get('priceDimensions', {})
                    for dim_key, dim_data in price_dimensions.items():
                        price_per_unit = dim_data.get('pricePerUnit', {}).get('USD', '0')
                        
                        pricing_data.append({
                            'instance_type': instance_type,
                            'region': region,
                            'operating_system': operating_system,
                            'hourly_price_usd': float(price_per_unit),
                            'monthly_price_usd': float(price_per_unit) * 24 * 30,
                            'annual_price_usd': float(price_per_unit) * 24 * 365,
                            'unit': dim_data.get('unit', 'Hrs'),
                            'description': dim_data.get('description', '')
                        })
            
            return {
                'success': True,
                'data': pricing_data,
                'instance_type': instance_type,
                'region': region,
                'timestamp': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Erro ao obter preços EC2: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }
    
    async def get_s3_pricing(self, region: str = None, 
                            storage_class: str = 'Standard') -> Dict[str, Any]:
        """
        Obtém preços do S3
        
        Args:
            region: Região AWS
            storage_class: Classe de armazenamento
        """
        try:
            if not region:
                region = self.credentials.region
            
            region_mapping = {
                'us-east-1': 'US East (N. Virginia)',
                'us-east-2': 'US East (Ohio)',
                'us-west-1': 'US West (N. California)',
                'us-west-2': 'US West (Oregon)',
                'eu-west-1': 'Europe (Ireland)',
                'eu-central-1': 'Europe (Frankfurt)'
            }
            
            location = region_mapping.get(region, region)
            
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonS3'},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                {'Type': 'TERM_MATCH', 'Field': 'storageClass', 'Value': storage_class}
            ]
            
            response = self.pricing.get_products(
                ServiceCode='AmazonS3',
                Filters=filters,
                MaxResults=100
            )
            
            pricing_data = []
            for price_item in response.get('PriceList', []):
                price_info = json.loads(price_item)
                
                terms = price_info.get('terms', {})
                on_demand = terms.get('OnDemand', {})
                
                for term_key, term_data in on_demand.items():
                    price_dimensions = term_data.get('priceDimensions', {})
                    for dim_key, dim_data in price_dimensions.items():
                        price_per_unit = dim_data.get('pricePerUnit', {}).get('USD', '0')
                        
                        pricing_data.append({
                            'storage_class': storage_class,
                            'region': region,
                            'price_per_gb_usd': float(price_per_unit),
                            'unit': dim_data.get('unit', 'GB-Mo'),
                            'description': dim_data.get('description', ''),
                            'usage_type': price_info.get('product', {}).get('attributes', {}).get('usagetype', '')
                        })
            
            return {
                'success': True,
                'data': pricing_data,
                'storage_class': storage_class,
                'region': region,
                'timestamp': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Erro ao obter preços S3: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }
    
    async def get_rightsizing_recommendations(self) -> Dict[str, Any]:
        """
        Obtém recomendações de rightsizing do Cost Explorer
        """
        try:
            response = self.cost_explorer.get_rightsizing_recommendation(
                Service='AmazonEC2',
                Configuration={
                    'BenefitsConsidered': True,
                    'RecommendationTarget': 'SAME_INSTANCE_FAMILY'
                }
            )
            
            recommendations = []
            for rec in response.get('RightsizingRecommendations', []):
                recommendations.append({
                    'account_id': rec.get('AccountId'),
                    'current_instance': rec.get('CurrentInstance', {}),
                    'rightsizing_type': rec.get('RightsizingType'),
                    'modify_recommendation': rec.get('ModifyRecommendationDetail', {}),
                    'terminate_recommendation': rec.get('TerminateRecommendationDetail', {}),
                    'finding_reason_codes': rec.get('FindingReasonCodes', [])
                })
            
            return {
                'success': True,
                'data': recommendations,
                'total_recommendations': len(recommendations),
                'timestamp': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Erro ao obter recomendações de rightsizing: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }
    
    async def get_trusted_advisor_checks(self) -> Dict[str, Any]:
        """
        Obtém verificações do Trusted Advisor (requer Business/Enterprise support)
        """
        if not self.support:
            return {
                'success': False,
                'error': 'Trusted Advisor requer plano Business ou Enterprise',
                'error_code': 'SUPPORT_NOT_AVAILABLE'
            }
        
        try:
            # Obter lista de verificações
            checks_response = self.support.describe_trusted_advisor_checks(
                language='en'
            )
            
            cost_optimization_checks = []
            for check in checks_response.get('checks', []):
                if 'cost' in check.get('category', '').lower():
                    # Obter resultado da verificação
                    result_response = self.support.describe_trusted_advisor_check_result(
                        checkId=check['id'],
                        language='en'
                    )
                    
                    cost_optimization_checks.append({
                        'check_id': check['id'],
                        'name': check['name'],
                        'description': check['description'],
                        'category': check['category'],
                        'status': result_response['result']['status'],
                        'resources_summary': result_response['result']['resourcesSummary'],
                        'flagged_resources': result_response['result'].get('flaggedResources', [])
                    })
            
            return {
                'success': True,
                'data': cost_optimization_checks,
                'total_checks': len(cost_optimization_checks),
                'timestamp': datetime.now().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"Erro ao obter Trusted Advisor: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response['Error']['Code']
            }
    
    def _calculate_total_cost(self, cost_response: Dict) -> float:
        """Calcula custo total da resposta do Cost Explorer"""
        total = 0.0
        
        for result in cost_response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                amount = group.get('Metrics', {}).get('BlendedCost', {}).get('Amount', '0')
                total += float(amount)
        
        return total


class AWSMCPServer:
    """Servidor MCP para AWS"""
    
    def __init__(self):
        self.server = Server("aws-mcp-server")
        self.cost_analyzer = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura handlers do servidor MCP"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Lista ferramentas disponíveis"""
            return [
                Tool(
                    name="get_cost_and_usage",
                    description="Obtém dados de custo e uso do AWS Cost Explorer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "description": "Data início (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "description": "Data fim (YYYY-MM-DD)"},
                            "granularity": {"type": "string", "enum": ["DAILY", "MONTHLY", "HOURLY"], "default": "MONTHLY"},
                            "group_by": {"type": "array", "description": "Agrupamentos opcionais"}
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="get_ec2_pricing",
                    description="Obtém preços de instâncias EC2",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "instance_type": {"type": "string", "description": "Tipo da instância (ex: t3.medium)"},
                            "region": {"type": "string", "description": "Região AWS"},
                            "operating_system": {"type": "string", "default": "Linux"},
                            "tenancy": {"type": "string", "default": "Shared"}
                        },
                        "required": ["instance_type"]
                    }
                ),
                Tool(
                    name="get_s3_pricing",
                    description="Obtém preços do Amazon S3",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region": {"type": "string", "description": "Região AWS"},
                            "storage_class": {"type": "string", "default": "Standard"}
                        }
                    }
                ),
                Tool(
                    name="get_rightsizing_recommendations",
                    description="Obtém recomendações de rightsizing do Cost Explorer",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_trusted_advisor_checks",
                    description="Obtém verificações de otimização de custos do Trusted Advisor",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Executa ferramenta"""
            
            if not self.cost_analyzer:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": "AWS credentials not configured"
                        })
                    )]
                )
            
            try:
                if name == "get_cost_and_usage":
                    result = await self.cost_analyzer.get_cost_and_usage(**arguments)
                elif name == "get_ec2_pricing":
                    result = await self.cost_analyzer.get_ec2_pricing(**arguments)
                elif name == "get_s3_pricing":
                    result = await self.cost_analyzer.get_s3_pricing(**arguments)
                elif name == "get_rightsizing_recommendations":
                    result = await self.cost_analyzer.get_rightsizing_recommendations()
                elif name == "get_trusted_advisor_checks":
                    result = await self.cost_analyzer.get_trusted_advisor_checks()
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
    
    def configure_credentials(self, credentials: AWSCredentials):
        """Configura credenciais AWS"""
        self.cost_analyzer = AWSCostAnalyzer(credentials)
        logger.info("Credenciais AWS configuradas")
    
    async def run(self):
        """Executa o servidor MCP"""
        logger.info("Iniciando AWS MCP Server...")
        
        # Configurar credenciais a partir de variáveis de ambiente
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        session_token = os.getenv('AWS_SESSION_TOKEN')
        
        if access_key and secret_key:
            credentials = AWSCredentials(
                access_key_id=access_key,
                secret_access_key=secret_key,
                region=region,
                session_token=session_token
            )
            self.configure_credentials(credentials)
        else:
            logger.warning("Credenciais AWS não encontradas nas variáveis de ambiente")
        
        # Executar servidor
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS MCP Server')
    parser.add_argument('--region', default='us-east-1', help='Região AWS padrão')
    parser.add_argument('--log-level', default='INFO', help='Nível de log')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Executar servidor
    server = AWSMCPServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

