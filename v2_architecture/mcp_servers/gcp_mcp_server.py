"""
Cloud Cost Agent v2 - GCP MCP Server
Servidor MCP especializado para conectar com APIs do Google Cloud
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

# Google Cloud SDK
from google.cloud import billing_v1
from google.cloud import monitoring_v3
from google.cloud import asset_v1
from google.cloud import recommender_v1
from google.oauth2 import service_account
from google.auth.exceptions import GoogleAuthError

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
        logging.FileHandler('gcp_mcp_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class GCPCredentials:
    """Credenciais GCP"""
    project_id: str
    service_account_path: Optional[str] = None
    service_account_info: Optional[Dict] = None


class GCPCostAnalyzer:
    """Analisador de custos GCP"""
    
    def __init__(self, credentials: GCPCredentials):
        self.credentials = credentials
        self.project_id = credentials.project_id
        
        # Configurar autenticação
        if credentials.service_account_path:
            self.creds = service_account.Credentials.from_service_account_file(
                credentials.service_account_path
            )
        elif credentials.service_account_info:
            self.creds = service_account.Credentials.from_service_account_info(
                credentials.service_account_info
            )
        else:
            # Usar credenciais padrão
            from google.auth import default
            self.creds, _ = default()
        
        # Clientes GCP
        self.billing_client = billing_v1.CloudBillingClient(credentials=self.creds)
        self.monitoring_client = monitoring_v3.MetricServiceClient(credentials=self.creds)
        self.asset_client = asset_v1.AssetServiceClient(credentials=self.creds)
        self.recommender_client = recommender_v1.RecommenderClient(credentials=self.creds)
    
    async def get_billing_accounts(self) -> Dict[str, Any]:
        """
        Obtém contas de billing do projeto
        """
        try:
            request = billing_v1.ListBillingAccountsRequest()
            page_result = self.billing_client.list_billing_accounts(request=request)
            
            accounts = []
            for account in page_result:
                accounts.append({
                    'name': account.name,
                    'display_name': account.display_name,
                    'open': account.open,
                    'master_billing_account': account.master_billing_account
                })
            
            return {
                'success': True,
                'data': accounts,
                'total_accounts': len(accounts),
                'timestamp': datetime.now().isoformat()
            }
            
        except GoogleAuthError as e:
            logger.error(f"Erro de autenticação GCP: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'AUTHENTICATION_ERROR'
            }
        except Exception as e:
            logger.error(f"Erro ao obter contas de billing: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'API_ERROR'
            }
    
    async def get_compute_pricing(self, machine_type: str, region: str,
                                 preemptible: bool = False) -> Dict[str, Any]:
        """
        Obtém preços de instâncias Compute Engine
        
        Args:
            machine_type: Tipo da máquina (ex: e2-medium)
            region: Região GCP (ex: us-central1)
            preemptible: Se é instância preemptível
        """
        try:
            # GCP não tem uma API de preços pública como AWS
            # Vamos usar uma tabela de preços estimada baseada na documentação oficial
            
            # Preços base por família de máquina (USD por hora)
            pricing_table = {
                'e2-micro': {'cpu': 0.00838, 'memory_gb': 0.00112},
                'e2-small': {'cpu': 0.01675, 'memory_gb': 0.00225},
                'e2-medium': {'cpu': 0.03351, 'memory_gb': 0.00449},
                'e2-standard-2': {'cpu': 0.06701, 'memory_gb': 0.00898},
                'e2-standard-4': {'cpu': 0.13402, 'memory_gb': 0.01796},
                'e2-standard-8': {'cpu': 0.26804, 'memory_gb': 0.03593},
                'n1-standard-1': {'cpu': 0.0475, 'memory_gb': 0.00638},
                'n1-standard-2': {'cpu': 0.095, 'memory_gb': 0.01275},
                'n1-standard-4': {'cpu': 0.19, 'memory_gb': 0.0255},
                'n1-standard-8': {'cpu': 0.38, 'memory_gb': 0.051},
                'n2-standard-2': {'cpu': 0.097, 'memory_gb': 0.013},
                'n2-standard-4': {'cpu': 0.194, 'memory_gb': 0.026},
                'n2-standard-8': {'cpu': 0.388, 'memory_gb': 0.052}
            }
            
            # Multiplicadores por região
            region_multipliers = {
                'us-central1': 1.0,
                'us-east1': 1.0,
                'us-west1': 1.0,
                'us-west2': 1.0,
                'europe-west1': 1.08,
                'europe-west2': 1.16,
                'europe-west3': 1.08,
                'asia-southeast1': 1.08,
                'asia-northeast1': 1.08
            }
            
            base_pricing = pricing_table.get(machine_type)
            if not base_pricing:
                return {
                    'success': False,
                    'error': f'Machine type {machine_type} not found in pricing table',
                    'error_type': 'MACHINE_TYPE_NOT_FOUND'
                }
            
            region_multiplier = region_multipliers.get(region, 1.1)  # Default 10% premium
            preemptible_discount = 0.2 if preemptible else 1.0  # 80% discount for preemptible
            
            # Calcular preços
            hourly_cpu_cost = base_pricing['cpu'] * region_multiplier * preemptible_discount
            hourly_memory_cost = base_pricing['memory_gb'] * region_multiplier * preemptible_discount
            hourly_total = hourly_cpu_cost + hourly_memory_cost
            
            pricing_data = {
                'machine_type': machine_type,
                'region': region,
                'preemptible': preemptible,
                'pricing': {
                    'hourly_usd': round(hourly_total, 5),
                    'daily_usd': round(hourly_total * 24, 2),
                    'monthly_usd': round(hourly_total * 24 * 30, 2),
                    'annual_usd': round(hourly_total * 24 * 365, 2)
                },
                'breakdown': {
                    'cpu_hourly_usd': round(hourly_cpu_cost, 5),
                    'memory_hourly_usd': round(hourly_memory_cost, 5),
                    'region_multiplier': region_multiplier,
                    'preemptible_discount': preemptible_discount
                }
            }
            
            return {
                'success': True,
                'data': pricing_data,
                'timestamp': datetime.now().isoformat(),
                'note': 'Preços estimados baseados na documentação oficial do GCP'
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter preços Compute Engine: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'PRICING_ERROR'
            }
    
    async def get_storage_pricing(self, storage_class: str = 'STANDARD',
                                 region: str = 'us-central1') -> Dict[str, Any]:
        """
        Obtém preços do Cloud Storage
        
        Args:
            storage_class: Classe de armazenamento
            region: Região GCP
        """
        try:
            # Tabela de preços do Cloud Storage (USD por GB por mês)
            storage_pricing = {
                'STANDARD': {
                    'us-central1': 0.020,
                    'us-east1': 0.020,
                    'us-west1': 0.020,
                    'europe-west1': 0.020,
                    'asia-southeast1': 0.020,
                    'multi-regional': 0.026
                },
                'NEARLINE': {
                    'us-central1': 0.010,
                    'us-east1': 0.010,
                    'us-west1': 0.010,
                    'europe-west1': 0.010,
                    'asia-southeast1': 0.010,
                    'multi-regional': 0.013
                },
                'COLDLINE': {
                    'us-central1': 0.004,
                    'us-east1': 0.004,
                    'us-west1': 0.004,
                    'europe-west1': 0.004,
                    'asia-southeast1': 0.004,
                    'multi-regional': 0.007
                },
                'ARCHIVE': {
                    'us-central1': 0.0012,
                    'us-east1': 0.0012,
                    'us-west1': 0.0012,
                    'europe-west1': 0.0012,
                    'asia-southeast1': 0.0012,
                    'multi-regional': 0.0025
                }
            }
            
            # Preços de operações (por 1000 operações)
            operation_pricing = {
                'STANDARD': {'read': 0.004, 'write': 0.005},
                'NEARLINE': {'read': 0.01, 'write': 0.01},
                'COLDLINE': {'read': 0.05, 'write': 0.10},
                'ARCHIVE': {'read': 0.50, 'write': 0.10}
            }
            
            storage_price = storage_pricing.get(storage_class, {}).get(region, 0.025)
            operations = operation_pricing.get(storage_class, {'read': 0.004, 'write': 0.005})
            
            pricing_data = {
                'storage_class': storage_class,
                'region': region,
                'storage_price_per_gb_month_usd': storage_price,
                'operations': {
                    'read_per_1k_ops_usd': operations['read'],
                    'write_per_1k_ops_usd': operations['write']
                },
                'examples': {
                    '100_gb_month': {
                        'storage_cost_usd': storage_price * 100,
                        'with_1k_reads_usd': storage_price * 100 + operations['read'],
                        'with_1k_writes_usd': storage_price * 100 + operations['write']
                    },
                    '1_tb_month': {
                        'storage_cost_usd': storage_price * 1024,
                        'with_10k_reads_usd': storage_price * 1024 + operations['read'] * 10,
                        'with_10k_writes_usd': storage_price * 1024 + operations['write'] * 10
                    }
                }
            }
            
            return {
                'success': True,
                'data': pricing_data,
                'timestamp': datetime.now().isoformat(),
                'note': 'Preços baseados na documentação oficial do GCP Cloud Storage'
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter preços Cloud Storage: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'PRICING_ERROR'
            }
    
    async def get_cost_recommendations(self, recommender_type: str = 'google.compute.instance.MachineTypeRecommender') -> Dict[str, Any]:
        """
        Obtém recomendações de otimização de custos
        
        Args:
            recommender_type: Tipo de recomendador
        """
        try:
            parent = f"projects/{self.project_id}/locations/global/recommenders/{recommender_type}"
            
            request = recommender_v1.ListRecommendationsRequest(
                parent=parent,
                page_size=100
            )
            
            page_result = self.recommender_client.list_recommendations(request=request)
            
            recommendations = []
            for recommendation in page_result:
                rec_data = {
                    'name': recommendation.name,
                    'description': recommendation.description,
                    'recommender_subtype': recommendation.recommender_subtype,
                    'last_refresh_time': recommendation.last_refresh_time.isoformat() if recommendation.last_refresh_time else None,
                    'priority': recommendation.priority.name if recommendation.priority else None,
                    'content': {
                        'operation_groups': []
                    }
                }
                
                # Extrair detalhes das operações
                if recommendation.content and recommendation.content.operation_groups:
                    for op_group in recommendation.content.operation_groups:
                        operations = []
                        for operation in op_group.operations:
                            operations.append({
                                'action': operation.action,
                                'resource_type': operation.resource_type,
                                'resource': operation.resource,
                                'path': operation.path,
                                'value': str(operation.value) if operation.value else None
                            })
                        
                        rec_data['content']['operation_groups'].append({
                            'operations': operations
                        })
                
                # Extrair impacto financeiro se disponível
                if recommendation.primary_impact:
                    rec_data['primary_impact'] = {
                        'category': recommendation.primary_impact.category.name,
                        'cost_projection': {
                            'cost': {
                                'currency_code': recommendation.primary_impact.cost_projection.cost.currency_code,
                                'units': str(recommendation.primary_impact.cost_projection.cost.units),
                                'nanos': recommendation.primary_impact.cost_projection.cost.nanos
                            },
                            'duration': str(recommendation.primary_impact.cost_projection.duration)
                        } if recommendation.primary_impact.cost_projection else None
                    }
                
                recommendations.append(rec_data)
            
            return {
                'success': True,
                'data': recommendations,
                'total_recommendations': len(recommendations),
                'recommender_type': recommender_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter recomendações: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'RECOMMENDATIONS_ERROR'
            }
    
    async def get_project_assets(self, asset_types: List[str] = None) -> Dict[str, Any]:
        """
        Obtém assets do projeto
        
        Args:
            asset_types: Lista de tipos de assets
        """
        try:
            parent = f"projects/{self.project_id}"
            
            request = asset_v1.ListAssetsRequest(
                parent=parent,
                asset_types=asset_types or [],
                page_size=1000
            )
            
            page_result = self.asset_client.list_assets(request=request)
            
            assets = []
            for asset in page_result:
                asset_data = {
                    'name': asset.name,
                    'asset_type': asset.asset_type,
                    'resource': {
                        'version': asset.resource.version,
                        'discovery_document_uri': asset.resource.discovery_document_uri,
                        'discovery_name': asset.resource.discovery_name,
                        'resource_url': asset.resource.resource_url,
                        'parent': asset.resource.parent,
                        'data': dict(asset.resource.data) if asset.resource.data else None
                    } if asset.resource else None,
                    'iam_policy': dict(asset.iam_policy) if asset.iam_policy else None,
                    'org_policy': list(asset.org_policy) if asset.org_policy else None,
                    'access_policy': dict(asset.access_policy) if asset.access_policy else None,
                    'os_inventory': dict(asset.os_inventory) if asset.os_inventory else None,
                    'related_assets': [dict(ra) for ra in asset.related_assets] if asset.related_assets else None,
                    'ancestors': list(asset.ancestors) if asset.ancestors else None,
                    'update_time': asset.update_time.isoformat() if asset.update_time else None
                }
                
                assets.append(asset_data)
            
            return {
                'success': True,
                'data': assets,
                'total_assets': len(assets),
                'asset_types_requested': asset_types,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter assets do projeto: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'ASSETS_ERROR'

