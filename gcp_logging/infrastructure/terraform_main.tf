# Cloud Cost Agent - GCP Infrastructure
# Terraform configuration for logging and analytics infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "cloud-cost-agent-project"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "logging.googleapis.com",
    "bigquery.googleapis.com",
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "monitoring.googleapis.com"
  ])
  
  project = var.project_id
  service = each.value
  
  disable_dependent_services = false
  disable_on_destroy        = false
}

# BigQuery Dataset
resource "google_bigquery_dataset" "agent_analytics" {
  dataset_id  = "agent_analytics"
  project     = var.project_id
  location    = "US"
  
  description = "Dataset for Cloud Cost Agent analytics and logging"
  
  default_table_expiration_ms = 31536000000  # 1 year
  
  labels = {
    environment = var.environment
    component   = "analytics"
    project     = "cloud-cost-agent"
  }
  
  depends_on = [google_project_service.required_apis]
}

# BigQuery Tables
resource "google_bigquery_table" "agent_executions" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "agent_executions"
  project    = var.project_id
  
  description = "Agent execution logs and metrics"
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["agent_type", "status"]
  
  schema = jsonencode([
    {
      name = "execution_id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Unique execution identifier"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Execution timestamp"
    },
    {
      name = "agent_type"
      type = "STRING"
      mode = "REQUIRED"
      description = "Type of agent (aws_specialist, gcp_specialist, etc.)"
    },
    {
      name = "agent_name"
      type = "STRING"
      mode = "REQUIRED"
      description = "Name of the agent function"
    },
    {
      name = "task_type"
      type = "STRING"
      mode = "REQUIRED"
      description = "Type of task executed"
    },
    {
      name = "input_parameters"
      type = "JSON"
      mode = "NULLABLE"
      description = "Input parameters for the execution"
    },
    {
      name = "execution_duration_ms"
      type = "INTEGER"
      mode = "NULLABLE"
      description = "Execution duration in milliseconds"
    },
    {
      name = "status"
      type = "STRING"
      mode = "REQUIRED"
      description = "Execution status (success, error, timeout)"
    },
    {
      name = "error_message"
      type = "STRING"
      mode = "NULLABLE"
      description = "Error message if execution failed"
    },
    {
      name = "memory_usage_mb"
      type = "FLOAT"
      mode = "NULLABLE"
      description = "Memory usage in MB"
    },
    {
      name = "cpu_usage_percent"
      type = "FLOAT"
      mode = "NULLABLE"
      description = "CPU usage percentage"
    },
    {
      name = "session_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "User session identifier"
    },
    {
      name = "user_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "User identifier"
    },
    {
      name = "request_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "Request identifier"
    }
  ])
}

resource "google_bigquery_table" "cost_comparisons" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "cost_comparisons"
  project    = var.project_id
  
  description = "Cost comparison analysis results"
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["analysis_type", "final_recommendation"]
  
  schema = jsonencode([
    {
      name = "comparison_id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Unique comparison identifier"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Analysis timestamp"
    },
    {
      name = "analysis_type"
      type = "STRING"
      mode = "REQUIRED"
      description = "Type of analysis (compute, storage, comprehensive)"
    },
    {
      name = "providers"
      type = "STRING"
      mode = "REPEATED"
      description = "Cloud providers compared"
    },
    {
      name = "input_requirements"
      type = "JSON"
      mode = "NULLABLE"
      description = "Input requirements for the analysis"
    },
    {
      name = "aws_results"
      type = "JSON"
      mode = "NULLABLE"
      description = "AWS analysis results"
    },
    {
      name = "gcp_results"
      type = "JSON"
      mode = "NULLABLE"
      description = "GCP analysis results"
    },
    {
      name = "azure_results"
      type = "JSON"
      mode = "NULLABLE"
      description = "Azure analysis results"
    },
    {
      name = "onpremise_results"
      type = "JSON"
      mode = "NULLABLE"
      description = "On-premise analysis results"
    },
    {
      name = "final_recommendation"
      type = "STRING"
      mode = "REQUIRED"
      description = "Final recommendation (aws, gcp, azure, onpremise)"
    },
    {
      name = "confidence_score"
      type = "FLOAT"
      mode = "NULLABLE"
      description = "Confidence score (0-1)"
    },
    {
      name = "cost_savings_percentage"
      type = "FLOAT"
      mode = "NULLABLE"
      description = "Cost savings percentage"
    },
    {
      name = "cost_savings_amount_usd"
      type = "FLOAT"
      mode = "NULLABLE"
      description = "Cost savings amount in USD"
    },
    {
      name = "reasoning"
      type = "STRING"
      mode = "NULLABLE"
      description = "Reasoning for the recommendation"
    },
    {
      name = "execution_time_ms"
      type = "INTEGER"
      mode = "NULLABLE"
      description = "Total execution time in milliseconds"
    },
    {
      name = "session_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "User session identifier"
    },
    {
      name = "user_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "User identifier"
    }
  ])
}

resource "google_bigquery_table" "agent_interactions" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "agent_interactions"
  project    = var.project_id
  
  description = "Inter-agent communication logs"
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["source_agent", "interaction_type"]
  
  schema = jsonencode([
    {
      name = "interaction_id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Unique interaction identifier"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Interaction timestamp"
    },
    {
      name = "source_agent"
      type = "STRING"
      mode = "REQUIRED"
      description = "Source agent name"
    },
    {
      name = "target_agent"
      type = "STRING"
      mode = "NULLABLE"
      description = "Target agent name"
    },
    {
      name = "interaction_type"
      type = "STRING"
      mode = "REQUIRED"
      description = "Type of interaction (request, response, collaboration)"
    },
    {
      name = "message_content"
      type = "JSON"
      mode = "NULLABLE"
      description = "Message content"
    },
    {
      name = "response_time_ms"
      type = "INTEGER"
      mode = "NULLABLE"
      description = "Response time in milliseconds"
    },
    {
      name = "success"
      type = "BOOLEAN"
      mode = "NULLABLE"
      description = "Whether interaction was successful"
    },
    {
      name = "session_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "Session identifier"
    },
    {
      name = "correlation_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "Correlation identifier for related interactions"
    }
  ])
}

resource "google_bigquery_table" "mcp_server_calls" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "mcp_server_calls"
  project    = var.project_id
  
  description = "MCP server call logs and performance metrics"
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["server_type", "status_code"]
  
  schema = jsonencode([
    {
      name = "call_id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Unique call identifier"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Call timestamp"
    },
    {
      name = "server_type"
      type = "STRING"
      mode = "REQUIRED"
      description = "MCP server type (aws_pricing, gcp_pricing, etc.)"
    },
    {
      name = "method_name"
      type = "STRING"
      mode = "REQUIRED"
      description = "Method name called"
    },
    {
      name = "input_parameters"
      type = "JSON"
      mode = "NULLABLE"
      description = "Input parameters"
    },
    {
      name = "response_data"
      type = "JSON"
      mode = "NULLABLE"
      description = "Response data"
    },
    {
      name = "response_time_ms"
      type = "INTEGER"
      mode = "NULLABLE"
      description = "Response time in milliseconds"
    },
    {
      name = "status_code"
      type = "INTEGER"
      mode = "NULLABLE"
      description = "HTTP status code"
    },
    {
      name = "error_message"
      type = "STRING"
      mode = "NULLABLE"
      description = "Error message if call failed"
    },
    {
      name = "cache_hit"
      type = "BOOLEAN"
      mode = "NULLABLE"
      description = "Whether response came from cache"
    },
    {
      name = "api_cost_usd"
      type = "FLOAT"
      mode = "NULLABLE"
      description = "API call cost in USD"
    },
    {
      name = "agent_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "Agent that made the call"
    },
    {
      name = "session_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "Session identifier"
    }
  ])
}

resource "google_bigquery_table" "user_feedback" {
  dataset_id = google_bigquery_dataset.agent_analytics.dataset_id
  table_id   = "user_feedback"
  project    = var.project_id
  
  description = "User feedback and satisfaction metrics"
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["recommendation_followed", "satisfaction_score"]
  
  schema = jsonencode([
    {
      name = "feedback_id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Unique feedback identifier"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
      description = "Feedback timestamp"
    },
    {
      name = "session_id"
      type = "STRING"
      mode = "REQUIRED"
      description = "Session identifier"
    },
    {
      name = "comparison_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "Related comparison identifier"
    },
    {
      name = "recommendation_followed"
      type = "BOOLEAN"
      mode = "NULLABLE"
      description = "Whether user followed the recommendation"
    },
    {
      name = "actual_savings_usd"
      type = "FLOAT"
      mode = "NULLABLE"
      description = "Actual savings achieved in USD"
    },
    {
      name = "satisfaction_score"
      type = "INTEGER"
      mode = "NULLABLE"
      description = "Satisfaction score (1-5)"
    },
    {
      name = "feedback_text"
      type = "STRING"
      mode = "NULLABLE"
      description = "Free text feedback"
    },
    {
      name = "improvement_suggestions"
      type = "STRING"
      mode = "NULLABLE"
      description = "Improvement suggestions"
    },
    {
      name = "user_id"
      type = "STRING"
      mode = "NULLABLE"
      description = "User identifier"
    }
  ])
}

# Pub/Sub Topic for real-time events
resource "google_pubsub_topic" "agent_events" {
  name    = "agent-analysis-events"
  project = var.project_id
  
  labels = {
    environment = var.environment
    component   = "messaging"
  }
  
  depends_on = [google_project_service.required_apis]
}

# Pub/Sub Subscription for BigQuery streaming
resource "google_pubsub_subscription" "bigquery_streaming" {
  name    = "bigquery-streaming-subscription"
  topic   = google_pubsub_topic.agent_events.name
  project = var.project_id
  
  # BigQuery subscription configuration
  bigquery_config {
    table = "${google_bigquery_table.agent_executions.project}.${google_bigquery_table.agent_executions.dataset_id}.${google_bigquery_table.agent_executions.table_id}"
    use_topic_schema = false
    write_metadata = true
  }
  
  depends_on = [google_bigquery_table.agent_executions]
}

# Cloud Storage bucket for data exports and backups
resource "google_storage_bucket" "analytics_exports" {
  name     = "${var.project_id}-analytics-exports"
  location = var.region
  project  = var.project_id
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  versioning {
    enabled = true
  }
  
  labels = {
    environment = var.environment
    component   = "storage"
  }
}

# Service Account for Cloud Functions
resource "google_service_account" "cloud_functions_sa" {
  account_id   = "cloud-functions-analytics"
  display_name = "Cloud Functions Analytics Service Account"
  project      = var.project_id
  description  = "Service account for analytics cloud functions"
}

# IAM bindings for service account
resource "google_project_iam_member" "cloud_functions_bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

resource "google_project_iam_member" "cloud_functions_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

resource "google_project_iam_member" "cloud_functions_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

# Outputs
output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.agent_analytics.dataset_id
}

output "pubsub_topic_name" {
  description = "Pub/Sub topic name"
  value       = google_pubsub_topic.agent_events.name
}

output "storage_bucket_name" {
  description = "Storage bucket name"
  value       = google_storage_bucket.analytics_exports.name
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.cloud_functions_sa.email
}

