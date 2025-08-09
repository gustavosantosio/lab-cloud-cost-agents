#!/usr/bin/env python3
"""
Script para deploy dos agentes Cloud Cost Analysis no Google Compute Engine.

Este script cria uma instância VM e configura todos os agentes em containers Docker
para máximo controle e performance.
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
ZONE = "us-central1-a"
REGION = "us-central1"
SERVICE_ACCOUNT_EMAIL = "lab-agents-prod-gcp@lab-cloud-cost-agents.iam.gserviceaccount.com"

# Configurações da instância
INSTANCE_CONFIG = {
    "name": "cloud-cost-agents-vm",
    "machine_type": "e2-standard-4",  # 4 vCPUs, 16GB RAM
    "boot_disk_size": "50GB",
    "boot_disk_type": "pd-ssd",
    "image_family": "ubuntu-2204-lts",
    "image_project": "ubuntu-os-cloud",
    "network": "default",
    "subnet": "default",
    "tags": ["cloud-cost-agents", "http-server", "https-server"],
    "scopes": [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/compute",
        "https://www.googleapis.com/auth/devstorage.read_write",
        "https://www.googleapis.com/auth/bigquery",
        "https://www.googleapis.com/auth/monitoring.write",
        "https://www.googleapis.com/auth/logging.write"
    ]
}

class ComputeEngineDeployer:
    def __init__(self, project_id: str, zone: str):
        self.project_id = project_id
        self.zone = zone
        self.instance_name = INSTANCE_CONFIG["name"]
        self.instance_ip = None
        
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
        
        # Verificar zona
        zone_result = self.run_command(["gcloud", "config", "set", "compute/zone", self.zone])
        if zone_result["success"]:
            print(f"✅ Zona configurada: {self.zone}")
        
        return True
    
    def create_startup_script(self) -> str:
        """Cria script de inicialização da VM."""
        startup_script = """#!/bin/bash

# Script de inicialização para Cloud Cost Agents VM
set -e

# Atualizar sistema
apt-get update
apt-get upgrade -y

# Instalar dependências
apt-get install -y \\
    apt-transport-https \\
    ca-certificates \\
    curl \\
    gnupg \\
    lsb-release \\
    software-properties-common \\
    git \\
    python3 \\
    python3-pip \\
    python3-venv \\
    nginx \\
    supervisor

# Instalar Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Configurar Docker
systemctl start docker
systemctl enable docker
usermod -aG docker $USER

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Criar diretório do projeto
mkdir -p /opt/cloud-cost-agents
cd /opt/cloud-cost-agents

# Clonar projeto (se disponível no GitHub)
# git clone https://github.com/seu-usuario/cloud-cost-agents.git .

# Criar estrutura básica
mkdir -p {agents/{operational,specialists,coordinators},mcp/{aws,gcp,sla,rag},web-dashboard,logs,data}

# Configurar variáveis de ambiente
cat > .env << 'EOF'
PROJECT_ID=""" + PROJECT_ID + """
GOOGLE_APPLICATION_CREDENTIALS=/opt/cloud-cost-agents/credentials.json
OPENAI_API_KEY=${OPENAI_API_KEY}
FLASK_ENV=production
PYTHONPATH=/opt/cloud-cost-agents
EOF

# Criar docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Agente Operacional
  operational-manager:
    build: ./agents/operational
    ports:
      - "8080:8080"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8080
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped
    depends_on:
      - mcp-aws
      - mcp-gcp

  # Especialistas
  aws-specialist:
    build: ./agents/specialists
    ports:
      - "8081:8081"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8081
      - AGENT_TYPE=aws
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  gcp-specialist:
    build: ./agents/specialists
    ports:
      - "8082:8082"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8082
      - AGENT_TYPE=gcp
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  # Coordenadores
  sla-coordinator:
    build: ./agents/coordinators
    ports:
      - "8083:8083"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8083
      - AGENT_TYPE=sla
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  cost-coordinator:
    build: ./agents/coordinators
    ports:
      - "8084:8084"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8084
      - AGENT_TYPE=cost
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  compliance-coordinator:
    build: ./agents/coordinators
    ports:
      - "8085:8085"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8085
      - AGENT_TYPE=compliance
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  legal-coordinator:
    build: ./agents/coordinators
    ports:
      - "8086:8086"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8086
      - AGENT_TYPE=legal
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped
    depends_on:
      - mcp-rag

  report-generator:
    build: ./agents/coordinators
    ports:
      - "8087:8087"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8087
      - AGENT_TYPE=report
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  # Servidores MCP
  mcp-aws:
    build: ./mcp/aws
    ports:
      - "8090:8090"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8090
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  mcp-gcp:
    build: ./mcp/gcp
    ports:
      - "8091:8091"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8091
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  mcp-sla:
    build: ./mcp/sla
    ports:
      - "8092:8092"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8092
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  mcp-rag:
    build: ./mcp/rag
    ports:
      - "8093:8093"
    environment:
      - PROJECT_ID=""" + PROJECT_ID + """
      - PORT=8093
    volumes:
      - ./logs:/app/logs
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  # Dashboard Web
  web-dashboard:
    build: ./web-dashboard
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web-dashboard
      - operational-manager
    restart: unless-stopped

EOF

# Criar configuração do Nginx
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream dashboard {
        server web-dashboard:3000;
    }
    
    upstream api {
        server operational-manager:8080;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Dashboard
        location / {
            proxy_pass http://dashboard;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # API
        location /api/ {
            proxy_pass http://api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            return 200 'OK';
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Configurar permissões
chown -R $USER:$USER /opt/cloud-cost-agents
chmod +x /opt/cloud-cost-agents

# Log de conclusão
echo "$(date): Startup script concluído" >> /var/log/startup-script.log

# Sinalizar conclusão
touch /opt/cloud-cost-agents/startup-complete
"""
        
        return startup_script
    
    def create_instance(self) -> bool:
        """Cria instância do Compute Engine."""
        print(f"\n🚀 Criando instância: {self.instance_name}")
        
        # Verificar se instância já existe
        check_command = [
            "gcloud", "compute", "instances", "describe", self.instance_name,
            f"--zone={self.zone}",
            "--format=value(name)"
        ]
        
        result = self.run_command(check_command)
        if result["success"]:
            print(f"⚠️  Instância já existe: {self.instance_name}")
            return self.get_instance_ip()
        
        # Criar script de inicialização
        startup_script = self.create_startup_script()
        
        # Salvar script temporariamente
        with open("/tmp/startup-script.sh", "w") as f:
            f.write(startup_script)
        
        # Comando de criação da instância
        create_command = [
            "gcloud", "compute", "instances", "create", self.instance_name,
            f"--zone={self.zone}",
            f"--machine-type={INSTANCE_CONFIG['machine_type']}",
            f"--network-interface=network-tier=PREMIUM,subnet={INSTANCE_CONFIG['subnet']}",
            "--maintenance-policy=MIGRATE",
            "--provisioning-model=STANDARD",
            f"--service-account={SERVICE_ACCOUNT_EMAIL}",
            f"--scopes={','.join(INSTANCE_CONFIG['scopes'])}",
            f"--tags={','.join(INSTANCE_CONFIG['tags'])}",
            f"--create-disk=auto-delete=yes,boot=yes,device-name={self.instance_name},image=projects/{INSTANCE_CONFIG['image_project']}/global/images/family/{INSTANCE_CONFIG['image_family']},mode=rw,size={INSTANCE_CONFIG['boot_disk_size']},type=projects/{self.project_id}/zones/{self.zone}/diskTypes/{INSTANCE_CONFIG['boot_disk_type']}",
            "--no-shielded-secure-boot",
            "--shielded-vtpm",
            "--shielded-integrity-monitoring",
            "--reservation-affinity=any",
            "--metadata-from-file=startup-script=/tmp/startup-script.sh"
        ]
        
        print("   Executando criação da instância...")
        result = self.run_command(create_command)
        
        if result["success"]:
            print(f"✅ Instância criada: {self.instance_name}")
            return self.get_instance_ip()
        else:
            print(f"❌ Erro ao criar instância: {result['stderr']}")
            return False
    
    def get_instance_ip(self) -> bool:
        """Obtém IP externo da instância."""
        print("🔍 Obtendo IP da instância...")
        
        ip_command = [
            "gcloud", "compute", "instances", "describe", self.instance_name,
            f"--zone={self.zone}",
            "--format=value(networkInterfaces[0].accessConfigs[0].natIP)"
        ]
        
        result = self.run_command(ip_command)
        if result["success"] and result["stdout"]:
            self.instance_ip = result["stdout"]
            print(f"✅ IP da instância: {self.instance_ip}")
            return True
        else:
            print("❌ Erro ao obter IP da instância")
            return False
    
    def wait_for_startup(self, timeout: int = 600) -> bool:
        """Aguarda conclusão do script de inicialização."""
        print("⏳ Aguardando conclusão da inicialização...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Verificar se arquivo de conclusão existe
            check_command = [
                "gcloud", "compute", "ssh", self.instance_name,
                f"--zone={self.zone}",
                "--command=test -f /opt/cloud-cost-agents/startup-complete && echo 'READY' || echo 'NOT_READY'",
                "--quiet"
            ]
            
            result = self.run_command(check_command)
            if result["success"] and "READY" in result["stdout"]:
                print("✅ Inicialização concluída")
                return True
            
            print("   Aguardando... (pode levar alguns minutos)")
            time.sleep(30)
        
        print("⚠️  Timeout na inicialização. Verifique logs da instância.")
        return False
    
    def configure_firewall(self) -> bool:
        """Configura regras de firewall."""
        print("🔥 Configurando regras de firewall...")
        
        # Regra para HTTP
        http_rule = [
            "gcloud", "compute", "firewall-rules", "create", "cloud-cost-agents-http",
            "--allow=tcp:80,tcp:3000,tcp:8080-8093",
            "--source-ranges=0.0.0.0/0",
            "--target-tags=cloud-cost-agents",
            "--description=Allow HTTP traffic for Cloud Cost Agents"
        ]
        
        result = self.run_command(http_rule)
        if result["success"] or "already exists" in result["stderr"]:
            print("✅ Regra HTTP configurada")
        else:
            print(f"⚠️  Erro na regra HTTP: {result['stderr']}")
        
        # Regra para HTTPS
        https_rule = [
            "gcloud", "compute", "firewall-rules", "create", "cloud-cost-agents-https",
            "--allow=tcp:443",
            "--source-ranges=0.0.0.0/0",
            "--target-tags=cloud-cost-agents",
            "--description=Allow HTTPS traffic for Cloud Cost Agents"
        ]
        
        result = self.run_command(https_rule)
        if result["success"] or "already exists" in result["stderr"]:
            print("✅ Regra HTTPS configurada")
        else:
            print(f"⚠️  Erro na regra HTTPS: {result['stderr']}")
        
        return True
    
    def deploy_application(self) -> bool:
        """Faz deploy da aplicação na instância."""
        print("📦 Fazendo deploy da aplicação...")
        
        # Copiar arquivos do projeto
        copy_command = [
            "gcloud", "compute", "scp", "--recurse",
            ".", f"{self.instance_name}:/opt/cloud-cost-agents/",
            f"--zone={self.zone}",
            "--quiet"
        ]
        
        result = self.run_command(copy_command)
        if not result["success"]:
            print(f"❌ Erro ao copiar arquivos: {result['stderr']}")
            return False
        
        print("✅ Arquivos copiados")
        
        # Executar docker-compose
        compose_command = [
            "gcloud", "compute", "ssh", self.instance_name,
            f"--zone={self.zone}",
            "--command=cd /opt/cloud-cost-agents && docker-compose up -d",
            "--quiet"
        ]
        
        result = self.run_command(compose_command)
        if result["success"]:
            print("✅ Aplicação deployada com Docker Compose")
            return True
        else:
            print(f"❌ Erro no deploy: {result['stderr']}")
            return False
    
    def print_summary(self):
        """Imprime resumo do deploy."""
        print("\n" + "=" * 60)
        print("📊 RESUMO DO DEPLOY - COMPUTE ENGINE")
        print("=" * 60)
        
        if self.instance_ip:
            print(f"\n✅ Instância criada com sucesso:")
            print(f"   Nome: {self.instance_name}")
            print(f"   IP: {self.instance_ip}")
            print(f"   Zona: {self.zone}")
            print(f"   Tipo: {INSTANCE_CONFIG['machine_type']}")
            
            print(f"\n🌐 URLs de acesso:")
            print(f"   Dashboard: http://{self.instance_ip}")
            print(f"   API Principal: http://{self.instance_ip}/api")
            print(f"   Health Check: http://{self.instance_ip}/health")
            
            print(f"\n🔧 Serviços disponíveis:")
            services = [
                ("Dashboard Web", "3000"),
                ("Gerente Operacional", "8080"),
                ("Especialista AWS", "8081"),
                ("Especialista GCP", "8082"),
                ("Coordenador SLA", "8083"),
                ("Coordenador Custos", "8084"),
                ("Coordenador Compliance", "8085"),
                ("Coordenador Jurídico", "8086"),
                ("Gerador Relatórios", "8087"),
                ("MCP AWS", "8090"),
                ("MCP GCP", "8091"),
                ("MCP SLA", "8092"),
                ("MCP RAG", "8093")
            ]
            
            for service_name, port in services:
                print(f"   {service_name}: http://{self.instance_ip}:{port}")
        
        print(f"\n📝 Próximos passos:")
        print("   1. Aguardar inicialização completa (5-10 minutos)")
        print("   2. Testar acesso ao dashboard")
        print("   3. Configurar SSL/HTTPS (opcional)")
        print("   4. Configurar monitoramento")
        print("   5. Configurar backup automático")
        
        print(f"\n🔧 Comandos úteis:")
        print(f"   SSH: gcloud compute ssh {self.instance_name} --zone={self.zone}")
        print(f"   Logs: gcloud compute ssh {self.instance_name} --zone={self.zone} --command='docker-compose logs'")
        print(f"   Restart: gcloud compute ssh {self.instance_name} --zone={self.zone} --command='docker-compose restart'")

def main():
    """Função principal."""
    print("🚀 Deploy Cloud Cost Agents - Google Compute Engine")
    print("=" * 60)
    print(f"Projeto: {PROJECT_ID}")
    print(f"Zona: {ZONE}")
    print(f"Instância: {INSTANCE_CONFIG['name']}")
    print(f"Tipo: {INSTANCE_CONFIG['machine_type']}")
    print("=" * 60)
    
    deployer = ComputeEngineDeployer(PROJECT_ID, ZONE)
    
    # Verificar pré-requisitos
    if not deployer.check_prerequisites():
        print("\n❌ Pré-requisitos não atendidos. Corrija os problemas e tente novamente.")
        sys.exit(1)
    
    # Configurar firewall
    deployer.configure_firewall()
    
    # Criar instância
    if not deployer.create_instance():
        print("\n❌ Falha ao criar instância.")
        sys.exit(1)
    
    # Aguardar inicialização
    if not deployer.wait_for_startup():
        print("\n⚠️  Inicialização pode não ter concluído. Verifique manualmente.")
    
    # Deploy da aplicação
    if not deployer.deploy_application():
        print("\n❌ Falha no deploy da aplicação.")
        sys.exit(1)
    
    # Imprimir resumo
    deployer.print_summary()
    
    print(f"\n🎉 Deploy concluído com sucesso!")

if __name__ == "__main__":
    main()

