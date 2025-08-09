#!/usr/bin/env python3
"""
Script para deploy dos agentes Cloud Cost Analysis no Google Cloud Run.

Este script automatiza o processo de build e deploy de todos os componentes
do sistema de agentes no Cloud Run.
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configurações do projeto
PROJECT_ID = "lab-cloud-cost-agents"
REGION = "us-central1"
SERVICE_ACCOUNT_EMAIL = "lab-agents-prod-gcp@lab-cloud-cost-agents.iam.gserviceaccount.com"

# Configurações dos serviços
SERVICES = {
    "operational-manager": {
        "name": "operational-manager",
        "source": "agents/operational",
        "port": 8080,
        "memory": "1Gi",
        "cpu": "1",
        "min_instances": 0,
        "max_instances": 10,
        "description": "Agente gerente operacional principal"
    },
    "aws-specialist": {
        "name": "aws-specialist", 
        "source": "agents/specialists",
        "port": 8081,
        "memory": "1Gi",
        "cpu": "1",
        "min_instances": 0,
        "max_instances": 5,
        "description": "Agente especialista em AWS"
    },
    "gcp-specialist": {
        "name": "gcp-specialist",
        "source": "agents/specialists", 
        "port": 8082,
        "memory": "1Gi",
        "cpu": "1",
        "min_instances": 0,
        "max_instances": 5,
        "description": "Agente especialista em GCP"
    },
    "sla-coordinator": {
        "name": "sla-coordinator",
        "source": "agents/coordinators",
        "port": 8083,
        "memory": "512Mi",
        "cpu": "0.5",
        "min_instances": 0,
        "max_instances": 3,
        "description": "Agente coordenador de SLA"
    },
    "cost-coordinator": {
        "name": "cost-coordinator",
        "source": "agents/coordinators",
        "port": 8084,
        "memory": "512Mi", 
        "cpu": "0.5",
        "min_instances": 0,
        "max_instances": 3,
        "description": "Agente coordenador de custos"
    },
    "compliance-coordinator": {
        "name": "compliance-coordinator",
        "source": "agents/coordinators",
        "port": 8085,
        "memory": "512Mi",
        "cpu": "0.5", 
        "min_instances": 0,
        "max_instances": 3,
        "description": "Agente coordenador de compliance"
    },
    "legal-coordinator": {
        "name": "legal-coordinator",
        "source": "agents/coordinators",
        "port": 8086,
        "memory": "1Gi",
        "cpu": "1",
        "min_instances": 0,
        "max_instances": 3,
        "description": "Agente coordenador jurídico com RAG"
    },
    "report-generator": {
        "name": "report-generator",
        "source": "agents/coordinators",
        "port": 8087,
        "memory": "1Gi",
        "cpu": "1",
        "min_instances": 0,
        "max_instances": 2,
        "description": "Agente gerador de relatórios"
    },
    "mcp-aws": {
        "name": "mcp-aws",
        "source": "mcp/aws",
        "port": 8090,
        "memory": "512Mi",
        "cpu": "0.5",
        "min_instances": 1,
        "max_instances": 3,
        "description": "Servidor MCP para AWS"
    },
    "mcp-gcp": {
        "name": "mcp-gcp", 
        "source": "mcp/gcp",
        "port": 8091,
        "memory": "512Mi",
        "cpu": "0.5",
        "min_instances": 1,
        "max_instances": 3,
        "description": "Servidor MCP para GCP"
    },
    "mcp-sla": {
        "name": "mcp-sla",
        "source": "mcp/sla", 
        "port": 8092,
        "memory": "512Mi",
        "cpu": "0.5",
        "min_instances": 0,
        "max_instances": 2,
        "description": "Servidor MCP para análise SLA"
    },
    "mcp-rag": {
        "name": "mcp-rag",
        "source": "mcp/rag",
        "port": 8093,
        "memory": "1Gi",
        "cpu": "1",
        "min_instances": 0,
        "max_instances": 2,
        "description": "Servidor MCP para RAG"
    },
    "web-dashboard": {
        "name": "web-dashboard",
        "source": "web-dashboard",
        "port": 3000,
        "memory": "512Mi",
        "cpu": "0.5",
        "min_instances": 1,
        "max_instances": 5,
        "description": "Dashboard web interativo",
        "type": "frontend"
    }
}

class CloudRunDeployer:
    def __init__(self, project_id: str, region: str):
        self.project_id = project_id
        self.region = region
        self.deployed_services = []
        self.failed_services = []
        
    def run_command(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Executa comando e retorna resultado."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd
            )
            return {
                "success": True,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "stdout": e.stdout.strip() if e.stdout else "",
                "stderr": e.stderr.strip() if e.stderr else "",
                "returncode": e.returncode
            }
    
    def check_prerequisites(self) -> bool:
        """Verifica pré-requisitos para deploy."""
        print("🔍 Verificando pré-requisitos...")
        
        # Verificar gcloud
        result = self.run_command(["gcloud", "version"])
        if not result["success"]:
            print("❌ gcloud CLI não encontrado")
            return False
        print("✅ gcloud CLI encontrado")
        
        # Verificar autenticação
        result = self.run_command(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
        if not result["success"] or not result["stdout"]:
            print("❌ Nenhuma conta ativa no gcloud")
            return False
        print(f"✅ Autenticado como: {result['stdout']}")
        
        # Verificar projeto
        result = self.run_command(["gcloud", "config", "get-value", "project"])
        if result["stdout"] != self.project_id:
            print(f"⚠️  Configurando projeto: {self.project_id}")
            set_result = self.run_command(["gcloud", "config", "set", "project", self.project_id])
            if not set_result["success"]:
                print(f"❌ Erro ao configurar projeto: {set_result['stderr']}")
                return False
        print(f"✅ Projeto configurado: {self.project_id}")
        
        # Verificar APIs necessárias
        required_apis = [
            "run.googleapis.com",
            "cloudbuild.googleapis.com",
            "containerregistry.googleapis.com"
        ]
        
        for api in required_apis:
            result = self.run_command([
                "gcloud", "services", "list", 
                "--enabled", 
                f"--filter=name:{api}",
                "--format=value(name)"
            ])
            
            if not result["success"] or api not in result["stdout"]:
                print(f"❌ API não habilitada: {api}")
                return False
        
        print("✅ APIs necessárias habilitadas")
        return True
    
    def create_dockerfile(self, service_name: str, service_config: Dict[str, Any]) -> bool:
        """Cria Dockerfile para o serviço."""
        service_path = Path(service_config["source"])
        dockerfile_path = service_path / "Dockerfile"
        
        if service_config.get("type") == "frontend":
            # Dockerfile para React/Node.js
            dockerfile_content = f"""# Build stage
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE {service_config["port"]}

CMD ["nginx", "-g", "daemon off;"]
"""
            
            # Criar nginx.conf
            nginx_conf = """events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    sendfile        on;
    keepalive_timeout  65;
    
    server {
        listen 3000;
        server_name localhost;
        
        location / {
            root   /usr/share/nginx/html;
            index  index.html index.htm;
            try_files $uri $uri/ /index.html;
        }
        
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   /usr/share/nginx/html;
        }
    }
}
"""
            
            with open(service_path / "nginx.conf", "w") as f:
                f.write(nginx_conf)
                
        else:
            # Dockerfile para Python/Flask
            dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT={service_config["port"]}

# Expose port
EXPOSE {service_config["port"]}

# Run the application
CMD ["python", "app.py"]
"""
        
        try:
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)
            print(f"✅ Dockerfile criado para {service_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar Dockerfile para {service_name}: {e}")
            return False
    
    def create_app_py(self, service_name: str, service_config: Dict[str, Any]) -> bool:
        """Cria app.py básico para o serviço."""
        if service_config.get("type") == "frontend":
            return True  # Frontend não precisa de app.py
            
        service_path = Path(service_config["source"])
        app_py_path = service_path / "app.py"
        
        if app_py_path.exists():
            print(f"✅ app.py já existe para {service_name}")
            return True
        
        # Template básico do Flask
        app_content = f'''#!/usr/bin/env python3
"""
{service_config["description"]}
Aplicação Flask para deploy no Cloud Run.
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para frontend

@app.route("/")
def health_check():
    """Health check endpoint."""
    return jsonify({{
        "status": "healthy",
        "service": "{service_name}",
        "description": "{service_config["description"]}"
    }})

@app.route("/health")
def health():
    """Health check detalhado."""
    return jsonify({{
        "status": "healthy",
        "service": "{service_name}",
        "timestamp": "{{}}".format(__import__("datetime").datetime.now().isoformat()),
        "version": "1.0.0"
    }})

@app.route("/api/status")
def api_status():
    """Status da API."""
    return jsonify({{
        "api_status": "active",
        "service": "{service_name}",
        "endpoints": ["/", "/health", "/api/status"]
    }})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", {service_config["port"]}))
    app.run(host="0.0.0.0", port=port, debug=False)
'''
        
        try:
            with open(app_py_path, "w") as f:
                f.write(app_content)
            print(f"✅ app.py criado para {service_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar app.py para {service_name}: {e}")
            return False
    
    def create_requirements_txt(self, service_name: str, service_config: Dict[str, Any]) -> bool:
        """Cria requirements.txt para o serviço."""
        if service_config.get("type") == "frontend":
            return True  # Frontend usa package.json
            
        service_path = Path(service_config["source"])
        req_path = service_path / "requirements.txt"
        
        if req_path.exists():
            print(f"✅ requirements.txt já existe para {service_name}")
            return True
        
        # Requirements básicos
        requirements = """flask==3.0.0
flask-cors==4.0.0
gunicorn==21.2.0
google-cloud-logging==3.11.3
google-cloud-monitoring==2.22.2
requests==2.32.3
python-dotenv==1.0.1
"""
        
        try:
            with open(req_path, "w") as f:
                f.write(requirements)
            print(f"✅ requirements.txt criado para {service_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar requirements.txt para {service_name}: {e}")
            return False
    
    def deploy_service(self, service_name: str, service_config: Dict[str, Any]) -> bool:
        """Faz deploy de um serviço específico."""
        print(f"\n🚀 Fazendo deploy do serviço: {service_name}")
        print(f"   Descrição: {service_config['description']}")
        
        service_path = Path(service_config["source"])
        
        # Verificar se diretório existe
        if not service_path.exists():
            print(f"❌ Diretório não encontrado: {service_path}")
            return False
        
        # Criar arquivos necessários
        if not self.create_dockerfile(service_name, service_config):
            return False
            
        if not self.create_app_py(service_name, service_config):
            return False
            
        if not self.create_requirements_txt(service_name, service_config):
            return False
        
        # Fazer deploy no Cloud Run
        deploy_command = [
            "gcloud", "run", "deploy", service_name,
            "--source", ".",
            "--platform", "managed",
            "--region", self.region,
            "--allow-unauthenticated",
            f"--service-account={SERVICE_ACCOUNT_EMAIL}",
            f"--memory={service_config['memory']}",
            f"--cpu={service_config['cpu']}",
            f"--min-instances={service_config['min_instances']}",
            f"--max-instances={service_config['max_instances']}",
            f"--port={service_config['port']}",
            "--quiet"
        ]
        
        print(f"   Executando deploy...")
        result = self.run_command(deploy_command, cwd=str(service_path))
        
        if result["success"]:
            print(f"✅ Deploy concluído: {service_name}")
            
            # Obter URL do serviço
            url_command = [
                "gcloud", "run", "services", "describe", service_name,
                "--platform", "managed",
                "--region", self.region,
                "--format", "value(status.url)"
            ]
            
            url_result = self.run_command(url_command)
            if url_result["success"]:
                service_url = url_result["stdout"]
                print(f"   URL: {service_url}")
                self.deployed_services.append({
                    "name": service_name,
                    "url": service_url,
                    "description": service_config["description"]
                })
            
            return True
        else:
            print(f"❌ Erro no deploy de {service_name}: {result['stderr']}")
            self.failed_services.append(service_name)
            return False
    
    def deploy_all_services(self) -> bool:
        """Faz deploy de todos os serviços."""
        print(f"\n🚀 Iniciando deploy de {len(SERVICES)} serviços...")
        print("=" * 60)
        
        success_count = 0
        
        for service_name, service_config in SERVICES.items():
            try:
                if self.deploy_service(service_name, service_config):
                    success_count += 1
                
                # Pausa entre deploys
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Erro inesperado no deploy de {service_name}: {e}")
                self.failed_services.append(service_name)
        
        print(f"\n📊 Resultado do deploy:")
        print(f"✅ Serviços deployados: {success_count}")
        print(f"❌ Serviços com falha: {len(self.failed_services)}")
        
        return len(self.failed_services) == 0
    
    def create_service_map(self) -> bool:
        """Cria mapa de serviços deployados."""
        if not self.deployed_services:
            print("⚠️  Nenhum serviço deployado para mapear")
            return False
        
        service_map = {
            "project_id": self.project_id,
            "region": self.region,
            "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "services": self.deployed_services
        }
        
        try:
            with open("deployed_services.json", "w") as f:
                json.dump(service_map, f, indent=2)
            
            print(f"✅ Mapa de serviços salvo em: deployed_services.json")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar mapa de serviços: {e}")
            return False
    
    def print_summary(self):
        """Imprime resumo do deploy."""
        print("\n" + "=" * 60)
        print("📊 RESUMO DO DEPLOY")
        print("=" * 60)
        
        if self.deployed_services:
            print(f"\n✅ Serviços deployados com sucesso ({len(self.deployed_services)}):")
            for service in self.deployed_services:
                print(f"   • {service['name']}: {service['url']}")
                print(f"     {service['description']}")
        
        if self.failed_services:
            print(f"\n❌ Serviços que falharam ({len(self.failed_services)}):")
            for service in self.failed_services:
                print(f"   • {service}")
        
        if self.deployed_services:
            print(f"\n🌐 URLs principais:")
            dashboard_service = next((s for s in self.deployed_services if s['name'] == 'web-dashboard'), None)
            if dashboard_service:
                print(f"   Dashboard: {dashboard_service['url']}")
            
            manager_service = next((s for s in self.deployed_services if s['name'] == 'operational-manager'), None)
            if manager_service:
                print(f"   API Principal: {manager_service['url']}")
        
        print(f"\n📝 Próximos passos:")
        if len(self.deployed_services) == len(SERVICES):
            print("   1. Testar todos os serviços deployados")
            print("   2. Configurar monitoramento")
            print("   3. Configurar alertas")
            print("   4. Documentar URLs para usuários")
        else:
            print("   1. Corrigir problemas nos serviços que falharam")
            print("   2. Executar deploy novamente")
            print("   3. Verificar logs de erro")

def main():
    """Função principal."""
    print("🚀 Deploy Cloud Cost Agents - Google Cloud Run")
    print("=" * 60)
    print(f"Projeto: {PROJECT_ID}")
    print(f"Região: {REGION}")
    print(f"Serviços: {len(SERVICES)}")
    print("=" * 60)
    
    deployer = CloudRunDeployer(PROJECT_ID, REGION)
    
    # Verificar pré-requisitos
    if not deployer.check_prerequisites():
        print("\n❌ Pré-requisitos não atendidos. Corrija os problemas e tente novamente.")
        sys.exit(1)
    
    # Fazer deploy de todos os serviços
    success = deployer.deploy_all_services()
    
    # Criar mapa de serviços
    deployer.create_service_map()
    
    # Imprimir resumo
    deployer.print_summary()
    
    if success:
        print(f"\n🎉 Deploy concluído com sucesso!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Deploy concluído com algumas falhas.")
        sys.exit(1)

if __name__ == "__main__":
    main()

