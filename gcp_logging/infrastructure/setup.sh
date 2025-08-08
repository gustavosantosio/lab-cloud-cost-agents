#!/bin/bash

# Cloud Cost Agent - GCP Infrastructure Setup Script
# This script sets up the complete logging and analytics infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-cloud-cost-agent-project}"
REGION="${REGION:-us-central1}"
ENVIRONMENT="${ENVIRONMENT:-prod}"

echo -e "${BLUE}🚀 Cloud Cost Agent - GCP Infrastructure Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Project ID: ${PROJECT_ID}"
echo -e "  Region: ${REGION}"
echo -e "  Environment: ${ENVIRONMENT}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed. Please install it first.${NC}"
    exit 1
fi

# Authenticate with GCP
echo -e "${YELLOW}🔐 Authenticating with GCP...${NC}"
gcloud auth application-default login

# Set the project
echo -e "${YELLOW}📋 Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Create project if it doesn't exist
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo -e "${YELLOW}🆕 Creating GCP project...${NC}"
    gcloud projects create $PROJECT_ID --name="Cloud Cost Agent"
    
    # Enable billing (requires manual setup)
    echo -e "${YELLOW}⚠️  Please enable billing for project $PROJECT_ID manually in the GCP Console${NC}"
    echo -e "${YELLOW}   https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID${NC}"
    read -p "Press Enter after enabling billing..."
fi

# Initialize Terraform
echo -e "${YELLOW}🏗️  Initializing Terraform...${NC}"
cd "$(dirname "$0")"
terraform init

# Plan Terraform deployment
echo -e "${YELLOW}📋 Planning Terraform deployment...${NC}"
terraform plan \
    -var="project_id=$PROJECT_ID" \
    -var="region=$REGION" \
    -var="environment=$ENVIRONMENT" \
    -out=tfplan

# Apply Terraform deployment
echo -e "${YELLOW}🚀 Applying Terraform deployment...${NC}"
terraform apply tfplan

# Get outputs
echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Infrastructure Details:${NC}"
terraform output

# Create service account key for local development
echo -e "${YELLOW}🔑 Creating service account key for local development...${NC}"
SA_EMAIL=$(terraform output -raw service_account_email)
gcloud iam service-accounts keys create ../credentials/service-account-key.json \
    --iam-account=$SA_EMAIL

echo -e "${GREEN}✅ Service account key created: ../credentials/service-account-key.json${NC}"

# Set environment variables
echo -e "${YELLOW}🌍 Setting up environment variables...${NC}"
cat > ../credentials/env_vars.sh << EOF
#!/bin/bash
# Cloud Cost Agent - Environment Variables

export GOOGLE_APPLICATION_CREDENTIALS="\$(dirname "\$0")/service-account-key.json"
export GCP_PROJECT_ID="$PROJECT_ID"
export GCP_REGION="$REGION"
export BIGQUERY_DATASET_ID="$(terraform output -raw bigquery_dataset_id)"
export PUBSUB_TOPIC_NAME="$(terraform output -raw pubsub_topic_name)"
export STORAGE_BUCKET_NAME="$(terraform output -raw storage_bucket_name)"

echo "Environment variables set for Cloud Cost Agent GCP integration"
EOF

chmod +x ../credentials/env_vars.sh

# Create BigQuery views for common queries
echo -e "${YELLOW}📊 Creating BigQuery views...${NC}"
bq query --use_legacy_sql=false << 'EOF'
CREATE OR REPLACE VIEW `cloud_cost_agent.agent_analytics.agent_performance_summary` AS
SELECT 
  agent_type,
  agent_name,
  DATE(timestamp) as date,
  COUNT(*) as total_executions,
  AVG(execution_duration_ms) as avg_duration_ms,
  PERCENTILE_CONT(execution_duration_ms, 0.95) OVER(PARTITION BY agent_type, agent_name, DATE(timestamp)) as p95_duration_ms,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*) * 100 as success_rate,
  COUNT(DISTINCT session_id) as unique_sessions
FROM `cloud_cost_agent.agent_analytics.agent_executions`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY agent_type, agent_name, DATE(timestamp)
ORDER BY date DESC, total_executions DESC;
EOF

bq query --use_legacy_sql=false << 'EOF'
CREATE OR REPLACE VIEW `cloud_cost_agent.agent_analytics.cost_savings_summary` AS
SELECT 
  final_recommendation,
  analysis_type,
  DATE(timestamp) as date,
  COUNT(*) as total_recommendations,
  AVG(confidence_score) as avg_confidence,
  AVG(cost_savings_percentage) as avg_savings_pct,
  SUM(cost_savings_amount_usd) as total_savings_usd,
  AVG(execution_time_ms) as avg_execution_time
FROM `cloud_cost_agent.agent_analytics.cost_comparisons`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY final_recommendation, analysis_type, DATE(timestamp)
ORDER BY date DESC, total_savings_usd DESC;
EOF

bq query --use_legacy_sql=false << 'EOF'
CREATE OR REPLACE VIEW `cloud_cost_agent.agent_analytics.mcp_performance_summary` AS
SELECT 
  server_type,
  method_name,
  DATE(timestamp) as date,
  COUNT(*) as total_calls,
  AVG(response_time_ms) as avg_response_time,
  SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) / COUNT(*) * 100 as success_rate,
  SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) / COUNT(*) * 100 as cache_hit_rate,
  SUM(api_cost_usd) as total_api_cost
FROM `cloud_cost_agent.agent_analytics.mcp_server_calls`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY server_type, method_name, DATE(timestamp)
ORDER BY date DESC, total_calls DESC;
EOF

echo -e "${GREEN}✅ BigQuery views created successfully!${NC}"

# Create monitoring alerts
echo -e "${YELLOW}🚨 Setting up monitoring alerts...${NC}"

# High error rate alert
gcloud alpha monitoring policies create --policy-from-file=- << 'EOF'
{
  "displayName": "Cloud Cost Agent - High Error Rate",
  "conditions": [
    {
      "displayName": "Agent execution error rate > 5%",
      "conditionThreshold": {
        "filter": "resource.type=\"bigquery_table\" AND resource.labels.table_id=\"agent_executions\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.05,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_MEAN",
            "groupByFields": ["resource.labels.table_id"]
          }
        ]
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "enabled": true
}
EOF

# High latency alert
gcloud alpha monitoring policies create --policy-from-file=- << 'EOF'
{
  "displayName": "Cloud Cost Agent - High Latency",
  "conditions": [
    {
      "displayName": "Agent execution time > 30 seconds",
      "conditionThreshold": {
        "filter": "resource.type=\"bigquery_table\" AND resource.labels.table_id=\"agent_executions\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 30000,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_MEAN",
            "crossSeriesReducer": "REDUCE_MEAN",
            "groupByFields": ["resource.labels.table_id"]
          }
        ]
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "enabled": true
}
EOF

echo -e "${GREEN}✅ Monitoring alerts configured!${NC}"

# Create scheduled queries for daily reports
echo -e "${YELLOW}📅 Setting up scheduled queries...${NC}"

# Daily performance report
bq mk --transfer_config \
    --project_id=$PROJECT_ID \
    --data_source=scheduled_query \
    --display_name="Daily Agent Performance Report" \
    --target_dataset=agent_analytics \
    --schedule="0 6 * * *" \
    --params='{
        "query": "SELECT * FROM `cloud_cost_agent.agent_analytics.agent_performance_summary` WHERE date = CURRENT_DATE() - 1",
        "destination_table_name_template": "daily_performance_report_{run_date}",
        "write_disposition": "WRITE_TRUNCATE"
    }'

# Daily cost savings report
bq mk --transfer_config \
    --project_id=$PROJECT_ID \
    --data_source=scheduled_query \
    --display_name="Daily Cost Savings Report" \
    --target_dataset=agent_analytics \
    --schedule="0 6 * * *" \
    --params='{
        "query": "SELECT * FROM `cloud_cost_agent.agent_analytics.cost_savings_summary` WHERE date = CURRENT_DATE() - 1",
        "destination_table_name_template": "daily_savings_report_{run_date}",
        "write_disposition": "WRITE_TRUNCATE"
    }'

echo -e "${GREEN}✅ Scheduled queries configured!${NC}"

# Final instructions
echo ""
echo -e "${GREEN}🎉 GCP Infrastructure Setup Complete!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "1. Source environment variables: ${YELLOW}source ../credentials/env_vars.sh${NC}"
echo -e "2. Install Python dependencies: ${YELLOW}pip install google-cloud-logging google-cloud-bigquery google-cloud-pubsub${NC}"
echo -e "3. Test the logging system: ${YELLOW}python ../collectors/test_logging.py${NC}"
echo -e "4. Access BigQuery console: ${YELLOW}https://console.cloud.google.com/bigquery?project=$PROJECT_ID${NC}"
echo -e "5. View monitoring: ${YELLOW}https://console.cloud.google.com/monitoring?project=$PROJECT_ID${NC}"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo -e "- Keep the service account key secure"
echo -e "- Monitor costs in the GCP Console"
echo -e "- Review and adjust retention policies as needed"
echo ""

