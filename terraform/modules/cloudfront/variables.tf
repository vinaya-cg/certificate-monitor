# CloudFront Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "s3_bucket_id" {
  description = "ID of the S3 bucket (dashboard bucket)"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "s3_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  type        = string
}

variable "origin_verify_secret" {
  description = "Secret value for origin verification header"
  type        = string
  default     = ""
}

variable "price_class" {
  description = "CloudFront price class (PriceClass_All, PriceClass_200, PriceClass_100)"
  type        = string
  default     = "PriceClass_100" # US, Canada, Europe
}

variable "use_custom_domain" {
  description = "Whether to use a custom domain name"
  type        = bool
  default     = false
}

variable "custom_domain_names" {
  description = "List of custom domain names"
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for custom domain (must be in us-east-1)"
  type        = string
  default     = null
}

variable "enable_logging" {
  description = "Enable CloudFront access logging"
  type        = bool
  default     = false
}

variable "logging_bucket_domain_name" {
  description = "Domain name of S3 bucket for CloudFront logs"
  type        = string
  default     = ""
}

variable "web_acl_id" {
  description = "AWS WAF Web ACL ID (optional)"
  type        = string
  default     = null
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
