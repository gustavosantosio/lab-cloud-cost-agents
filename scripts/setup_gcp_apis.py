#!/usr/bin/env python3
"""
Script para configurar e ativar APIs necessárias do Google Cloud Platform
para o projeto Cloud Cost Agents.

Este script automatiza a habilitação de todas as APIs necessárias para o funcionamento
dos agentes de análise de custos cloud.
"""

import subprocess
import sys
import json
import time
from typing import List, Dict, Any

# Configurações do projeto
PROJECT_ID = "lab-cloud-cost-agents"
SERVICE_ACCOUNT_EMAIL = "lab-agents-prod-gcp@lab-cloud-cost-agents.iam.gserviceaccount.com"

# APIs necessárias para o projeto
REQUIRED_APIS = [
    # APIs de Billing e Custos
    "cloudbilling.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    
    # APIs de Compute e Storage
    "compute.googleapis.com",
    "storage-api.googleapis.com",
    "storage-component.googleapis.com",
    
    # APIs de BigQuery para Data Lake
    "bigquery.googleapis.com",
    "bigquerydatatransfer.googleapis.com",
    "bigquerystorage.googleapis.com",
    
    # APIs de Cloud Functions/Run para deploy dos agentes
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    
    # APIs de Monitoring e Logging
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    
    # APIs de IAM e Security
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudkms.googleapis.com",
    
    # APIs de AI/ML para agentes
    "aiplatform.googleapis.com",
    "ml.googleapis.com",
    
    # APIs de Networking
    "dns.googleapis.com",
    "networkmanagement.googleapis.com",
    
    # APIs de Cloud SQL (se necessário)
    "sqladmin.googleapis.com",
    
    # APIs de Pub/Sub para comunicação entre agentes
    "pubsub.googleapis.com",
    
    # APIs de Secret Manager
    "secretmanager.googleapis.com",
    
    # APIs de Cloud Scheduler
    "cloudscheduler.googleapis.com"
]

# Permissões necessárias para a conta de serviço
REQUIRED_ROLES = [
    "roles/billing.viewer",
    "roles/compute.viewer",
    "roles/storage.objectViewer",
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/monitoring.viewer",
    "roles/logging.viewer",
    "roles/iam.serviceAccountUser",
    "roles/cloudfunctions.developer",
    "roles/run.developer",
    "roles/pubsub.editor",
    "roles/secretmanager.secretAccessor",
    "roles/cloudscheduler.admin"
]

class GCPSetup:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.enabled_apis = []
        self.failed_apis = []
        
    def run_gcloud_command(self, command: List[str]) -> Dict[str, Any]:
        """Executa comando gcloud e retorna resultado."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
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
    
    def check_gcloud_auth(self) -> bool:
        """Verifica se o gcloud está autenticado."""
        print("🔐 Verificando autenticação do gcloud...")
        
        result = self.run_gcloud_command(["gcloud", "auth", "list", "--format=json"])
        if not result["success"]:
            print("❌ Erro ao verificar autenticação")
            return False
            
        try:
            auth_accounts = json.loads(result["stdout"])
            if not auth_accounts:
                print("❌ Nenhuma conta autenticada encontrada")
                print("Execute: gcloud auth login")
                return False
                
            active_account = next((acc for acc in auth_accounts if acc.get("status") == "ACTIVE"), None)
            if not active_account:
                print("❌ Nenhuma conta ativa encontrada")
                return False
                
            print(f"✅ Autenticado como: {active_account['account']}")
            return True
            
        except json.JSONDecodeError:
            print("❌ Erro ao processar informações de autenticação")
            return False
    
    def set_project(self) -> bool:
        """Define o projeto ativo."""
        print(f"🎯 Configurando projeto: {self.project_id}")
        
        result = self.run_gcloud_command([
            "gcloud", "config", "set", "project", self.project_id
        ])
        
        if result["success"]:
            print(f"✅ Projeto configurado: {self.project_id}")
            return True
        else:
            print(f"❌ Erro ao configurar projeto: {result['stderr']}")
            return False
    
    def check_api_status(self, api_name: str) -> bool:
        """Verifica se uma API está habilitada."""
        result = self.run_gcloud_command([
            "gcloud", "services", "list", 
            "--enabled", 
            f"--filter=name:{api_name}",
            "--format=value(name)"
        ])
        
        return result["success"] and api_name in result["stdout"]
    
    def enable_api(self, api_name: str) -> bool:
        """Habilita uma API específica."""
        print(f"🔧 Habilitando API: {api_name}")
        
        # Verifica se já está habilitada
        if self.check_api_status(api_name):
            print(f"✅ API já habilitada: {api_name}")
            self.enabled_apis.append(api_name)
            return True
        
        # Habilita a API
        result = self.run_gcloud_command([
            "gcloud", "services", "enable", api_name
        ])
        
        if result["success"]:
            print(f"✅ API habilitada com sucesso: {api_name}")
            self.enabled_apis.append(api_name)
            return True
        else:
            print(f"❌ Erro ao habilitar API {api_name}: {result['stderr']}")
            self.failed_apis.append(api_name)
            return False
    
    def enable_all_apis(self) -> bool:
        """Habilita todas as APIs necessárias."""
        print(f"\n🚀 Habilitando {len(REQUIRED_APIS)} APIs necessárias...")
        print("=" * 60)
        
        success_count = 0
        for i, api in enumerate(REQUIRED_APIS, 1):
            print(f"\n[{i}/{len(REQUIRED_APIS)}] Processando: {api}")
            
            if self.enable_api(api):
                success_count += 1
            
            # Pequena pausa para evitar rate limiting
            time.sleep(1)
        
        print(f"\n📊 Resultado:")
        print(f"✅ APIs habilitadas com sucesso: {success_count}")
        print(f"❌ APIs com falha: {len(self.failed_apis)}")
        
        if self.failed_apis:
            print(f"\n⚠️  APIs que falharam:")
            for api in self.failed_apis:
                print(f"   - {api}")
        
        return len(self.failed_apis) == 0
    
    def check_service_account(self) -> bool:
        """Verifica se a conta de serviço existe."""
        print(f"\n👤 Verificando conta de serviço: {SERVICE_ACCOUNT_EMAIL}")
        
        result = self.run_gcloud_command([
            "gcloud", "iam", "service-accounts", "describe", 
            SERVICE_ACCOUNT_EMAIL,
            "--format=json"
        ])
        
        if result["success"]:
            try:
                sa_info = json.loads(result["stdout"])
                print(f"✅ Conta de serviço encontrada: {sa_info.get('displayName', 'N/A')}")
                print(f"   Email: {sa_info.get('email')}")
                print(f"   Status: {sa_info.get('disabled', False) and 'Desabilitada' or 'Ativa'}")
                return True
            except json.JSONDecodeError:
                print("❌ Erro ao processar informações da conta de serviço")
                return False
        else:
            print(f"❌ Conta de serviço não encontrada: {result['stderr']}")
            return False
    
    def assign_roles_to_service_account(self) -> bool:
        """Atribui roles necessárias à conta de serviço."""
        print(f"\n🔑 Atribuindo roles à conta de serviço...")
        
        success_count = 0
        failed_roles = []
        
        for role in REQUIRED_ROLES:
            print(f"   Atribuindo role: {role}")
            
            result = self.run_gcloud_command([
                "gcloud", "projects", "add-iam-policy-binding", self.project_id,
                f"--member=serviceAccount:{SERVICE_ACCOUNT_EMAIL}",
                f"--role={role}"
            ])
            
            if result["success"]:
                success_count += 1
                print(f"   ✅ Role atribuída: {role}")
            else:
                failed_roles.append(role)
                print(f"   ❌ Falha ao atribuir role {role}: {result['stderr']}")
            
            time.sleep(0.5)  # Evitar rate limiting
        
        print(f"\n📊 Resultado das roles:")
        print(f"✅ Roles atribuídas: {success_count}")
        print(f"❌ Roles com falha: {len(failed_roles)}")
        
        return len(failed_roles) == 0
    
    def create_bigquery_datasets(self) -> bool:
        """Cria datasets do BigQuery para o Data Lake."""
        print(f"\n📊 Criando datasets do BigQuery...")
        
        datasets = [
            {
                "name": "cloud_cost_agents_raw",
                "description": "Camada RAW - Dados brutos de logs dos agentes",
                "location": "US"
            },
            {
                "name": "cloud_cost_agents_trusted", 
                "description": "Camada TRUSTED - Dados limpos e estruturados",
                "location": "US"
            },
            {
                "name": "cloud_cost_agents_refined",
                "description": "Camada REFINED - Dados prontos para análise",
                "location": "US"
            }
        ]
        
        success_count = 0
        for dataset in datasets:
            print(f"   Criando dataset: {dataset['name']}")
            
            result = self.run_gcloud_command([
                "bq", "mk", 
                "--dataset",
                f"--description={dataset['description']}",
                f"--location={dataset['location']}",
                f"{self.project_id}:{dataset['name']}"
            ])
            
            if result["success"] or "already exists" in result["stderr"].lower():
                success_count += 1
                print(f"   ✅ Dataset criado/existe: {dataset['name']}")
            else:
                print(f"   ❌ Erro ao criar dataset {dataset['name']}: {result['stderr']}")
        
        return success_count == len(datasets)
    
    def verify_setup(self) -> bool:
        """Verifica se toda a configuração está correta."""
        print(f"\n🔍 Verificando configuração final...")
        
        # Verificar APIs habilitadas
        enabled_count = 0
        for api in REQUIRED_APIS:
            if self.check_api_status(api):
                enabled_count += 1
        
        print(f"   APIs habilitadas: {enabled_count}/{len(REQUIRED_APIS)}")
        
        # Verificar conta de serviço
        sa_exists = self.check_service_account()
        
        # Verificar datasets BigQuery
        result = self.run_gcloud_command([
            "bq", "ls", "-d", self.project_id
        ])
        
        datasets_exist = result["success"] and "cloud_cost_agents" in result["stdout"]
        print(f"   Datasets BigQuery: {'✅' if datasets_exist else '❌'}")
        
        all_good = (enabled_count == len(REQUIRED_APIS)) and sa_exists and datasets_exist
        
        if all_good:
            print(f"\n🎉 Configuração concluída com sucesso!")
            print(f"   Projeto: {self.project_id}")
            print(f"   APIs habilitadas: {enabled_count}")
            print(f"   Conta de serviço: ✅")
            print(f"   Datasets BigQuery: ✅")
        else:
            print(f"\n⚠️  Configuração incompleta. Verifique os erros acima.")
        
        return all_good

def main():
    """Função principal."""
    print("🚀 Configuração de APIs do Google Cloud Platform")
    print("=" * 60)
    print(f"Projeto: {PROJECT_ID}")
    print(f"Conta de serviço: {SERVICE_ACCOUNT_EMAIL}")
    print("=" * 60)
    
    setup = GCPSetup(PROJECT_ID)
    
    # Verificar autenticação
    if not setup.check_gcloud_auth():
        print("\n❌ Falha na autenticação. Execute 'gcloud auth login' primeiro.")
        sys.exit(1)
    
    # Configurar projeto
    if not setup.set_project():
        print("\n❌ Falha ao configurar projeto.")
        sys.exit(1)
    
    # Habilitar APIs
    if not setup.enable_all_apis():
        print("\n⚠️  Algumas APIs falharam. Continuando...")
    
    # Verificar conta de serviço
    if not setup.check_service_account():
        print("\n⚠️  Conta de serviço não encontrada. Verifique se existe.")
    else:
        # Atribuir roles
        setup.assign_roles_to_service_account()
    
    # Criar datasets BigQuery
    setup.create_bigquery_datasets()
    
    # Verificação final
    setup.verify_setup()
    
    print(f"\n✅ Script de configuração concluído!")
    print(f"📝 Próximos passos:")
    print(f"   1. Verificar se todas as APIs estão funcionando")
    print(f"   2. Testar autenticação da conta de serviço")
    print(f"   3. Executar os agentes de teste")

if __name__ == "__main__":
    main()

