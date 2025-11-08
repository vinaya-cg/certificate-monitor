# IAM Module - Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "certificates_table_arn" {
  description = "ARN of the certificates DynamoDB table"
  type        = string
}

variable "logs_table_arn" {
  description = "ARN of the certificate logs DynamoDB table"
  type        = string
}

variable "uploads_bucket_arn" {
  description = "ARN of the uploads S3 bucket"
  type        = string
}

variable "dashboard_bucket_arn" {
  description = "ARN of the dashboard S3 bucket"
  type        = string
}

variable "logs_bucket_arn" {
  description = "ARN of the logs S3 bucket"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
