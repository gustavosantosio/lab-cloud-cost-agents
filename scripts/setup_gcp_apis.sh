#!/bin/bash

# Script para configurar APIs do Google Cloud Platform
# para o projeto Cloud Cost Agents

set -e  # Parar em caso de erro

# Configurações
PROJECT_ID="lab-cloud-cost-agents"
SERVICE_ACCOUNT_EMAIL="lab-agents-prod-gcp@lab-cloud-cost-agents.iam.gserviceaccount.com"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se gcloud está instalado
check_gcloud() {
    log_info "Verificando instalação do gcloud..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI não encontrado!"
        log_info "Instale o Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    log_success "gcloud CLI encontrado"
}

# Verificar autenticação
check_auth() {
    log_info "Verificando autenticação..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Nenhuma conta ativa encontrada!"
        log_info "Execute: gcloud auth login"
        exit 1
    fi
    
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    log_success "Autenticado como: $ACTIVE_ACCOUNT"
}

# Configurar projeto
set_project() {
    log_info "Configurando projeto: $PROJECT_ID"
    
    if gcloud config set project $PROJECT_ID; then
        log_success "Projeto configurado: $PROJECT_ID"
    else
        log_error "Falha ao configurar projeto"
        exit 1
    fi
}

# Habilitar APIs
enable_apis() {
    log_info "Habilitando APIs necessárias..."
    
    # Lista de APIs necessárias
    APIS=(
        "cloudbilling.googleapis.com"
        "cloudresourcemanager.googleapis.com"
        "serviceusage.googleapis.com"
        "compute.googleapis.com"
        "storage-api.googleapis.com"
        "storage-component.googleapis.com"
        "bigquery.googleapis.com"
        "bigquerydatatransfer.googleapis.com"
        "bigquerystorage.googleapis.com"
        "cloudfunctions.googleapis.com"
        "run.googleapis.com"
        "cloudbuild.googleapis.com"
        "containerregistry.googleapis.com"
        "monitoring.googleapis.com"
        "logging.googleapis.com"
        "cloudtrace.googleapis.com"
        "iam.googleapis.com"
        "iamcredentials.googleapis.com"
        "cloudkms.googleapis.com"
        "aiplatform.googleapis.com"
        "ml.googleapis.com"
        "dns.googleapis.com"
        "networkmanagement.googleapis.com"
        "sqladmin.googleapis.com"
        "pubsub.googleapis.com"
        "secretmanager.googleapis.com"
        "cloudscheduler.googleapis.com"
    )
    
    ENABLED_COUNT=0
    FAILED_APIS=()
    
    for API in "${APIS[@]}"; do
        log_info "Habilitando: $API"
        
        if gcloud services enable $API --quiet; then
            log_success "API habilitada: $API"
            ((ENABLED_COUNT++))
        else
            log_error "Falha ao habilitar: $API"
            FAILED_APIS+=($API)
        fi
        
        # Pequena pausa para evitar rate limiting
        sleep 1
    done
    
    log_info "Resultado: $ENABLED_COUNT/${#APIS[@]} APIs habilitadas"
    
    if [ ${#FAILED_APIS[@]} -gt 0 ]; then
        log_warning "APIs que falharam:"
        for FAILED_API in "${FAILED_APIS[@]}"; do
            echo "  - $FAILED_API"
        done
    fi
}

# Verificar conta de serviço
check_service_account() {
    log_info "Verificando conta de serviço: $SERVICE_ACCOUNT_EMAIL"
    
    if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --quiet &> /dev/null; then
        log_success "Conta de serviço encontrada"
        return 0
    else
        log_warning "Conta de serviço não encontrada"
        return 1
    fi
}

# Atribuir roles à conta de serviço
assign_roles() {
    log_info "Atribuindo roles à conta de serviço..."
    
    ROLES=(
        "roles/billing.viewer"
        "roles/compute.viewer"
        "roles/storage.objectViewer"
        "roles/bigquery.dataViewer"
        "roles/bigquery.jobUser"
        "roles/monitoring.viewer"
        "roles/logging.viewer"
        "roles/iam.serviceAccountUser"
        "roles/cloudfunctions.developer"
        "roles/run.developer"
        "roles/pubsub.editor"
        "roles/secretmanager.secretAccessor"
        "roles/cloudscheduler.admin"
    )
    
    SUCCESS_COUNT=0
    
    for ROLE in "${ROLES[@]}"; do
        log_info "Atribuindo role: $ROLE"
        
        if gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
            --role="$ROLE" \
            --quiet &> /dev/null; then
            log_success "Role atribuída: $ROLE"
            ((SUCCESS_COUNT++))
        else
            log_warning "Falha ao atribuir role: $ROLE"
        fi
        
        sleep 0.5
    done
    
    log_info "Resultado: $SUCCESS_COUNT/${#ROLES[@]} roles atribuídas"
}

# Criar datasets BigQuery
create_bigquery_datasets() {
    log_info "Criando datasets do BigQuery..."
    
    # Verificar se bq está disponível
    if ! command -v bq &> /dev/null; then
        log_warning "Comando 'bq' não encontrado. Pulando criação de datasets."
        return
    fi
    
    DATASETS=(
        "cloud_cost_agents_raw:Camada RAW - Dados brutos de logs dos agentes"
        "cloud_cost_agents_trusted:Camada TRUSTED - Dados limpos e estruturados"
        "cloud_cost_agents_refined:Camada REFINED - Dados prontos para análise"
    )
    
    for DATASET_INFO in "${DATASETS[@]}"; do
        DATASET_NAME=$(echo $DATASET_INFO | cut -d: -f1)
        DATASET_DESC=$(echo $DATASET_INFO | cut -d: -f2)
        
        log_info "Criando dataset: $DATASET_NAME"
        
        if bq mk --dataset \
            --description="$DATASET_DESC" \
            --location=US \
            $PROJECT_ID:$DATASET_NAME &> /dev/null; then
            log_success "Dataset criado: $DATASET_NAME"
        else
            # Verificar se já existe
            if bq show $PROJECT_ID:$DATASET_NAME &> /dev/null; then
                log_success "Dataset já existe: $DATASET_NAME"
            else
                log_warning "Falha ao criar dataset: $DATASET_NAME"
            fi
        fi
    done
}

# Verificar configuração final
verify_setup() {
    log_info "Verificando configuração final..."
    
    # Verificar projeto ativo
    CURRENT_PROJECT=$(gcloud config get-value project)
    if [ "$CURRENT_PROJECT" = "$PROJECT_ID" ]; then
        log_success "Projeto ativo: $PROJECT_ID"
    else
        log_warning "Projeto ativo diferente: $CURRENT_PROJECT"
    fi
    
    # Verificar algumas APIs críticas
    CRITICAL_APIS=(
        "cloudbilling.googleapis.com"
        "compute.googleapis.com"
        "bigquery.googleapis.com"
        "run.googleapis.com"
    )
    
    ENABLED_CRITICAL=0
    for API in "${CRITICAL_APIS[@]}"; do
        if gcloud services list --enabled --filter="name:$API" --format="value(name)" | grep -q $API; then
            ((ENABLED_CRITICAL++))
        fi
    done
    
    log_info "APIs críticas habilitadas: $ENABLED_CRITICAL/${#CRITICAL_APIS[@]}"
    
    # Verificar conta de serviço
    if check_service_account; then
        log_success "Conta de serviço: OK"
    else
        log_warning "Conta de serviço: Não encontrada"
    fi
}

# Função principal
main() {
    echo "🚀 Configuração de APIs do Google Cloud Platform"
    echo "=================================================="
    echo "Projeto: $PROJECT_ID"
    echo "Conta de serviço: $SERVICE_ACCOUNT_EMAIL"
    echo "=================================================="
    echo
    
    check_gcloud
    check_auth
    set_project
    enable_apis
    
    if check_service_account; then
        assign_roles
    fi
    
    create_bigquery_datasets
    verify_setup
    
    echo
    log_success "Script de configuração concluído!"
    echo
    echo "📝 Próximos passos:"
    echo "   1. Verificar se todas as APIs estão funcionando"
    echo "   2. Testar autenticação da conta de serviço"
    echo "   3. Executar os agentes de teste"
    echo
}

# Executar função principal
main "$@"

