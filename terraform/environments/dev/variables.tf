# Development Environment - Variables

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cert-management"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "owner_tag" {
  description = "Owner tag for resources"
  type        = string
  default     = "Certificate-Management-Team"
}

variable "sender_email" {
  description = "Email address for sending notifications"
  type        = string
}

variable "expiry_threshold_days" {
  description = "Number of days before expiry to trigger alerts"
  type        = number
  default     = 30
}

variable "monitoring_schedule" {
  description = "Schedule expression for certificate monitoring"
  type        = string
  default     = "cron(0 9 * * ? *)"
}
