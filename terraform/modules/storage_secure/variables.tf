# Secure Storage Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "bucket_suffix" {
  description = "Random suffix for bucket uniqueness"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning for dashboard bucket"
  type        = bool
  default     = false
}

variable "allowed_origins" {
  description = "Allowed origins for CORS (CloudFront URLs)"
  type        = list(string)
  default     = ["*"]
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
