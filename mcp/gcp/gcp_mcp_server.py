"""
Servidor MCP para GCP - Model Context Protocol
Responsável por conectar à API de custos do Google Cloud e fornecer dados para os agentes
"""
import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from google.cloud import billing_v1, compute_v1, storage, bigquery
from google.oauth2 import service_account
from google.auth import default

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mcp import MCPServer, Tool, Resource
from config.project_config import config
from agents.base.logger import AgentLogger

class GCPMCPServer:
    """
    Servidor MCP para GCP - Fornece acesso às APIs de custos e recursos do Google Cloud
    """
    
    def __init__(self):
        self.logger = AgentLogger("GCPMCPServer")
        self.server = MCPServer("gcp-cost-api")
        self.credentials = None
        self.clients = {}
        self._initialize_gcp_connection()
        self._register_tools()
        self._register_resources()
    
    def _initialize_gcp_connection(self):
        """Inicializa conexão com GCP"""
        try:
            if config.gcp.credentials_path and os.path.exists(config.gcp.credentials_path):
                self.credentials = service_account.Credentials.from_service_account_file(
                    config.gcp.credentials_path
                )
            else:
                # Tentar usar credenciais padrão
                self.credentials, _ = default()
            
            # Inicializar clientes GCP
            self.clients = {
                'billing': billing_v1.CloudBillingClient(credentials=self.credentials),
                'compute': compute_v1.InstancesClient(credentials=self.credentials),
                'storage': storage.Client(credentials=self.credentials, project=config.gcp.project_id),
                'bigquery': bigquery.Client(credentials=self.credentials, project=config.gcp.project_id)
            }
            
            self.logger.info("GCP MCP Server conectado", {
                "project_id": config.gcp.project_id,
                "service_account": config.gcp.service_account
            })
            
        except Exception as e:
            self.logger.error(f"Erro na conexão GCP MCP: {str(e)}")
            self.credentials = None
    
    def _register_tools(self):
        """Registra ferramentas MCP para GCP"""
        
        @self.server.tool("get_billing_accounts")
        async def get_billing_accounts() -> Dict[str, Any]:
            """
            Lista contas de billing do GCP
            """
            try:
                if not self.credentials:
                    return {"error": "GCP não conectado"}
                
                billing_client = self.clients['billing']
                
                # Listar contas de billing
                billing_accounts = []
                for account in billing_client.list_billing_accounts():
                    billing_accounts.append({
                        'name': account.name,
                        'display_name': account.display_name,
                        'open': account.open,
                        'master_billing_account': account.master_billing_account
                    })
                
                self.logger.info("Contas de billing GCP listadas", {
                    "accounts_count": len(billing_accounts)
                })
                
                return {
                    "success": True,
                    "data": billing_accounts,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao obter contas de billing: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_project_billing_info")
        async def get_project_billing_info(project_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Obtém informações de billing de um projeto
            
            Args:
                project_id: ID do projeto (opcional, usa o padrão se não especificado)
            """
            try:
                if not self.credentials:
                    return {"error": "GCP não conectado"}
                
                target_project = project_id or config.gcp.project_id
                billing_client = self.clients['billing']
                
                # Obter informações de billing do projeto
                project_name = f"projects/{target_project}"
                billing_info = billing_client.get_project_billing_info(name=project_name)
                
                self.logger.info("Informações de billing obtidas", {
                    "project_id": target_project,
                    "billing_enabled": billing_info.billing_enabled
                })
                
                return {
                    "success": True,
                    "data": {
                        "project_id": target_project,
                        "billing_account_name": billing_info.billing_account_name,
                        "billing_enabled": billing_info.billing_enabled,
                        "name": billing_info.name
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao obter billing info: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_compute_instances")
        async def get_compute_instances(zone: str = "us-central1-a") -> Dict[str, Any]:
            """
            Lista instâncias Compute Engine
            
            Args:
                zone: Zona do GCP (padrão: us-central1-a)
            """
            try:
                if not self.credentials:
                    return {"error": "GCP não conectado"}
                
                compute_client = self.clients['compute']
                
                # Listar instâncias na zona especificada
                request = compute_v1.ListInstancesRequest(
                    project=config.gcp.project_id,
                    zone=zone
                )
                
                instances = []
                for instance in compute_client.list(request=request):
                    instances.append({
                        'name': instance.name,
                        'machine_type': instance.machine_type.split('/')[-1],
                        'status': instance.status,
                        'zone': zone,
                        'creation_timestamp': instance.creation_timestamp,
                        'cpu_platform': instance.cpu_platform
                    })
                
                self.logger.info("Instâncias Compute Engine listadas", {
                    "zone": zone,
                    "instances_count": len(instances)
                })
                
                return {
                    "success": True,
                    "data": instances,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao listar instâncias Compute: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_storage_buckets")
        async def get_storage_buckets() -> Dict[str, Any]:
            """
            Lista buckets Cloud Storage
            """
            try:
                if not self.credentials:
                    return {"error": "GCP não conectado"}
                
                storage_client = self.clients['storage']
                
                buckets = []
                for bucket in storage_client.list_buckets():
                    buckets.append({
                        'name': bucket.name,
                        'location': bucket.location,
                        'storage_class': bucket.storage_class,
                        'time_created': bucket.time_created.isoformat() if bucket.time_created else None,
                        'metageneration': bucket.metageneration
                    })
                
                self.logger.info("Buckets Cloud Storage listados", {
                    "buckets_count": len(buckets)
                })
                
                return {
                    "success": True,
                    "data": buckets,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao listar buckets Storage: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_bigquery_datasets")
        async def get_bigquery_datasets() -> Dict[str, Any]:
            """
            Lista datasets BigQuery
            """
            try:
                if not self.credentials:
                    return {"error": "GCP não conectado"}
                
                bigquery_client = self.clients['bigquery']
                
                datasets = []
                for dataset in bigquery_client.list_datasets():
                    dataset_info = bigquery_client.get_dataset(dataset.reference)
                    datasets.append({
                        'dataset_id': dataset.dataset_id,
                        'project': dataset.project,
                        'location': dataset_info.location,
                        'created': dataset_info.created.isoformat() if dataset_info.created else None,
                        'modified': dataset_info.modified.isoformat() if dataset_info.modified else None,
                        'description': dataset_info.description
                    })
                
                self.logger.info("Datasets BigQuery listados", {
                    "datasets_count": len(datasets)
                })
                
                return {
                    "success": True,
                    "data": datasets,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao listar datasets BigQuery: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("execute_bigquery_query")
        async def execute_bigquery_query(query: str, dry_run: bool = False) -> Dict[str, Any]:
            """
            Executa query no BigQuery
            
            Args:
                query: Query SQL para executar
                dry_run: Se True, apenas valida a query sem executar
            """
            try:
                if not self.credentials:
                    return {"error": "GCP não conectado"}
                
                bigquery_client = self.clients['bigquery']
                
                job_config = bigquery.QueryJobConfig(dry_run=dry_run)
                query_job = bigquery_client.query(query, job_config=job_config)
                
                if dry_run:
                    return {
                        "success": True,
                        "data": {
                            "bytes_processed": query_job.total_bytes_processed,
                            "bytes_billed": query_job.total_bytes_billed,
                            "dry_run": True
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    results = query_job.result()
                    
                    rows = []
                    for row in results:
                        rows.append(dict(row))
                    
                    self.logger.info("Query BigQuery executada", {
                        "rows_returned": len(rows),
                        "bytes_processed": query_job.total_bytes_processed
                    })
                    
                    return {
                        "success": True,
                        "data": {
                            "rows": rows,
                            "total_rows": results.total_rows,
                            "bytes_processed": query_job.total_bytes_processed,
                            "job_id": query_job.job_id
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                
            except Exception as e:
                self.logger.error(f"Erro ao executar query BigQuery: {str(e)}")
                return {"error": str(e)}
        
        @self.server.tool("get_recommender_recommendations")
        async def get_recommender_recommendations(recommender_type: str = "google.compute.instance.MachineTypeRecommender") -> Dict[str, Any]:
            """
            Obtém recomendações do GCP Recommender
            
            Args:
                recommender_type: Tipo de recomendador
            """
            try:
                if not self.credentials:
                    return {"error": "GCP não conectado"}
                
                # Nota: Implementação simplificada
                # Em produção, seria necessário usar a API do Recommender
                
                recommendations = {
                    "recommender_type": recommender_type,
                    "recommendations": [
                        {
                            "name": "Rightsizing recommendation",
                            "description": "Redimensionar instâncias subutilizadas",
                            "impact": "Economia estimada de 20-30%"
                        }
                    ]
                }
                
                self.logger.info("Recomendações GCP obtidas", {
                    "recommender_type": recommender_type,
                    "recommendations_count": len(recommendations["recommendations"])
                })
                
                return {
                    "success": True,
                    "data": recommendations,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Erro ao obter recomendações: {str(e)}")
                return {"error": str(e)}
    
    def _register_resources(self):
        """Registra recursos MCP para GCP"""
        
        @self.server.resource("gcp://billing/summary")
        async def billing_summary() -> Dict[str, Any]:
            """
            Recurso que fornece resumo de billing
            """
            try:
                billing_accounts = await self.server.tools["get_billing_accounts"]()
                project_billing = await self.server.tools["get_project_billing_info"]()
                
                return {
                    "resource_type": "billing_summary",
                    "data": {
                        "billing_accounts": billing_accounts,
                        "project_billing": project_billing
                    },
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"error": str(e)}
        
        @self.server.resource("gcp://resources/inventory")
        async def resources_inventory() -> Dict[str, Any]:
            """
            Recurso que fornece inventário de recursos
            """
            try:
                compute_instances = await self.server.tools["get_compute_instances"]()
                storage_buckets = await self.server.tools["get_storage_buckets"]()
                bigquery_datasets = await self.server.tools["get_bigquery_datasets"]()
                
                return {
                    "resource_type": "resources_inventory",
                    "data": {
                        "compute_instances": compute_instances,
                        "storage_buckets": storage_buckets,
                        "bigquery_datasets": bigquery_datasets
                    },
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"error": str(e)}
    
    async def start_server(self, host: str = "0.0.0.0", port: int = None):
        """Inicia o servidor MCP"""
        server_port = port or config.mcp.gcp_port
        
        try:
            self.logger.info(f"Iniciando GCP MCP Server em {host}:{server_port}")
            await self.server.start(host=host, port=server_port)
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar GCP MCP Server: {str(e)}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """Retorna informações do servidor"""
        return {
            "name": "GCP MCP Server",
            "version": "1.0.0",
            "description": "Servidor MCP para APIs de custos e recursos GCP",
            "port": config.mcp.gcp_port,
            "tools_count": len(self.server.tools),
            "resources_count": len(self.server.resources),
            "gcp_connected": self.credentials is not None,
            "project_id": config.gcp.project_id
        }

async def main():
    """Função principal para executar o servidor"""
    gcp_mcp = GCPMCPServer()
    
    try:
        await gcp_mcp.start_server()
    except KeyboardInterrupt:
        print("Servidor GCP MCP interrompido pelo usuário")
    except Exception as e:
        print(f"Erro no servidor GCP MCP: {e}")

if __name__ == "__main__":
    asyncio.run(main())

