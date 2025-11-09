# API Gateway Module Variables

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool for authorization"
  type        = string
}

variable "dashboard_api_lambda_name" {
  description = "Name of the dashboard API Lambda function"
  type        = string
}

variable "dashboard_api_lambda_invoke_arn" {
  description = "Invoke ARN of the dashboard API Lambda function"
  type        = string
}

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing for API Gateway"
  type        = bool
  default     = false
}

variable "enable_detailed_logging" {
  description = "Enable detailed CloudWatch logging"
  type        = bool
  default     = false
}

variable "throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 5000
}

variable "throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 2000
}

variable "enable_usage_plan" {
  description = "Enable API Gateway usage plan"
  type        = bool
  default     = false
}

variable "quota_limit" {
  description = "Daily API quota limit"
  type        = number
  default     = 10000
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
