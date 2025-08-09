"""
Servidor MCP para AWS - Model Context Protocol
Responsável por conectar à API de custos da AWS e fornecer dados para os agentes
"""
import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mcp import MCPServer, Tool, Resource
from config.project_config import config
from agents.base.logger import AgentLogger

class AWSMCPServer:
    """
    Servidor MCP para AWS - Fornece acesso às APIs de custos e recursos da AWS
    """
    
    def __init__(self):
        self.logger = AgentLogger("AWSMCPServer")
        self.server = MCPServer("aws-cost-api")
        self.aws_session = None
        self._initialize_aws_connection()
        self._register_tools()
        self._register_resources()
    
    def _initialize_aws_connection(self):
        """Inicializa conexão com AWS"""
        try:
            self.aws_session = boto3.Session(
                aws_access_key_id=config.aws.access_key_id,
                aws_secret_access_key=config.aws.secret_access_key,
                region_name=config.aws.region
            )
            
            # Testar conexão
            sts_client = self.aws_session.client('sts')
            identity = sts_client.get_caller_identity()
            
            self.logger.info("AWS MCP Server conectado", {
                "account_id": identity.get('Account'),
                "region": config.aws.region
            })
            
        except (NoCredentialsError, ClientError) as e:
            self.logger.error(f"Erro na conexão AWS MCP: {str(e)}")
            self.aws_session = None
    
    def _register_tools(self):
        """Registra ferramentas MCP para AWS"""
        
        @self.server.tool("get_cost_and_usage")
        async def get_cost_and_usage(
            start_date: str,
            end_date: str,
            granularity: str = "MONTHLY",
            group_by: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Obtém dados de custo e uso da AWS Cost Explorer
            
            Args:
                start_date: Data de início (YYYY-MM-DD)
                end_date: Data de fim (YYYY-MM-DD)
                granularity: Granularidade (DAILY, MONTHLY)
                group_by: Lista de dimensões para agrupamento
            """
            try:
                if not self.aws_session:
                    return {"error": "AWS não conectada"}
                
                cost_explorer = self.aws_session.client('ce')
                
                # Configurar parâmetros da consulta
                params = {
                    'TimePeriod': {
                        'Start': start_date,
                        'End': end_date
                    },
                    'Granularity': granularity,
                    'Metrics': ['BlendedCost', 'UsageQuantity']
                }
                
                # Adicionar agrupamento se especificado
                if group_by:
                    params['GroupBy'] = [
                        {'Type': 'DIMENSION', 'Key': key} for key in group_by
                    ]
                
                response = cost_explorer.get_cost_and_usage(**params)
                
                self.logger.info("Dados de custo AWS obtidos", {
                    "period": f"{start_date} to {end_date}",
                    "results_count": len(response.get('ResultsByTime', []))
                })
                
                return {
                    "success": True,
                    "data": response,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao obter custos AWS: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_rightsizing_recommendations")
        async def get_rightsizing_recommendations() -> Dict[str, Any]:
            """
            Obtém recomendações de rightsizing da AWS
            """
            try:
                if not self.aws_session:
                    return {"error": "AWS não conectada"}
                
                cost_explorer = self.aws_session.client('ce')
                
                response = cost_explorer.get_rightsizing_recommendation(
                    Service='AmazonEC2',
                    Configuration={
                        'BenefitsConsidered': True,
                        'RecommendationTarget': 'SAME_INSTANCE_FAMILY'
                    }
                )
                
                self.logger.info("Recomendações de rightsizing obtidas", {
                    "recommendations_count": len(response.get('RightsizingRecommendations', []))
                })
                
                return {
                    "success": True,
                    "data": response,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao obter recomendações: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_reserved_instances_recommendations")
        async def get_reserved_instances_recommendations() -> Dict[str, Any]:
            """
            Obtém recomendações de Reserved Instances
            """
            try:
                if not self.aws_session:
                    return {"error": "AWS não conectada"}
                
                cost_explorer = self.aws_session.client('ce')
                
                response = cost_explorer.get_reservation_purchase_recommendation(
                    Service='AmazonEC2',
                    LookbackPeriodInDays='SIXTY_DAYS',
                    TermInYears='ONE_YEAR',
                    PaymentOption='NO_UPFRONT'
                )
                
                self.logger.info("Recomendações de RI obtidas", {
                    "recommendations_count": len(response.get('Recommendations', []))
                })
                
                return {
                    "success": True,
                    "data": response,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao obter recomendações RI: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_ec2_instances")
        async def get_ec2_instances(region: Optional[str] = None) -> Dict[str, Any]:
            """
            Lista instâncias EC2
            
            Args:
                region: Região específica (opcional)
            """
            try:
                if not self.aws_session:
                    return {"error": "AWS não conectada"}
                
                target_region = region or config.aws.region
                ec2 = self.aws_session.client('ec2', region_name=target_region)
                
                response = ec2.describe_instances()
                
                instances = []
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        instances.append({
                            'InstanceId': instance['InstanceId'],
                            'InstanceType': instance['InstanceType'],
                            'State': instance['State']['Name'],
                            'LaunchTime': instance['LaunchTime'].isoformat(),
                            'Region': target_region
                        })
                
                self.logger.info("Instâncias EC2 listadas", {
                    "region": target_region,
                    "instances_count": len(instances)
                })
                
                return {
                    "success": True,
                    "data": instances,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao listar instâncias EC2: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_s3_buckets")
        async def get_s3_buckets() -> Dict[str, Any]:
            """
            Lista buckets S3
            """
            try:
                if not self.aws_session:
                    return {"error": "AWS não conectada"}
                
                s3 = self.aws_session.client('s3')
                
                response = s3.list_buckets()
                
                buckets = []
                for bucket in response['Buckets']:
                    # Obter região do bucket
                    try:
                        location = s3.get_bucket_location(Bucket=bucket['Name'])
                        region = location['LocationConstraint'] or 'us-east-1'
                    except:
                        region = 'unknown'
                    
                    buckets.append({
                        'Name': bucket['Name'],
                        'CreationDate': bucket['CreationDate'].isoformat(),
                        'Region': region
                    })
                
                self.logger.info("Buckets S3 listados", {
                    "buckets_count": len(buckets)
                })
                
                return {
                    "success": True,
                    "data": buckets,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao listar buckets S3: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_rds_instances")
        async def get_rds_instances(region: Optional[str] = None) -> Dict[str, Any]:
            """
            Lista instâncias RDS
            
            Args:
                region: Região específica (opcional)
            """
            try:
                if not self.aws_session:
                    return {"error": "AWS não conectada"}
                
                target_region = region or config.aws.region
                rds = self.aws_session.client('rds', region_name=target_region)
                
                response = rds.describe_db_instances()
                
                instances = []
                for instance in response['DBInstances']:
                    instances.append({
                        'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                        'DBInstanceClass': instance['DBInstanceClass'],
                        'Engine': instance['Engine'],
                        'DBInstanceStatus': instance['DBInstanceStatus'],
                        'AllocatedStorage': instance['AllocatedStorage'],
                        'Region': target_region
                    })
                
                self.logger.info("Instâncias RDS listadas", {
                    "region": target_region,
                    "instances_count": len(instances)
                })
                
                return {
                    "success": True,
                    "data": instances,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao listar instâncias RDS: {str(e)}")
                return {"error": str(e)}
    
    def _register_resources(self):
        """Registra recursos MCP para AWS"""
        
        @self.server.resource("aws://cost-explorer/summary")
        async def cost_explorer_summary() -> Dict[str, Any]:
            """
            Recurso que fornece resumo do Cost Explorer
            """
            try:
                # Obter dados dos últimos 30 dias
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                cost_data = await self.server.tools["get_cost_and_usage"](
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d'),
                    "MONTHLY",
                    ["SERVICE"]
                )
                
                return {
                    "resource_type": "cost_summary",
                    "data": cost_data,
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"error": str(e)}
        
        @self.server.resource("aws://recommendations/all")
        async def all_recommendations() -> Dict[str, Any]:
            """
            Recurso que fornece todas as recomendações AWS
            """
            try:
                rightsizing = await self.server.tools["get_rightsizing_recommendations"]()
                reserved_instances = await self.server.tools["get_reserved_instances_recommendations"]()
                
                return {
                    "resource_type": "recommendations",
                    "data": {
                        "rightsizing": rightsizing,
                        "reserved_instances": reserved_instances
                    },
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"error": str(e)}
    
    async def start_server(self, host: str = "0.0.0.0", port: int = None):
        """Inicia o servidor MCP"""
        server_port = port or config.mcp.aws_port
        
        try:
            self.logger.info(f"Iniciando AWS MCP Server em {host}:{server_port}")
            await self.server.start(host=host, port=server_port)
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar AWS MCP Server: {str(e)}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """Retorna informações do servidor"""
        return {
            "name": "AWS MCP Server",
            "version": "1.0.0",
            "description": "Servidor MCP para APIs de custos e recursos AWS",
            "port": config.mcp.aws_port,
            "tools_count": len(self.server.tools),
            "resources_count": len(self.server.resources),
            "aws_connected": self.aws_session is not None
        }

async def main():
    """Função principal para executar o servidor"""
    aws_mcp = AWSMCPServer()
    
    try:
        await aws_mcp.start_server()
    except KeyboardInterrupt:
        print("Servidor AWS MCP interrompido pelo usuário")
    except Exception as e:
        print(f"Erro no servidor AWS MCP: {e}")

if __name__ == "__main__":
    asyncio.run(main())

