#!/usr/bin/env python3
"""
Script para testar conexões e funcionalidades do Google Cloud Platform
após a configuração das APIs.

Este script verifica se todas as integrações estão funcionando corretamente.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

try:
    from google.cloud import billing_v1
    from google.cloud import compute_v1
    from google.cloud import storage
    from google.cloud import bigquery
    from google.cloud import monitoring_v3
    from google.cloud import logging
    from google.oauth2 import service_account
    import google.auth
except ImportError as e:
    print(f"❌ Erro ao importar bibliotecas do Google Cloud: {e}")
    print("Execute: pip install google-cloud-billing google-cloud-compute google-cloud-storage google-cloud-bigquery google-cloud-monitoring google-cloud-logging")
    sys.exit(1)

# Configurações
PROJECT_ID = "lab-cloud-cost-agents"
SERVICE_ACCOUNT_EMAIL = "lab-agents-prod-gcp@lab-cloud-cost-agents.iam.gserviceaccount.com"
BUCKET_NAME = "lab-rag-files-bucket"

class GCPConnectionTester:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.credentials = None
        self.test_results = {}
        
    def setup_credentials(self) -> bool:
        """Configura credenciais do GCP."""
        print("🔐 Configurando credenciais...")
        
        try:
            # Tentar usar credenciais padrão
            credentials, project = google.auth.default()
            self.credentials = credentials
            
            if project != self.project_id:
                print(f"⚠️  Projeto das credenciais ({project}) diferente do esperado ({self.project_id})")
            
            print(f"✅ Credenciais configuradas para projeto: {project}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao configurar credenciais: {e}")
            print("Verifique se GOOGLE_APPLICATION_CREDENTIALS está configurado ou execute 'gcloud auth application-default login'")
            return False
    
    def test_billing_api(self) -> bool:
        """Testa API de Billing."""
        print("\n💰 Testando API de Billing...")
        
        try:
            client = billing_v1.CloudBillingClient(credentials=self.credentials)
            
            # Listar contas de billing
            request = billing_v1.ListBillingAccountsRequest()
            response = client.list_billing_accounts(request=request)
            
            billing_accounts = list(response)
            print(f"✅ API de Billing funcionando. Contas encontradas: {len(billing_accounts)}")
            
            for account in billing_accounts[:3]:  # Mostrar apenas as primeiras 3
                print(f"   - {account.display_name} ({account.name})")
            
            self.test_results['billing'] = True
            return True
            
        except Exception as e:
            print(f"❌ Erro na API de Billing: {e}")
            self.test_results['billing'] = False
            return False
    
    def test_compute_api(self) -> bool:
        """Testa API de Compute Engine."""
        print("\n🖥️  Testando API de Compute Engine...")
        
        try:
            client = compute_v1.InstancesClient(credentials=self.credentials)
            
            # Listar instâncias em algumas zonas
            zones = ['us-central1-a', 'us-east1-b', 'europe-west1-b']
            total_instances = 0
            
            for zone in zones:
                try:
                    request = compute_v1.ListInstancesRequest(
                        project=self.project_id,
                        zone=zone
                    )
                    response = client.list(request=request)
                    instances = list(response)
                    total_instances += len(instances)
                    
                    if instances:
                        print(f"   Zona {zone}: {len(instances)} instâncias")
                        
                except Exception as zone_error:
                    # Zona pode não existir ou não ter permissão
                    continue
            
            print(f"✅ API de Compute funcionando. Total de instâncias: {total_instances}")
            self.test_results['compute'] = True
            return True
            
        except Exception as e:
            print(f"❌ Erro na API de Compute: {e}")
            self.test_results['compute'] = False
            return False
    
    def test_storage_api(self) -> bool:
        """Testa API de Cloud Storage."""
        print("\n🗄️  Testando API de Cloud Storage...")
        
        try:
            client = storage.Client(project=self.project_id, credentials=self.credentials)
            
            # Listar buckets
            buckets = list(client.list_buckets())
            print(f"✅ API de Storage funcionando. Buckets encontrados: {len(buckets)}")
            
            # Verificar bucket específico do RAG
            try:
                bucket = client.bucket(BUCKET_NAME)
                if bucket.exists():
                    print(f"✅ Bucket RAG encontrado: {BUCKET_NAME}")
                    
                    # Listar alguns arquivos
                    blobs = list(bucket.list_blobs(max_results=5))
                    print(f"   Arquivos no bucket: {len(blobs)}")
                    for blob in blobs:
                        print(f"   - {blob.name} ({blob.size} bytes)")
                else:
                    print(f"⚠️  Bucket RAG não encontrado: {BUCKET_NAME}")
                    
            except Exception as bucket_error:
                print(f"⚠️  Erro ao acessar bucket RAG: {bucket_error}")
            
            self.test_results['storage'] = True
            return True
            
        except Exception as e:
            print(f"❌ Erro na API de Storage: {e}")
            self.test_results['storage'] = False
            return False
    
    def test_bigquery_api(self) -> bool:
        """Testa API do BigQuery."""
        print("\n📊 Testando API do BigQuery...")
        
        try:
            client = bigquery.Client(project=self.project_id, credentials=self.credentials)
            
            # Listar datasets
            datasets = list(client.list_datasets())
            print(f"✅ API do BigQuery funcionando. Datasets encontrados: {len(datasets)}")
            
            # Verificar datasets específicos do projeto
            expected_datasets = [
                'cloud_cost_agents_raw',
                'cloud_cost_agents_trusted', 
                'cloud_cost_agents_refined'
            ]
            
            found_datasets = [ds.dataset_id for ds in datasets]
            
            for expected in expected_datasets:
                if expected in found_datasets:
                    print(f"✅ Dataset encontrado: {expected}")
                    
                    # Tentar listar tabelas
                    try:
                        dataset = client.dataset(expected)
                        tables = list(client.list_tables(dataset))
                        print(f"   Tabelas no dataset: {len(tables)}")
                    except Exception:
                        print(f"   Dataset vazio ou sem permissão")
                else:
                    print(f"⚠️  Dataset não encontrado: {expected}")
            
            # Teste simples de query
            try:
                query = "SELECT 1 as test_value"
                query_job = client.query(query)
                results = query_job.result()
                print(f"✅ Teste de query executado com sucesso")
            except Exception as query_error:
                print(f"⚠️  Erro no teste de query: {query_error}")
            
            self.test_results['bigquery'] = True
            return True
            
        except Exception as e:
            print(f"❌ Erro na API do BigQuery: {e}")
            self.test_results['bigquery'] = False
            return False
    
    def test_monitoring_api(self) -> bool:
        """Testa API de Monitoring."""
        print("\n📈 Testando API de Monitoring...")
        
        try:
            client = monitoring_v3.MetricServiceClient(credentials=self.credentials)
            
            # Listar métricas disponíveis (limitado)
            project_name = f"projects/{self.project_id}"
            request = monitoring_v3.ListMetricDescriptorsRequest(
                name=project_name,
                page_size=5
            )
            
            response = client.list_metric_descriptors(request=request)
            metrics = list(response)
            
            print(f"✅ API de Monitoring funcionando. Métricas disponíveis: {len(metrics)}")
            
            for metric in metrics[:3]:
                print(f"   - {metric.type}")
            
            self.test_results['monitoring'] = True
            return True
            
        except Exception as e:
            print(f"❌ Erro na API de Monitoring: {e}")
            self.test_results['monitoring'] = False
            return False
    
    def test_logging_api(self) -> bool:
        """Testa API de Logging."""
        print("\n📝 Testando API de Logging...")
        
        try:
            client = logging.Client(project=self.project_id, credentials=self.credentials)
            
            # Listar logs recentes
            filter_str = 'timestamp >= "2024-01-01T00:00:00Z"'
            entries = client.list_entries(filter_=filter_str, max_results=5)
            
            entry_count = 0
            for entry in entries:
                entry_count += 1
                if entry_count <= 3:
                    print(f"   Log: {entry.log_name} - {entry.timestamp}")
            
            print(f"✅ API de Logging funcionando. Entradas encontradas: {entry_count}")
            
            self.test_results['logging'] = True
            return True
            
        except Exception as e:
            print(f"❌ Erro na API de Logging: {e}")
            self.test_results['logging'] = False
            return False
    
    def test_service_account_permissions(self) -> bool:
        """Testa permissões da conta de serviço."""
        print(f"\n👤 Testando permissões da conta de serviço...")
        
        try:
            # Usar Resource Manager para testar permissões básicas
            from google.cloud import resourcemanager
            
            client = resourcemanager.ProjectsClient(credentials=self.credentials)
            
            # Tentar obter informações do projeto
            request = resourcemanager.GetProjectRequest(name=f"projects/{self.project_id}")
            project = client.get_project(request=request)
            
            print(f"✅ Acesso ao projeto confirmado: {project.display_name}")
            print(f"   ID: {project.project_id}")
            print(f"   Estado: {project.state.name}")
            
            self.test_results['permissions'] = True
            return True
            
        except Exception as e:
            print(f"❌ Erro ao testar permissões: {e}")
            self.test_results['permissions'] = False
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Executa todos os testes."""
        print("🧪 Iniciando testes de conexão GCP")
        print("=" * 50)
        
        if not self.setup_credentials():
            return self.test_results
        
        # Executar todos os testes
        tests = [
            self.test_service_account_permissions,
            self.test_billing_api,
            self.test_compute_api,
            self.test_storage_api,
            self.test_bigquery_api,
            self.test_monitoring_api,
            self.test_logging_api
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Erro inesperado no teste {test.__name__}: {e}")
                self.test_results[test.__name__] = False
        
        return self.test_results
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS TESTES")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"Total de testes: {total_tests}")
        print(f"Testes aprovados: {passed_tests}")
        print(f"Testes falharam: {total_tests - passed_tests}")
        print(f"Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetalhes:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"  {test_name}: {status}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 Todos os testes passaram! O sistema está pronto para uso.")
        else:
            print(f"\n⚠️  Alguns testes falharam. Verifique as configurações e permissões.")
        
        print("\n📝 Próximos passos:")
        if passed_tests == total_tests:
            print("  1. Executar os agentes de teste")
            print("  2. Configurar monitoramento")
            print("  3. Fazer deploy dos agentes")
        else:
            print("  1. Corrigir problemas identificados")
            print("  2. Executar novamente os testes")
            print("  3. Verificar permissões da conta de serviço")

def main():
    """Função principal."""
    print(f"🔍 Teste de Conexões GCP")
    print(f"Projeto: {PROJECT_ID}")
    print(f"Conta de serviço: {SERVICE_ACCOUNT_EMAIL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tester = GCPConnectionTester(PROJECT_ID)
    results = tester.run_all_tests()
    tester.print_summary()
    
    # Retornar código de saída baseado nos resultados
    if all(results.values()):
        sys.exit(0)  # Sucesso
    else:
        sys.exit(1)  # Falha

if __name__ == "__main__":
    main()

