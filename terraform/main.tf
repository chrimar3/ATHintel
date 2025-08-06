# ATHintel Enterprise Platform - Terraform Infrastructure as Code
# Cloud-native deployment on AWS with auto-scaling and high availability

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
  
  backend "s3" {
    # Configure your backend in terraform.tfvars or via CLI
    # bucket = "athintel-terraform-state"
    # key    = "infrastructure/terraform.tfstate"
    # region = "eu-central-1"
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "ATHintel"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "ATHintel-DevOps"
    }
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# ============================================================================
# Local Values & Data Sources
# ============================================================================

locals {
  name = "athintel-${var.environment}"
  
  common_tags = {
    Project     = "ATHintel"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
  
  # Availability zones
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
}

data "aws_availability_zones" "available" {}

data "aws_caller_identity" "current" {}

# ============================================================================
# Random Resources
# ============================================================================

resource "random_password" "database_password" {
  length  = 32
  special = true
}

resource "random_password" "redis_password" {
  length  = 32
  special = false
}

# ============================================================================
# VPC & Networking
# ============================================================================

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "${local.name}-vpc"
  cidr = var.vpc_cidr
  
  azs             = local.azs
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets
  
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment == "dev"
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true
  
  # VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  
  # Tags for EKS
  public_subnet_tags = {
    "kubernetes.io/cluster/${local.name}" = "shared"
    "kubernetes.io/role/elb"               = "1"
  }
  
  private_subnet_tags = {
    "kubernetes.io/cluster/${local.name}" = "shared"
    "kubernetes.io/role/internal-elb"     = "1"
  }
  
  tags = local.common_tags
}

# ============================================================================
# Security Groups
# ============================================================================

resource "aws_security_group" "database" {
  name_prefix = "${local.name}-database-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name}-database-sg"
  })
}

resource "aws_security_group" "redis" {
  name_prefix = "${local.name}-redis-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name}-redis-sg"
  })
}

# ============================================================================
# EKS Cluster
# ============================================================================

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = local.name
  cluster_version = var.kubernetes_version
  
  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true
  
  # Cluster encryption
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }
  
  # EKS Managed Node Groups
  eks_managed_node_groups = {
    # Main application nodes
    main = {
      name           = "${local.name}-main"
      instance_types = var.node_instance_types
      
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size
      desired_size = var.node_group_desired_size
      
      # Use latest EKS Optimized AMI
      ami_type = "AL2_x86_64"
      
      # Node group configuration
      disk_size = 50
      
      # Taints and labels
      labels = {
        role = "main"
      }
      
      tags = {
        "k8s.io/cluster-autoscaler/enabled"          = "true"
        "k8s.io/cluster-autoscaler/${local.name}"    = "owned"
      }
    }
    
    # Scraper nodes with more resources
    scraper = {
      name           = "${local.name}-scraper"
      instance_types = ["c5.xlarge", "c5.2xlarge"]
      
      min_size     = 1
      max_size     = 10
      desired_size = 2
      
      # Larger disk for browser cache
      disk_size = 100
      
      labels = {
        role = "scraper"
      }
      
      taints = [
        {
          key    = "workload"
          value  = "scraper"
          effect = "NO_SCHEDULE"
        }
      ]
      
      tags = {
        "k8s.io/cluster-autoscaler/enabled"          = "true"
        "k8s.io/cluster-autoscaler/${local.name}"    = "owned"
      }
    }
  }
  
  # Fargate Profiles (for lightweight workloads)
  fargate_profiles = var.enable_fargate ? {
    monitoring = {
      name = "${local.name}-monitoring"
      selectors = [
        {
          namespace = "monitoring"
          labels = {
            fargate = "true"
          }
        }
      ]
    }
  } : {}
  
  tags = local.common_tags
}

# ============================================================================
# KMS Key for EKS
# ============================================================================

resource "aws_kms_key" "eks" {
  description             = "EKS Secret Encryption Key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name}-eks-encryption-key"
  })
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${local.name}-eks"
  target_key_id = aws_kms_key.eks.key_id
}

# ============================================================================
# RDS PostgreSQL Database
# ============================================================================

module "rds" {
  source = "terraform-aws-modules/rds/aws"
  
  identifier = "${local.name}-postgresql"
  
  # Database configuration
  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = var.db_instance_class
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.database.arn
  
  # Database credentials
  db_name  = "athintel"
  username = "athintel"
  password = random_password.database_password.result
  
  # Networking
  create_db_subnet_group = true
  subnet_ids             = module.vpc.private_subnets
  vpc_security_group_ids = [aws_security_group.database.id]
  
  # Backup configuration
  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Multi-AZ for production
  multi_az = var.environment == "prod"
  
  # Enhanced monitoring
  monitoring_interval    = 60
  monitoring_role_name   = "${local.name}-rds-monitoring-role"
  create_monitoring_role = true
  
  # Performance Insights
  performance_insights_enabled = var.environment == "prod"
  
  # Parameter group
  parameters = [
    {
      name  = "log_statement"
      value = "all"
    },
    {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries taking longer than 1 second
    },
    {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
    }
  ]
  
  tags = local.common_tags
}

# KMS key for database encryption
resource "aws_kms_key" "database" {
  description             = "RDS encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name}-rds-encryption-key"
  })
}

resource "aws_kms_alias" "database" {
  name          = "alias/${local.name}-rds"
  target_key_id = aws_kms_key.database.key_id
}

# ============================================================================
# ElastiCache Redis Cluster
# ============================================================================

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
  
  tags = local.common_tags
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${local.name}-redis"
  description                = "ATHintel Redis cluster"
  
  node_type          = var.redis_node_type
  port               = 6379
  parameter_group_name = "default.redis7"
  
  num_cache_clusters = var.redis_num_cache_nodes
  
  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_password.result
  
  # Networking
  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]
  
  # Backup
  snapshot_retention_limit = var.environment == "prod" ? 7 : 1
  snapshot_window         = "03:00-04:00"
  
  # Maintenance
  maintenance_window = "sun:04:00-sun:05:00"
  
  # Automatic failover for multi-node clusters
  automatic_failover_enabled = var.redis_num_cache_nodes > 1
  
  tags = local.common_tags
}

# ============================================================================
# ECR Repositories
# ============================================================================

resource "aws_ecr_repository" "athintel" {
  for_each = toset([
    "athintel-api",
    "athintel-dashboard", 
    "athintel-scraper-worker",
    "athintel-analytics-worker",
    "athintel-monitoring"
  ])
  
  name                 = each.value
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  encryption_configuration {
    encryption_type = "AES256"
  }
  
  lifecycle_policy {
    policy = jsonencode({
      rules = [
        {
          rulePriority = 1
          description  = "Keep last 30 images"
          selection = {
            tagStatus     = "tagged"
            tagPrefixList = ["v"]
            countType     = "imageCountMoreThan"
            countNumber   = 30
          }
          action = {
            type = "expire"
          }
        },
        {
          rulePriority = 2
          description  = "Delete untagged images older than 1 day"
          selection = {
            tagStatus   = "untagged"
            countType   = "sinceImagePushed"
            countUnit   = "days"
            countNumber = 1
          }
          action = {
            type = "expire"
          }
        }
      ]
    })
  }
  
  tags = local.common_tags
}

# ============================================================================
# Application Load Balancer
# ============================================================================

module "alb" {
  source = "terraform-aws-modules/alb/aws"
  
  name               = "${local.name}-alb"
  load_balancer_type = "application"
  
  vpc_id          = module.vpc.vpc_id
  subnets         = module.vpc.public_subnets
  security_groups = [aws_security_group.alb.id]
  
  # Access logs
  access_logs = {
    bucket = aws_s3_bucket.alb_logs.id
    prefix = "alb"
  }
  
  # Target groups will be created by Kubernetes ingress controller
  target_groups = [
    {
      name_prefix      = "api-"
      backend_protocol = "HTTP"
      backend_port     = 80
      target_type      = "ip"
      
      health_check = {
        enabled             = true
        healthy_threshold   = 2
        interval            = 30
        matcher             = "200"
        path                = "/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }
    }
  ]
  
  # HTTPS listeners
  https_listeners = [
    {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = module.acm.acm_certificate_arn
      target_group_index = 0
    }
  ]
  
  # HTTP listeners (redirect to HTTPS)
  http_tcp_listeners = [
    {
      port        = 80
      protocol    = "HTTP"
      action_type = "redirect"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  ]
  
  tags = local.common_tags
}

# ALB Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${local.name}-alb-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(local.common_tags, {
    Name = "${local.name}-alb-sg"
  })
}

# S3 bucket for ALB access logs
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${local.name}-alb-access-logs"
  force_destroy = true
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================================================
# SSL Certificate
# ============================================================================

module "acm" {
  source = "terraform-aws-modules/acm/aws"
  
  domain_name       = var.domain_name
  zone_id           = aws_route53_zone.main.zone_id
  validation_method = "DNS"
  
  subject_alternative_names = [
    "*.${var.domain_name}",
    "api.${var.domain_name}",
    "dashboard.${var.domain_name}",
    "monitoring.${var.domain_name}"
  ]
  
  wait_for_validation = true
  
  tags = local.common_tags
}

# ============================================================================
# Route53 DNS
# ============================================================================

resource "aws_route53_zone" "main" {
  name = var.domain_name
  
  tags = local.common_tags
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  
  alias {
    name                   = module.alb.lb_dns_name
    zone_id                = module.alb.lb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "dashboard" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "dashboard.${var.domain_name}"
  type    = "A"
  
  alias {
    name                   = module.alb.lb_dns_name
    zone_id                = module.alb.lb_zone_id
    evaluate_target_health = true
  }
}

# ============================================================================
# S3 Buckets for Data Storage
# ============================================================================

# Data lake bucket
resource "aws_s3_bucket" "data_lake" {
  bucket = "${local.name}-data-lake"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# Lifecycle configuration for data lake
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  
  rule {
    id     = "data_lifecycle"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# KMS key for S3 encryption
resource "aws_kms_key" "s3" {
  description             = "S3 encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name}-s3-encryption-key"
  })
}

resource "aws_kms_alias" "s3" {
  name          = "alias/${local.name}-s3"
  target_key_id = aws_kms_key.s3.key_id
}

# ============================================================================
# CloudWatch Log Groups
# ============================================================================

resource "aws_cloudwatch_log_group" "application" {
  for_each = toset([
    "/aws/eks/${local.name}/api",
    "/aws/eks/${local.name}/dashboard",
    "/aws/eks/${local.name}/scraper-worker",
    "/aws/eks/${local.name}/analytics-worker",
    "/aws/eks/${local.name}/monitoring"
  ])
  
  name              = each.value
  retention_in_days = var.environment == "prod" ? 30 : 7
  kms_key_id       = aws_kms_key.cloudwatch.arn
  
  tags = local.common_tags
}

# KMS key for CloudWatch logs
resource "aws_kms_key" "cloudwatch" {
  description             = "CloudWatch Logs encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnEquals = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
          }
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = "${local.name}-cloudwatch-encryption-key"
  })
}

resource "aws_kms_alias" "cloudwatch" {
  name          = "alias/${local.name}-cloudwatch"
  target_key_id = aws_kms_key.cloudwatch.key_id
}

# ============================================================================
# IAM Roles and Policies
# ============================================================================

# EKS Node Group Instance Profile
data "aws_iam_policy_document" "node_group_assume_role" {
  statement {
    effect = "Allow"
    
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
    
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "node_group" {
  name               = "${local.name}-node-group-role"
  assume_role_policy = data.aws_iam_policy_document.node_group_assume_role.json
  
  tags = local.common_tags
}

# Attach required policies to node group role
resource "aws_iam_role_policy_attachment" "node_group_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy", 
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  ])
  
  policy_arn = each.value
  role       = aws_iam_role.node_group.name
}

# Additional IAM policy for application-specific permissions
resource "aws_iam_policy" "application_policy" {
  name        = "${local.name}-application-policy"
  description = "Policy for ATHintel application components"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.database_credentials.arn,
          aws_secretsmanager_secret.redis_credentials.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = [
          aws_kms_key.s3.arn,
          aws_kms_key.database.arn
        ]
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "node_group_application_policy" {
  policy_arn = aws_iam_policy.application_policy.arn
  role       = aws_iam_role.node_group.name
}

# ============================================================================
# Secrets Manager
# ============================================================================

resource "aws_secretsmanager_secret" "database_credentials" {
  name                    = "${local.name}-database-credentials"
  description             = "Database credentials for ATHintel"
  recovery_window_in_days = 7
  kms_key_id             = aws_kms_key.database.arn
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "database_credentials" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    username = module.rds.db_instance_username
    password = random_password.database_password.result
    engine   = "postgres"
    host     = module.rds.db_instance_endpoint
    port     = module.rds.db_instance_port
    dbname   = module.rds.db_instance_name
  })
}

resource "aws_secretsmanager_secret" "redis_credentials" {
  name                    = "${local.name}-redis-credentials"
  description             = "Redis credentials for ATHintel"
  recovery_window_in_days = 7
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis_credentials" {
  secret_id = aws_secretsmanager_secret.redis_credentials.id
  secret_string = jsonencode({
    auth_token = random_password.redis_password.result
    host       = aws_elasticache_replication_group.redis.configuration_endpoint_address
    port       = aws_elasticache_replication_group.redis.port
  })
}