# Storage Module - Variables
# Manages S3 buckets for dashboard, uploads, and logs

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "bucket_suffix" {
  description = "Random suffix for unique bucket naming"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
