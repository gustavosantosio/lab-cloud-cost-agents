"""
Configuração principal do projeto Cloud Cost Agents
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class GCPConfig:
    """Configurações do Google Cloud Platform"""
    project_id: str = "lab-cloud-cost-agents"
    service_account: str = "lab-agents-prod-gcp@lab-cloud-cost-agents.iam.gserviceaccount.com"
    credentials_path: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    rag_bucket: str = "lab-rag-files-bucket"
    region: str = "us-central1"
    
@dataclass
class AWSConfig:
    """Configurações da AWS"""
    region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
@dataclass
class BigQueryConfig:
    """Configurações do BigQuery para Data Lake"""
    project_id: str = "lab-cloud-cost-agents"
    dataset_raw: str = "cost_analysis_raw"
    dataset_trusted: str = "cost_analysis_trusted"
    dataset_refined: str = "cost_analysis_refined"
    location: str = "US"

@dataclass
class MCPConfig:
    """Configurações dos servidores MCP"""
    aws_port: int = 8001
    gcp_port: int = 8002
    sla_port: int = 8003
    rag_port: int = 8004
    host: str = "0.0.0.0"

@dataclass
class AgentConfig:
    """Configurações dos agentes"""
    max_iterations: int = 10
    timeout_seconds: int = 300
    log_level: str = "INFO"
    
@dataclass
class WebConfig:
    """Configurações da interface web"""
    frontend_port: int = 3000
    backend_port: int = 5000
    host: str = "0.0.0.0"

class ProjectConfig:
    """Configuração centralizada do projeto"""
    
    def __init__(self):
        self.gcp = GCPConfig()
        self.aws = AWSConfig()
        self.bigquery = BigQueryConfig()
        self.mcp = MCPConfig()
        self.agents = AgentConfig()
        self.web = WebConfig()
        
    def validate_config(self) -> List[str]:
        """Valida as configurações e retorna lista de erros"""
        errors = []
        
        if not self.gcp.credentials_path or not os.path.exists(self.gcp.credentials_path):
            errors.append("GOOGLE_APPLICATION_CREDENTIALS não configurado ou arquivo não encontrado")
            
        if not self.aws.access_key_id:
            errors.append("AWS_ACCESS_KEY_ID não configurado")
            
        if not self.aws.secret_access_key:
            errors.append("AWS_SECRET_ACCESS_KEY não configurado")
            
        return errors
    
    def get_required_gcp_apis(self) -> List[str]:
        """Retorna lista de APIs do GCP necessárias"""
        return [
            "run.googleapis.com",
            "cloudfunctions.googleapis.com", 
            "bigquery.googleapis.com",
            "storage.googleapis.com",
            "cloudbilling.googleapis.com",
            "compute.googleapis.com",
            "cloudresourcemanager.googleapis.com",
            "iamcredentials.googleapis.com",
            "aiplatform.googleapis.com"
        ]
    
    def get_deployment_strategy(self) -> Dict[str, str]:
        """
        Retorna estratégia de deploy recomendada para cada componente
        
        Análise:
        - Cloud Run: Melhor para agentes que precisam escalar automaticamente
        - Cloud Functions: Melhor para MCPs com execução sob demanda
        - Compute Engine: Melhor para componentes que precisam rodar continuamente
        """
        return {
            "agents": "cloud_run",  # Escalabilidade automática para processamento
            "mcp_servers": "cloud_functions",  # Execução sob demanda
            "web_backend": "cloud_run",  # API que precisa estar sempre disponível
            "web_frontend": "cloud_storage",  # Hospedagem estática
            "bigquery_etl": "cloud_functions"  # Processamento de dados sob demanda
        }

# Instância global da configuração
config = ProjectConfig()

