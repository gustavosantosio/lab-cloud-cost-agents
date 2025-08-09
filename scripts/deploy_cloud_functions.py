#!/usr/bin/env python3
"""
Script para deploy dos agentes Cloud Cost Analysis no Google Cloud Functions.

Este script oferece uma alternativa ao Cloud Run, deployando os agentes
como Cloud Functions para casos de uso com menor carga.
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

# Configurações das funções
FUNCTIONS = {
    "operational-manager": {
        "name": "operational-manager",
        "source": "agents/operational",
        "entry_point": "main",
        "runtime": "python311",
        "memory": "1GiB",
        "timeout": "540s",
        "description": "Agente gerente operacional principal"
    },
    "aws-specialist": {
        "name": "aws-specialist",
        "source": "agents/specialists", 
        "entry_point": "aws_main",
        "runtime": "python311",
        "memory": "1GiB",
        "timeout": "300s",
        "description": "Agente especialista em AWS"
    },
    "gcp-specialist": {
        "name": "gcp-specialist",
        "source": "agents/specialists",
        "entry_point": "gcp_main", 
        "runtime": "python311",
        "memory": "1GiB",
        "timeout": "300s",
        "description": "Agente especialista em GCP"
    },
    "sla-coordinator": {
        "name": "sla-coordinator",
        "source": "agents/coordinators",
        "entry_point": "sla_main",
        "runtime": "python311", 
        "memory": "512MiB",
        "timeout": "300s",
        "description": "Agente coordenador de SLA"
    },
    "cost-coordinator": {
        "name": "cost-coordinator",
        "source": "agents/coordinators",
        "entry_point": "cost_main",
        "runtime": "python311",
        "memory": "512MiB",
        "timeout": "300s", 
        "description": "Agente coordenador de custos"
    },
    "compliance-coordinator": {
        "name": "compliance-coordinator",
        "source": "agents/coordinators",
        "entry_point": "compliance_main",
        "runtime": "python311",
        "memory": "512MiB",
        "timeout": "300s",
        "description": "Agente coordenador de compliance"
    },
    "legal-coordinator": {
        "name": "legal-coordinator",
        "source": "agents/coordinators", 
        "entry_point": "legal_main",
        "runtime": "python311",
        "memory": "1GiB",
        "timeout": "540s",
        "description": "Agente coordenador jurídico com RAG"
    },
    "report-generator": {
        "name": "report-generator",
        "source": "agents/coordinators",
        "entry_point": "report_main",
        "runtime": "python311",
        "memory": "1GiB", 
        "timeout": "540s",
        "description": "Agente gerador de relatórios"
    }
}

class CloudFunctionsDeployer:
    def __init__(self, project_id: str, region: str):
        self.project_id = project_id
        self.region = region
        self.deployed_functions = []
        self.failed_functions = []
        
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
            "cloudfunctions.googleapis.com",
            "cloudbuild.googleapis.com"
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
    
    def create_main_py(self, function_name: str, function_config: Dict[str, Any]) -> bool:
        """Cria main.py para a Cloud Function."""
        function_path = Path(function_config["source"])
        main_py_path = function_path / "main.py"
        
        if main_py_path.exists():
            print(f"✅ main.py já existe para {function_name}")
            return True
        
        # Template básico da Cloud Function
        main_content = f'''"""
{function_config["description"]}
Cloud Function para processamento de requisições.
"""

import json
import logging
from typing import Any, Dict
import functions_framework
from flask import Request

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def {function_config["entry_point"]}(request: Request) -> Dict[str, Any]:
    """
    Função principal da Cloud Function.
    
    Args:
        request: Requisição HTTP Flask
        
    Returns:
        Dict com resposta JSON
    """
    try:
        # Log da requisição
        logger.info(f"Requisição recebida: {{request.method}} {{request.path}}")
        
        # Processar diferentes métodos HTTP
        if request.method == "GET":
            return handle_get_request(request)
        elif request.method == "POST":
            return handle_post_request(request)
        else:
            return {{
                "error": "Método não suportado",
                "method": request.method
            }}, 405
            
    except Exception as e:
        logger.error(f"Erro na função: {{str(e)}}")
        return {{
            "error": "Erro interno do servidor",
            "message": str(e)
        }}, 500

def handle_get_request(request: Request) -> Dict[str, Any]:
    """Processa requisições GET."""
    return {{
        "status": "healthy",
        "function": "{function_name}",
        "description": "{function_config["description"]}",
        "method": "GET",
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }}

def handle_post_request(request: Request) -> Dict[str, Any]:
    """Processa requisições POST."""
    try:
        # Obter dados JSON da requisição
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return {{
                "error": "Dados JSON não fornecidos"
            }}, 400
        
        # Processar dados (implementar lógica específica aqui)
        result = process_request_data(request_json)
        
        return {{
            "status": "success",
            "function": "{function_name}",
            "result": result,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }}
        
    except Exception as e:
        logger.error(f"Erro ao processar POST: {{str(e)}}")
        return {{
            "error": "Erro ao processar dados",
            "message": str(e)
        }}, 400

def process_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa dados da requisição.
    
    Args:
        data: Dados JSON da requisição
        
    Returns:
        Dict com resultado do processamento
    """
    # Implementar lógica específica do agente aqui
    logger.info(f"Processando dados: {{data}}")
    
    return {{
        "processed": True,
        "input_data": data,
        "agent_type": "{function_name}",
        "processing_time": "0.1s"
    }}

# Função para compatibilidade com diferentes entry points
{function_config["entry_point"]} = {function_config["entry_point"]}
'''
        
        try:
            with open(main_py_path, "w") as f:
                f.write(main_content)
            print(f"✅ main.py criado para {function_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar main.py para {function_name}: {e}")
            return False
    
    def create_requirements_txt(self, function_name: str, function_config: Dict[str, Any]) -> bool:
        """Cria requirements.txt para a Cloud Function."""
        function_path = Path(function_config["source"])
        req_path = function_path / "requirements.txt"
        
        if req_path.exists():
            print(f"✅ requirements.txt já existe para {function_name}")
            return True
        
        # Requirements para Cloud Functions
        requirements = """functions-framework==3.5.0
google-cloud-logging==3.11.3
google-cloud-monitoring==2.22.2
google-cloud-bigquery==3.25.0
google-cloud-storage==2.18.0
google-cloud-billing==1.13.3
google-cloud-compute==1.19.2
requests==2.32.3
flask==3.0.0
"""
        
        try:
            with open(req_path, "w") as f:
                f.write(requirements)
            print(f"✅ requirements.txt criado para {function_name}")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar requirements.txt para {function_name}: {e}")
            return False
    
    def deploy_function(self, function_name: str, function_config: Dict[str, Any]) -> bool:
        """Faz deploy de uma Cloud Function específica."""
        print(f"\n🚀 Fazendo deploy da função: {function_name}")
        print(f"   Descrição: {function_config['description']}")
        
        function_path = Path(function_config["source"])
        
        # Verificar se diretório existe
        if not function_path.exists():
            print(f"❌ Diretório não encontrado: {function_path}")
            return False
        
        # Criar arquivos necessários
        if not self.create_main_py(function_name, function_config):
            return False
            
        if not self.create_requirements_txt(function_name, function_config):
            return False
        
        # Fazer deploy da Cloud Function
        deploy_command = [
            "gcloud", "functions", "deploy", function_name,
            "--gen2",
            f"--runtime={function_config['runtime']}",
            f"--region={self.region}",
            f"--source=.",
            f"--entry-point={function_config['entry_point']}",
            "--trigger-http",
            "--allow-unauthenticated",
            f"--service-account={SERVICE_ACCOUNT_EMAIL}",
            f"--memory={function_config['memory']}",
            f"--timeout={function_config['timeout']}",
            "--quiet"
        ]
        
        print(f"   Executando deploy...")
        result = self.run_command(deploy_command, cwd=str(function_path))
        
        if result["success"]:
            print(f"✅ Deploy concluído: {function_name}")
            
            # Obter URL da função
            url_command = [
                "gcloud", "functions", "describe", function_name,
                f"--region={self.region}",
                "--gen2",
                "--format=value(serviceConfig.uri)"
            ]
            
            url_result = self.run_command(url_command)
            if url_result["success"]:
                function_url = url_result["stdout"]
                print(f"   URL: {function_url}")
                self.deployed_functions.append({
                    "name": function_name,
                    "url": function_url,
                    "description": function_config["description"]
                })
            
            return True
        else:
            print(f"❌ Erro no deploy de {function_name}: {result['stderr']}")
            self.failed_functions.append(function_name)
            return False
    
    def deploy_all_functions(self) -> bool:
        """Faz deploy de todas as Cloud Functions."""
        print(f"\n🚀 Iniciando deploy de {len(FUNCTIONS)} funções...")
        print("=" * 60)
        
        success_count = 0
        
        for function_name, function_config in FUNCTIONS.items():
            try:
                if self.deploy_function(function_name, function_config):
                    success_count += 1
                
                # Pausa entre deploys
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Erro inesperado no deploy de {function_name}: {e}")
                self.failed_functions.append(function_name)
        
        print(f"\n📊 Resultado do deploy:")
        print(f"✅ Funções deployadas: {success_count}")
        print(f"❌ Funções com falha: {len(self.failed_functions)}")
        
        return len(self.failed_functions) == 0
    
    def create_function_map(self) -> bool:
        """Cria mapa de funções deployadas."""
        if not self.deployed_functions:
            print("⚠️  Nenhuma função deployada para mapear")
            return False
        
        function_map = {
            "project_id": self.project_id,
            "region": self.region,
            "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "functions": self.deployed_functions
        }
        
        try:
            with open("deployed_functions.json", "w") as f:
                json.dump(function_map, f, indent=2)
            
            print(f"✅ Mapa de funções salvo em: deployed_functions.json")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar mapa de funções: {e}")
            return False
    
    def print_summary(self):
        """Imprime resumo do deploy."""
        print("\n" + "=" * 60)
        print("📊 RESUMO DO DEPLOY - CLOUD FUNCTIONS")
        print("=" * 60)
        
        if self.deployed_functions:
            print(f"\n✅ Funções deployadas com sucesso ({len(self.deployed_functions)}):")
            for function in self.deployed_functions:
                print(f"   • {function['name']}: {function['url']}")
                print(f"     {function['description']}")
        
        if self.failed_functions:
            print(f"\n❌ Funções que falharam ({len(self.failed_functions)}):")
            for function in self.failed_functions:
                print(f"   • {function}")
        
        if self.deployed_functions:
            print(f"\n🌐 URLs principais:")
            manager_function = next((f for f in self.deployed_functions if f['name'] == 'operational-manager'), None)
            if manager_function:
                print(f"   Gerente Operacional: {manager_function['url']}")
        
        print(f"\n📝 Próximos passos:")
        if len(self.deployed_functions) == len(FUNCTIONS):
            print("   1. Testar todas as funções deployadas")
            print("   2. Configurar triggers e schedulers")
            print("   3. Configurar monitoramento")
            print("   4. Deploy do frontend separadamente")
        else:
            print("   1. Corrigir problemas nas funções que falharam")
            print("   2. Executar deploy novamente")
            print("   3. Verificar logs de erro")

def main():
    """Função principal."""
    print("🚀 Deploy Cloud Cost Agents - Google Cloud Functions")
    print("=" * 60)
    print(f"Projeto: {PROJECT_ID}")
    print(f"Região: {REGION}")
    print(f"Funções: {len(FUNCTIONS)}")
    print("=" * 60)
    
    deployer = CloudFunctionsDeployer(PROJECT_ID, REGION)
    
    # Verificar pré-requisitos
    if not deployer.check_prerequisites():
        print("\n❌ Pré-requisitos não atendidos. Corrija os problemas e tente novamente.")
        sys.exit(1)
    
    # Fazer deploy de todas as funções
    success = deployer.deploy_all_functions()
    
    # Criar mapa de funções
    deployer.create_function_map()
    
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

