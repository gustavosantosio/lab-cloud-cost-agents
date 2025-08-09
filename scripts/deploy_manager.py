#!/usr/bin/env python3
"""
Gerenciador de Deploy para Cloud Cost Agents.

Este script permite escolher e executar diferentes opções de deploy:
- Cloud Run (recomendado para produção)
- Cloud Functions (para cargas menores)
- Compute Engine (para máximo controle)
"""

import os
import sys
import subprocess
from typing import Dict, List, Any

# Configurações
PROJECT_ID = "lab-cloud-cost-agents"
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

DEPLOY_OPTIONS = {
    "1": {
        "name": "Cloud Run",
        "script": "deploy_cloud_run.py",
        "description": "Deploy em Cloud Run (Recomendado)",
        "pros": [
            "Escalabilidade automática",
            "Pay-per-use",
            "Gerenciamento simplificado",
            "HTTPS automático",
            "Integração nativa com GCP"
        ],
        "cons": [
            "Cold start ocasional",
            "Limitações de CPU/memória",
            "Menos controle sobre infraestrutura"
        ],
        "best_for": "Produção com carga variável"
    },
    "2": {
        "name": "Cloud Functions",
        "script": "deploy_cloud_functions.py", 
        "description": "Deploy em Cloud Functions",
        "pros": [
            "Serverless completo",
            "Custo muito baixo",
            "Escalabilidade automática",
            "Ideal para eventos"
        ],
        "cons": [
            "Cold start mais frequente",
            "Limitações de tempo de execução",
            "Menos adequado para APIs complexas"
        ],
        "best_for": "Cargas leves e processamento por eventos"
    },
    "3": {
        "name": "Compute Engine",
        "script": "deploy_compute_engine.py",
        "description": "Deploy em VM (Máximo controle)",
        "pros": [
            "Controle total da infraestrutura",
            "Performance consistente",
            "Sem cold start",
            "Customização completa"
        ],
        "cons": [
            "Custo fixo",
            "Gerenciamento manual",
            "Responsabilidade por atualizações",
            "Configuração mais complexa"
        ],
        "best_for": "Cargas constantes e alta performance"
    }
}

class DeployManager:
    def __init__(self):
        self.project_id = PROJECT_ID
        self.scripts_dir = SCRIPTS_DIR
        
    def print_header(self):
        """Imprime cabeçalho do gerenciador."""
        print("🚀 Gerenciador de Deploy - Cloud Cost Agents")
        print("=" * 60)
        print(f"Projeto: {self.project_id}")
        print(f"Scripts: {self.scripts_dir}")
        print("=" * 60)
    
    def print_options(self):
        """Imprime opções de deploy disponíveis."""
        print("\n📋 Opções de Deploy Disponíveis:")
        print("-" * 40)
        
        for key, option in DEPLOY_OPTIONS.items():
            print(f"\n{key}. {option['name']}")
            print(f"   {option['description']}")
            print(f"   Melhor para: {option['best_for']}")
            
            print(f"   ✅ Vantagens:")
            for pro in option['pros']:
                print(f"      • {pro}")
                
            print(f"   ⚠️  Desvantagens:")
            for con in option['cons']:
                print(f"      • {con}")
    
    def get_user_choice(self) -> str:
        """Obtém escolha do usuário."""
        print("\n" + "=" * 60)
        
        while True:
            choice = input("Escolha uma opção de deploy (1-3) ou 'q' para sair: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Saindo...")
                sys.exit(0)
            
            if choice in DEPLOY_OPTIONS:
                return choice
            
            print("❌ Opção inválida. Tente novamente.")
    
    def confirm_deploy(self, option: Dict[str, Any]) -> bool:
        """Confirma deploy com o usuário."""
        print(f"\n🎯 Opção selecionada: {option['name']}")
        print(f"📝 Descrição: {option['description']}")
        print(f"📄 Script: {option['script']}")
        
        while True:
            confirm = input("\nConfirma o deploy? (s/n): ").strip().lower()
            
            if confirm in ['s', 'sim', 'y', 'yes']:
                return True
            elif confirm in ['n', 'não', 'nao', 'no']:
                return False
            else:
                print("❌ Resposta inválida. Digite 's' para sim ou 'n' para não.")
    
    def check_prerequisites(self) -> bool:
        """Verifica pré-requisitos gerais."""
        print("\n🔍 Verificando pré-requisitos gerais...")
        
        # Verificar se está no diretório correto
        if not os.path.exists("config/project_config.py"):
            print("❌ Execute este script a partir do diretório raiz do projeto")
            return False
        
        # Verificar se scripts existem
        for option in DEPLOY_OPTIONS.values():
            script_path = os.path.join(self.scripts_dir, option['script'])
            if not os.path.exists(script_path):
                print(f"❌ Script não encontrado: {script_path}")
                return False
        
        print("✅ Pré-requisitos gerais atendidos")
        return True
    
    def run_deploy_script(self, script_name: str) -> bool:
        """Executa script de deploy específico."""
        script_path = os.path.join(self.scripts_dir, script_name)
        
        print(f"\n🚀 Executando: {script_name}")
        print("=" * 60)
        
        try:
            # Executar script
            result = subprocess.run([
                sys.executable, script_path
            ], cwd=os.path.dirname(self.scripts_dir))
            
            if result.returncode == 0:
                print(f"\n✅ Deploy concluído com sucesso!")
                return True
            else:
                print(f"\n❌ Deploy falhou com código: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"\n❌ Erro ao executar script: {e}")
            return False
    
    def print_post_deploy_info(self, option: Dict[str, Any], success: bool):
        """Imprime informações pós-deploy."""
        print("\n" + "=" * 60)
        print("📊 INFORMAÇÕES PÓS-DEPLOY")
        print("=" * 60)
        
        if success:
            print(f"✅ Deploy do {option['name']} concluído com sucesso!")
            
            print(f"\n📝 Próximos passos:")
            if option['name'] == "Cloud Run":
                print("   1. Verificar URLs dos serviços deployados")
                print("   2. Testar endpoints da API")
                print("   3. Configurar domínio customizado (opcional)")
                print("   4. Configurar monitoramento e alertas")
                
            elif option['name'] == "Cloud Functions":
                print("   1. Testar funções deployadas")
                print("   2. Configurar triggers e schedulers")
                print("   3. Deploy separado do frontend")
                print("   4. Configurar monitoramento")
                
            elif option['name'] == "Compute Engine":
                print("   1. Aguardar inicialização completa (5-10 min)")
                print("   2. Testar acesso ao dashboard")
                print("   3. Configurar SSL/HTTPS")
                print("   4. Configurar backup automático")
            
            print(f"\n🔧 Comandos úteis:")
            print("   • Verificar status: python3 scripts/test_gcp_connection.py")
            print("   • Ver logs: gcloud logging read 'resource.type=cloud_run_revision'")
            print("   • Monitorar custos: gcloud billing budgets list")
            
        else:
            print(f"❌ Deploy do {option['name']} falhou!")
            
            print(f"\n🔧 Troubleshooting:")
            print("   1. Verificar autenticação: gcloud auth list")
            print("   2. Verificar projeto: gcloud config get-value project")
            print("   3. Verificar APIs: python3 scripts/setup_gcp_apis.py")
            print("   4. Verificar logs de erro acima")
            print("   5. Tentar novamente após correções")
    
    def run(self):
        """Executa o gerenciador de deploy."""
        self.print_header()
        
        # Verificar pré-requisitos
        if not self.check_prerequisites():
            print("\n❌ Pré-requisitos não atendidos. Corrija os problemas e tente novamente.")
            sys.exit(1)
        
        # Mostrar opções
        self.print_options()
        
        # Obter escolha do usuário
        choice = self.get_user_choice()
        option = DEPLOY_OPTIONS[choice]
        
        # Confirmar deploy
        if not self.confirm_deploy(option):
            print("❌ Deploy cancelado pelo usuário.")
            sys.exit(0)
        
        # Executar deploy
        success = self.run_deploy_script(option['script'])
        
        # Informações pós-deploy
        self.print_post_deploy_info(option, success)
        
        # Código de saída
        sys.exit(0 if success else 1)

def print_usage():
    """Imprime informações de uso."""
    print("""
Uso: python3 scripts/deploy_manager.py

Este script oferece um menu interativo para escolher entre diferentes
opções de deploy para o sistema Cloud Cost Agents:

1. Cloud Run - Recomendado para produção
2. Cloud Functions - Para cargas menores  
3. Compute Engine - Para máximo controle

Pré-requisitos:
- gcloud CLI instalado e autenticado
- Projeto GCP configurado
- APIs necessárias habilitadas
- Conta de serviço configurada

Para configurar pré-requisitos:
python3 scripts/setup_gcp_apis.py
""")

def main():
    """Função principal."""
    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print_usage()
            sys.exit(0)
    
    # Executar gerenciador
    manager = DeployManager()
    manager.run()

if __name__ == "__main__":
    main()

