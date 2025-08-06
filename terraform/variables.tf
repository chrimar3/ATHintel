# ATHintel Enterprise Platform - Terraform Variables
# Configuration variables for cloud infrastructure deployment

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-central-1"
  
  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "athintel.com"
}

# ============================================================================
# VPC Configuration
# ============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  
  validation {
    condition     = length(var.private_subnets) >= 2
    error_message = "At least 2 private subnets are required for high availability."
  }
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  validation {
    condition     = length(var.public_subnets) >= 2
    error_message = "At least 2 public subnets are required for high availability."
  }
}

# ============================================================================
# EKS Configuration
# ============================================================================

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
  
  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+$", var.kubernetes_version))
    error_message = "Kubernetes version must be in format X.Y (e.g., 1.28)."
  }
}

variable "node_instance_types" {
  description = "Instance types for EKS node groups"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
  
  validation {
    condition     = length(var.node_instance_types) > 0
    error_message = "At least one instance type must be specified."
  }
}

variable "node_group_min_size" {
  description = "Minimum number of nodes in the node group"
  type        = number
  default     = 2
  
  validation {
    condition     = var.node_group_min_size >= 1
    error_message = "Node group minimum size must be at least 1."
  }
}

variable "node_group_max_size" {
  description = "Maximum number of nodes in the node group"
  type        = number
  default     = 20
  
  validation {
    condition     = var.node_group_max_size >= var.node_group_min_size
    error_message = "Node group maximum size must be greater than or equal to minimum size."
  }
}

variable "node_group_desired_size" {
  description = "Desired number of nodes in the node group"
  type        = number
  default     = 3
  
  validation {
    condition = var.node_group_desired_size >= var.node_group_min_size && var.node_group_desired_size <= var.node_group_max_size
    error_message = "Node group desired size must be between min and max size."
  }
}

variable "enable_fargate" {
  description = "Enable Fargate profiles for serverless workloads"
  type        = bool
  default     = false
}

# ============================================================================
# Database Configuration
# ============================================================================

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
  
  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "Database instance class must start with 'db.'."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance (GB)"
  type        = number
  default     = 20
  
  validation {
    condition     = var.db_allocated_storage >= 20
    error_message = "Allocated storage must be at least 20 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance (GB)"
  type        = number
  default     = 100
  
  validation {
    condition     = var.db_max_allocated_storage >= var.db_allocated_storage
    error_message = "Maximum allocated storage must be greater than or equal to allocated storage."
  }
}

# ============================================================================
# Redis Configuration
# ============================================================================

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
  
  validation {
    condition     = can(regex("^cache\\.", var.redis_node_type))
    error_message = "Redis node type must start with 'cache.'."
  }
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in the Redis cluster"
  type        = number
  default     = 1
  
  validation {
    condition     = var.redis_num_cache_nodes >= 1 && var.redis_num_cache_nodes <= 6
    error_message = "Number of cache nodes must be between 1 and 6."
  }
}

# ============================================================================
# Monitoring Configuration
# ============================================================================

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring stack (Prometheus, Grafana)"
  type        = bool
  default     = true
}

variable "monitoring_retention_days" {
  description = "Number of days to retain monitoring data"
  type        = number
  default     = 30
  
  validation {
    condition     = var.monitoring_retention_days >= 1 && var.monitoring_retention_days <= 365
    error_message = "Monitoring retention must be between 1 and 365 days."
  }
}

# ============================================================================
# Security Configuration
# ============================================================================

variable "enable_encryption" {
  description = "Enable encryption at rest for all supported resources"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 35
    error_message = "Backup retention must be between 1 and 35 days."
  }
}

# ============================================================================
# Cost Optimization
# ============================================================================

variable "enable_cost_optimization" {
  description = "Enable cost optimization features (spot instances, scheduled scaling)"
  type        = bool
  default     = false
}

variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_instance_percentage" {
  description = "Percentage of spot instances in node groups (0-100)"
  type        = number
  default     = 50
  
  validation {
    condition     = var.spot_instance_percentage >= 0 && var.spot_instance_percentage <= 100
    error_message = "Spot instance percentage must be between 0 and 100."
  }
}

# ============================================================================
# Feature Flags
# ============================================================================

variable "enable_web_scraping" {
  description = "Enable web scraping infrastructure and workers"
  type        = bool
  default     = true
}

variable "enable_analytics" {
  description = "Enable advanced analytics and ML infrastructure"
  type        = bool
  default     = true
}

variable "enable_dashboard" {
  description = "Enable interactive dashboard deployment"
  type        = bool
  default     = true
}

variable "enable_api_gateway" {
  description = "Enable API Gateway for external API access"
  type        = bool
  default     = true
}

# ============================================================================
# Resource Tags
# ============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "cost_center" {
  description = "Cost center for billing and resource allocation"
  type        = string
  default     = "engineering"
}

variable "project_code" {
  description = "Project code for tracking and billing"
  type        = string
  default     = "ATHINTEL-2025"
}

# ============================================================================
# Performance Configuration
# ============================================================================

variable "enable_performance_mode" {
  description = "Enable high-performance configuration (larger instances, more resources)"
  type        = bool
  default     = false
}

variable "scraper_worker_count" {
  description = "Number of scraper workers to deploy"
  type        = number
  default     = 2
  
  validation {
    condition     = var.scraper_worker_count >= 1 && var.scraper_worker_count <= 20
    error_message = "Scraper worker count must be between 1 and 20."
  }
}

variable "analytics_worker_count" {
  description = "Number of analytics workers to deploy"
  type        = number
  default     = 2
  
  validation {
    condition     = var.analytics_worker_count >= 1 && var.analytics_worker_count <= 10
    error_message = "Analytics worker count must be between 1 and 10."
  }
}

# ============================================================================
# Environment-specific Configurations
# ============================================================================

variable "environment_configs" {
  description = "Environment-specific configuration overrides"
  type = map(object({
    node_instance_types     = list(string)
    node_group_min_size    = number
    node_group_max_size    = number
    node_group_desired_size = number
    db_instance_class      = string
    redis_node_type        = string
    backup_retention_days  = number
    monitoring_retention_days = number
    enable_multi_az        = bool
  }))
  
  default = {
    dev = {
      node_instance_types     = ["t3.medium"]
      node_group_min_size    = 1
      node_group_max_size    = 5
      node_group_desired_size = 2
      db_instance_class      = "db.t3.micro"
      redis_node_type        = "cache.t3.micro"
      backup_retention_days  = 1
      monitoring_retention_days = 7
      enable_multi_az        = false
    }
    
    staging = {
      node_instance_types     = ["t3.large"]
      node_group_min_size    = 2
      node_group_max_size    = 10
      node_group_desired_size = 3
      db_instance_class      = "db.t3.small"
      redis_node_type        = "cache.t3.small"
      backup_retention_days  = 7
      monitoring_retention_days = 14
      enable_multi_az        = false
    }
    
    prod = {
      node_instance_types     = ["t3.xlarge", "t3.2xlarge"]
      node_group_min_size    = 3
      node_group_max_size    = 20
      node_group_desired_size = 5
      db_instance_class      = "db.r5.large"
      redis_node_type        = "cache.r5.large"
      backup_retention_days  = 30
      monitoring_retention_days = 90
      enable_multi_az        = true
    }
  }
}

# ============================================================================
# Disaster Recovery Configuration
# ============================================================================

variable "enable_disaster_recovery" {
  description = "Enable disaster recovery features (cross-region backups, replication)"
  type        = bool
  default     = false
}

variable "dr_region" {
  description = "Disaster recovery region"
  type        = string
  default     = "eu-west-1"
  
  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.dr_region))
    error_message = "DR region must be a valid region identifier."
  }
}

# ============================================================================
# Networking Configuration
# ============================================================================

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services to reduce NAT gateway costs"
  type        = bool
  default     = true
}

variable "enable_transit_gateway" {
  description = "Enable AWS Transit Gateway for complex network topologies"
  type        = bool
  default     = false
}

# ============================================================================
# Compliance Configuration
# ============================================================================

variable "compliance_framework" {
  description = "Compliance framework to adhere to (gdpr, hipaa, sox, none)"
  type        = string
  default     = "gdpr"
  
  validation {
    condition     = contains(["gdpr", "hipaa", "sox", "none"], var.compliance_framework)
    error_message = "Compliance framework must be gdpr, hipaa, sox, or none."
  }
}

variable "enable_audit_logging" {
  description = "Enable comprehensive audit logging for compliance"
  type        = bool
  default     = true
}

# ============================================================================
# Data Retention Configuration
# ============================================================================

variable "data_retention_policies" {
  description = "Data retention policies for different data types"
  type = object({
    raw_data_days      = number
    processed_data_days = number
    analytics_data_days = number
    log_data_days       = number
  })
  
  default = {
    raw_data_days      = 90
    processed_data_days = 365
    analytics_data_days = 1095  # 3 years
    log_data_days       = 30
  }
  
  validation {
    condition = alltrue([
      var.data_retention_policies.raw_data_days >= 1,
      var.data_retention_policies.processed_data_days >= 1,
      var.data_retention_policies.analytics_data_days >= 1,
      var.data_retention_policies.log_data_days >= 1
    ])
    error_message = "All data retention periods must be at least 1 day."
  }
}