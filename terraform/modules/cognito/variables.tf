# Cognito Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "domain_suffix" {
  description = "Random suffix for Cognito domain uniqueness"
  type        = string
}

variable "sender_email" {
  description = "Email address for Cognito notifications (must be verified in SES)"
  type        = string
}

variable "ses_identity_arn" {
  description = "ARN of the SES verified email identity"
  type        = string
}

variable "callback_urls" {
  description = "List of allowed callback URLs after authentication"
  type        = list(string)
  default     = ["http://localhost:3000"]
}

variable "logout_urls" {
  description = "List of allowed logout redirect URLs"
  type        = list(string)
  default     = ["http://localhost:3000"]
}

variable "admin_user" {
  description = "Admin user configuration"
  type = object({
    username = string
    email    = string
    name     = string
  })
}

variable "operator_user" {
  description = "Operator user configuration"
  type = object({
    username = string
    email    = string
    name     = string
  })
}

variable "viewer_user" {
  description = "Viewer user configuration"
  type = object({
    username = string
    email    = string
    name     = string
  })
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
