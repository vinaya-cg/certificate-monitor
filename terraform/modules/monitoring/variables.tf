# Monitoring Module - Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "certificate_monitor_function_name" {
  description = "Name of the certificate monitor Lambda function"
  type        = string
}

variable "certificates_table_name" {
  description = "Name of the certificates DynamoDB table"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
