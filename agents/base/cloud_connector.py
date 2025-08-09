"""
Conector para provedores de nuvem (AWS e GCP)
"""
import os
import sys
import boto3
from typing import Dict, Any, Optional, List
from google.cloud import billing_v1, compute_v1, storage
from google.oauth2 import service_account
from botocore.exceptions import ClientError, NoCredentialsError

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from config.project_config import config
from agents.base.logger import AgentLogger

class CloudConnector:
    """
    Conector unificado para AWS e Google Cloud Platform
    """
    
    def __init__(self):
        self.logger = AgentLogger("CloudConnector")
        self.aws_session = None
        self.gcp_credentials = None
        self.gcp_clients = {}
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Inicializa conexões com os provedores"""
        try:
            self._setup_aws_connection()
            self._setup_gcp_connection()
        except Exception as e:
            self.logger.error(f"Erro na inicialização das conexões: {str(e)}")
    
    def _setup_aws_connection(self):
        """Configura conexão com AWS"""
        try:
            self.aws_session = boto3.Session(
                aws_access_key_id=config.aws.access_key_id,
                aws_secret_access_key=config.aws.secret_access_key,
                region_name=config.aws.region
            )
            
            # Testar conexão
            sts_client = self.aws_session.client('sts')
            identity = sts_client.get_caller_identity()
            
            self.logger.info("Conexão AWS estabelecida", {
                "account_id": identity.get('Account'),
                "user_id": identity.get('UserId'),
                "region": config.aws.region
            })
            
        except (NoCredentialsError, ClientError) as e:
            self.logger.error(f"Erro na conexão AWS: {str(e)}")
            self.aws_session = None
    
    def _setup_gcp_connection(self):
        """Configura conexão com GCP"""
        try:
            if config.gcp.credentials_path and os.path.exists(config.gcp.credentials_path):
                self.gcp_credentials = service_account.Credentials.from_service_account_file(
                    config.gcp.credentials_path
                )
            else:
                # Tentar usar credenciais padrão
                from google.auth import default
                self.gcp_credentials, _ = default()
            
            # Inicializar clientes GCP
            self.gcp_clients = {
                'billing': billing_v1.CloudBillingClient(credentials=self.gcp_credentials),
                'compute': compute_v1.InstancesClient(credentials=self.gcp_credentials),
                'storage': storage.Client(credentials=self.gcp_credentials, project=config.gcp.project_id)
            }
            
            self.logger.info("Conexão GCP estabelecida", {
                "project_id": config.gcp.project_id,
                "service_account": config.gcp.service_account
            })
            
        except Exception as e:
            self.logger.error(f"Erro na conexão GCP: {str(e)}")
            self.gcp_credentials = None
    
    def is_aws_connected(self) -> bool:
        """Verifica se a conexão AWS está ativa"""
        return self.aws_session is not None
    
    def is_gcp_connected(self) -> bool:
        """Verifica se a conexão GCP está ativa"""
        return self.gcp_credentials is not None
    
    def connect_aws(self) -> Dict[str, Any]:
        """Estabelece/verifica conexão AWS"""
        if not self.is_aws_connected():
            self._setup_aws_connection()
        
        if self.is_aws_connected():
            return {
                "status": "connected",
                "provider": "AWS",
                "region": config.aws.region,
                "services_available": ["cost_explorer", "ec2", "s3", "rds"]
            }
        else:
            return {
                "status": "failed",
                "provider": "AWS",
                "error": "Credenciais não configuradas ou inválidas"
            }
    
    def connect_gcp(self) -> Dict[str, Any]:
        """Estabelece/verifica conexão GCP"""
        if not self.is_gcp_connected():
            self._setup_gcp_connection()
        
        if self.is_gcp_connected():
            return {
                "status": "connected",
                "provider": "GCP",
                "project_id": config.gcp.project_id,
                "services_available": ["billing", "compute", "storage", "bigquery"]
            }
        else:
            return {
                "status": "failed",
                "provider": "GCP",
                "error": "Credenciais não configuradas ou inválidas"
            }
    
    def get_aws_cost_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Obtém dados de custo da AWS"""
        if not self.is_aws_connected():
            return {"error": "AWS não conectada"}
        
        try:
            cost_explorer = self.aws_session.client('ce')
            
            response = cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            self.logger.log_cost_analysis("AWS", {
                "period": f"{start_date} to {end_date}",
                "total_results": len(response.get('ResultsByTime', []))
            })
            
            return {
                "provider": "AWS",
                "period": f"{start_date} to {end_date}",
                "data": response
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados de custo AWS: {str(e)}")
            return {"error": str(e)}
    
    def get_gcp_cost_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Obtém dados de custo do GCP"""
        if not self.is_gcp_connected():
            return {"error": "GCP não conectada"}
        
        try:
            billing_client = self.gcp_clients['billing']
            
            # Listar contas de billing
            billing_accounts = list(billing_client.list_billing_accounts())
            
            if not billing_accounts:
                return {"error": "Nenhuma conta de billing encontrada"}
            
            # Para cada conta de billing, obter dados de custo
            cost_data = []
            for account in billing_accounts:
                # Aqui seria implementada a lógica específica de obtenção de custos
                # usando a Cloud Billing API
                pass
            
            self.logger.log_cost_analysis("GCP", {
                "period": f"{start_date} to {end_date}",
                "billing_accounts": len(billing_accounts)
            })
            
            return {
                "provider": "GCP",
                "period": f"{start_date} to {end_date}",
                "billing_accounts": len(billing_accounts),
                "data": cost_data
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados de custo GCP: {str(e)}")
            return {"error": str(e)}
    
    def get_aws_resources(self) -> Dict[str, Any]:
        """Lista recursos AWS"""
        if not self.is_aws_connected():
            return {"error": "AWS não conectada"}
        
        try:
            resources = {}
            
            # EC2 Instances
            ec2 = self.aws_session.client('ec2')
            instances = ec2.describe_instances()
            resources['ec2_instances'] = len([
                instance for reservation in instances['Reservations']
                for instance in reservation['Instances']
            ])
            
            # S3 Buckets
            s3 = self.aws_session.client('s3')
            buckets = s3.list_buckets()
            resources['s3_buckets'] = len(buckets['Buckets'])
            
            # RDS Instances
            rds = self.aws_session.client('rds')
            db_instances = rds.describe_db_instances()
            resources['rds_instances'] = len(db_instances['DBInstances'])
            
            return {
                "provider": "AWS",
                "resources": resources,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao listar recursos AWS: {str(e)}")
            return {"error": str(e)}
    
    def get_gcp_resources(self) -> Dict[str, Any]:
        """Lista recursos GCP"""
        if not self.is_gcp_connected():
            return {"error": "GCP não conectada"}
        
        try:
            resources = {}
            
            # Compute Engine Instances
            compute_client = self.gcp_clients['compute']
            # Aqui seria implementada a lógica para listar instâncias
            # em todas as zonas do projeto
            
            # Cloud Storage Buckets
            storage_client = self.gcp_clients['storage']
            buckets = list(storage_client.list_buckets())
            resources['storage_buckets'] = len(buckets)
            
            return {
                "provider": "GCP",
                "project_id": config.gcp.project_id,
                "resources": resources,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao listar recursos GCP: {str(e)}")
            return {"error": str(e)}
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Retorna status das conexões"""
        return {
            "aws": {
                "connected": self.is_aws_connected(),
                "region": config.aws.region if self.is_aws_connected() else None
            },
            "gcp": {
                "connected": self.is_gcp_connected(),
                "project_id": config.gcp.project_id if self.is_gcp_connected() else None
            },
            "timestamp": self._get_timestamp()
        }

