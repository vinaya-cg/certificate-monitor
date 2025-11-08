# Dashboard Module - Variables

variable "dashboard_bucket_name" {
  description = "Name of the dashboard S3 bucket"
  type        = string
}

variable "api_url" {
  description = "Lambda Function URL for the dashboard API"
  type        = string
}

variable "source_files_path" {
  description = "Path to dashboard source files"
  type        = string
}
