#!/usr/bin/env python3
"""
Cloud Cost Agent - Teste do Sistema de Logging
Script para testar todas as funcionalidades do sistema de logging
"""

import os
import sys
import time
import random
from datetime import datetime

# Adicionar path do projeto
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from gcp_logging.collectors.gcp_logger import CloudCostLogger, initialize_logger
from gcp_logging.collectors.decorators import (
    log_agent_execution, 
    log_mcp_call, 
    log_cost_comparison_result,
    log_complete_agent
)


def test_basic_logging():
    """Teste básico do sistema de logging"""
    print("🧪 Testando logging básico...")
    
    logger = initialize_logger()
    
    # Teste de execução de agente
    execution_id = logger.log_cost_comparison(
        analysis_type='compute',
        providers=['aws', 'gcp'],
        input_requirements={
            'instance_type': 't3.medium',
            'region': 'us-east-1',
            'workload': 'web_server'
        },
        results_by_provider={
            'aws': {'monthly_cost': 156.80, 'performance_score': 85},
            'gcp': {'monthly_cost': 204.30, 'performance_score': 82}
        },
        recommendation='aws',
        confidence=0.87,
        savings_pct=23.5,
        savings_amount=47.50,
        reasoning='AWS oferece melhor custo-benefício para este workload',
        execution_time=3500,
        session_id='test_session_001',
        user_id='test_user_001'
    )
    
    print(f"✅ Comparação de custos logada: {execution_id}")
    
    # Teste de interação entre agentes
    interaction_id = logger.log_agent_interaction(
        source_agent='cost_coordinator',
        target_agent='aws_specialist',
        interaction_type='request',
        message_content={
            'action': 'analyze_costs',
            'parameters': {'instance_type': 't3.medium', 'region': 'us-east-1'}
        },
        response_time=1200,
        success=True,
        session_id='test_session_001'
    )
    
    print(f"✅ Interação entre agentes logada: {interaction_id}")
    
    # Teste de chamada MCP
    call_id = logger.log_mcp_server_call(
        server_type='aws_pricing',
        method_name='get_ec2_pricing',
        input_params={'instance_type': 't3.medium', 'region': 'us-east-1'},
        response_data={'hourly_cost': 0.0464, 'monthly_cost': 33.79},
        response_time=850,
        status_code=200,
        cache_hit=False,
        api_cost=0.001,
        agent_id='aws_specialist_001',
        session_id='test_session_001'
    )
    
    print(f"✅ Chamada MCP logada: {call_id}")
    
    # Teste de feedback do usuário
    feedback_id = logger.log_user_feedback(
        session_id='test_session_001',
        comparison_id=execution_id,
        recommendation_followed=True,
        actual_savings=45.20,
        satisfaction_score=4,
        feedback_text='Recomendação muito precisa, economizei conforme previsto',
        user_id='test_user_001'
    )
    
    print(f"✅ Feedback do usuário logado: {feedback_id}")
    
    return logger


@log_agent_execution('aws_specialist', 'cost_analysis')
def mock_aws_analysis(instance_type: str, region: str, session_id: str = None):
    """Mock de análise AWS com decorador"""
    print(f"🔍 Analisando AWS: {instance_type} em {region}")
    
    # Simular processamento
    time.sleep(random.uniform(0.5, 2.0))
    
    # Simular resultado
    base_cost = random.uniform(100, 300)
    return {
        'provider': 'aws',
        'instance_type': instance_type,
        'region': region,
        'monthly_cost': base_cost,
        'performance_score': random.randint(80, 95),
        'availability': '99.99%'
    }


@log_mcp_call('gcp_pricing', estimate_cost=True)
def mock_gcp_pricing_call(machine_type: str, region: str, session_id: str = None):
    """Mock de chamada MCP para GCP com decorador"""
    print(f"💰 Consultando preços GCP: {machine_type} em {region}")
    
    # Simular latência de API
    time.sleep(random.uniform(0.3, 1.5))
    
    # Simular resposta da API
    base_cost = random.uniform(120, 350)
    return {
        'machine_type': machine_type,
        'region': region,
        'hourly_cost': base_cost / 730,
        'monthly_cost': base_cost,
        'currency': 'USD'
    }


@log_cost_comparison_result('comprehensive')
def mock_comprehensive_analysis(requirements: dict, session_id: str = None):
    """Mock de análise abrangente com decorador"""
    print("📊 Executando análise abrangente...")
    
    # Simular análise complexa
    time.sleep(random.uniform(2.0, 5.0))
    
    # Simular resultados
    aws_cost = random.uniform(200, 400)
    gcp_cost = random.uniform(220, 450)
    
    recommendation = 'aws' if aws_cost < gcp_cost else 'gcp'
    savings = abs(aws_cost - gcp_cost)
    savings_pct = (savings / max(aws_cost, gcp_cost)) * 100
    
    return {
        'providers': ['aws', 'gcp'],
        'results_by_provider': {
            'aws': {
                'monthly_cost': aws_cost,
                'performance_score': random.randint(80, 95),
                'reliability': '99.99%'
            },
            'gcp': {
                'monthly_cost': gcp_cost,
                'performance_score': random.randint(80, 95),
                'reliability': '99.95%'
            }
        },
        'recommendation': recommendation,
        'confidence': random.uniform(0.75, 0.95),
        'savings_pct': savings_pct,
        'savings_amount': savings,
        'reasoning': f'{recommendation.upper()} oferece melhor custo-benefício com economia de ${savings:.2f}/mês'
    }


@log_complete_agent('azure_specialist', 'cost_analysis', 'azure_pricing')
def mock_azure_complete_analysis(vm_size: str, region: str, session_id: str = None):
    """Mock de análise Azure completa com decorador composto"""
    print(f"🔷 Análise completa Azure: {vm_size} em {region}")
    
    # Simular processamento intensivo
    time.sleep(random.uniform(1.0, 3.0))
    
    # Simular múltiplas operações
    for i in range(3):
        time.sleep(0.2)  # Simular sub-operações
    
    base_cost = random.uniform(180, 380)
    return {
        'provider': 'azure',
        'vm_size': vm_size,
        'region': region,
        'monthly_cost': base_cost,
        'performance_score': random.randint(75, 90),
        'sla': '99.95%',
        'features': ['auto_scaling', 'load_balancer', 'backup']
    }


def test_decorators():
    """Teste dos decoradores de logging"""
    print("\n🎭 Testando decoradores...")
    
    session_id = f"test_session_{int(time.time())}"
    
    # Teste de agente AWS
    aws_result = mock_aws_analysis(
        instance_type='t3.large',
        region='us-west-2',
        session_id=session_id
    )
    print(f"✅ Resultado AWS: ${aws_result['monthly_cost']:.2f}/mês")
    
    # Teste de chamada MCP GCP
    gcp_result = mock_gcp_pricing_call(
        machine_type='e2-standard-4',
        region='us-central1',
        session_id=session_id
    )
    print(f"✅ Preço GCP: ${gcp_result['monthly_cost']:.2f}/mês")
    
    # Teste de análise abrangente
    comprehensive_result = mock_comprehensive_analysis(
        requirements={
            'workload_type': 'web_application',
            'expected_traffic': 'medium',
            'budget_limit': 500
        },
        session_id=session_id
    )
    print(f"✅ Recomendação: {comprehensive_result['recommendation'].upper()} "
          f"(economia de {comprehensive_result['savings_pct']:.1f}%)")
    
    # Teste de agente completo
    azure_result = mock_azure_complete_analysis(
        vm_size='Standard_D4s_v3',
        region='East US',
        session_id=session_id
    )
    print(f"✅ Análise Azure: ${azure_result['monthly_cost']:.2f}/mês "
          f"(score: {azure_result['performance_score']})")


def test_context_manager():
    """Teste do context manager para logging"""
    print("\n🔄 Testando context manager...")
    
    logger = CloudCostLogger()
    session_id = f"test_session_{int(time.time())}"
    
    # Teste de sucesso
    with logger.log_agent_execution_context(
        agent_type='cost_coordinator',
        agent_name='coordinate_analysis',
        task_type='orchestration',
        session_id=session_id,
        workload_type='enterprise',
        budget_limit=1000
    ) as ctx:
        print("🎯 Executando coordenação de análise...")
        time.sleep(1.5)
        
        result = {
            'total_providers_analyzed': 3,
            'best_recommendation': 'aws',
            'total_savings': 250.75
        }
        ctx.set_result(result)
        print(f"✅ Coordenação concluída: economia de ${result['total_savings']}")
    
    # Teste de erro
    try:
        with logger.log_agent_execution_context(
            agent_type='error_agent',
            agent_name='failing_function',
            task_type='error_test',
            session_id=session_id
        ) as ctx:
            print("💥 Simulando erro...")
            time.sleep(0.5)
            raise ValueError("Erro simulado para teste")
    except ValueError as e:
        print(f"✅ Erro capturado e logado: {e}")


def test_performance_load():
    """Teste de carga para verificar performance"""
    print("\n⚡ Testando performance com carga...")
    
    logger = CloudCostLogger()
    start_time = time.time()
    
    # Simular múltiplas análises simultâneas
    for i in range(50):
        session_id = f"load_test_session_{i}"
        
        # Log de execução
        with logger.log_agent_execution_context(
            agent_type=random.choice(['aws_specialist', 'gcp_specialist', 'azure_specialist']),
            agent_name=f'analysis_{i}',
            task_type='load_test',
            session_id=session_id
        ):
            time.sleep(random.uniform(0.01, 0.1))  # Simular processamento rápido
        
        # Log de comparação
        if i % 5 == 0:  # A cada 5 execuções
            logger.log_cost_comparison(
                analysis_type='compute',
                providers=['aws', 'gcp'],
                input_requirements={'test_id': i},
                results_by_provider={
                    'aws': {'cost': random.uniform(100, 300)},
                    'gcp': {'cost': random.uniform(120, 320)}
                },
                recommendation=random.choice(['aws', 'gcp']),
                confidence=random.uniform(0.7, 0.95),
                savings_pct=random.uniform(5, 30),
                savings_amount=random.uniform(20, 100),
                reasoning=f'Análise de carga #{i}',
                execution_time=random.randint(1000, 5000),
                session_id=session_id
            )
    
    # Forçar flush
    logger.flush()
    
    total_time = time.time() - start_time
    print(f"✅ Teste de carga concluído: 50 execuções em {total_time:.2f}s")
    print(f"📊 Métricas do logger: {logger.get_metrics()}")


def test_error_handling():
    """Teste de tratamento de erros"""
    print("\n🚨 Testando tratamento de erros...")
    
    # Teste com projeto inválido
    try:
        invalid_logger = CloudCostLogger(project_id="projeto-inexistente-12345")
        print("❌ Deveria ter falhado com projeto inválido")
    except Exception as e:
        print(f"✅ Erro esperado capturado: {type(e).__name__}")
    
    # Teste com dados inválidos
    logger = CloudCostLogger()
    
    try:
        # Tentar log com dados não serializáveis
        class NonSerializable:
            pass
        
        logger.log_cost_comparison(
            analysis_type='test',
            providers=['aws'],
            input_requirements={'invalid': NonSerializable()},
            results_by_provider={},
            recommendation='aws',
            confidence=0.5,
            savings_pct=0,
            savings_amount=0,
            reasoning='teste',
            execution_time=1000
        )
        print("✅ Dados não serializáveis tratados corretamente")
    except Exception as e:
        print(f"⚠️ Erro inesperado: {e}")


def main():
    """Função principal de teste"""
    print("🚀 Cloud Cost Agent - Teste do Sistema de Logging")
    print("=" * 60)
    
    # Verificar variáveis de ambiente
    required_vars = ['GCP_PROJECT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {missing_vars}")
        print("💡 Execute: source ../credentials/env_vars.sh")
        return 1
    
    try:
        # Executar testes
        logger = test_basic_logging()
        test_decorators()
        test_context_manager()
        test_performance_load()
        test_error_handling()
        
        # Flush final
        logger.flush()
        
        print("\n🎉 Todos os testes concluídos com sucesso!")
        print(f"📊 Métricas finais: {logger.get_metrics()}")
        
        # Instruções para visualização
        project_id = os.getenv('GCP_PROJECT_ID')
        print(f"\n📈 Para visualizar os logs:")
        print(f"🔗 Cloud Logging: https://console.cloud.google.com/logs/query?project={project_id}")
        print(f"🔗 BigQuery: https://console.cloud.google.com/bigquery?project={project_id}")
        print(f"🔗 Pub/Sub: https://console.cloud.google.com/cloudpubsub?project={project_id}")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

