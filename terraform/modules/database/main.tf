# Database Module - DynamoDB Tables
# Manages certificates and logs tables with GSIs

locals {
  common_name = "${var.project_name}-${var.environment}"
}

# ===================================================================
# CERTIFICATES TABLE
# ===================================================================

resource "aws_dynamodb_table" "certificates" {
  name         = "${local.common_name}-certificates"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "CertificateID"

  attribute {
    name = "CertificateID"
    type = "S"
  }

  attribute {
    name = "Status"
    type = "S"
  }

  attribute {
    name = "ExpiryDate"
    type = "S"
  }

  attribute {
    name = "Environment"
    type = "S"
  }

  attribute {
    name = "OwnerEmail"
    type = "S"
  }

  # GSI for status-based queries
  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "Status"
    range_key       = "ExpiryDate"
    projection_type = "ALL"
  }

  # GSI for environment-based queries
  global_secondary_index {
    name            = "EnvironmentIndex"
    hash_key        = "Environment"
    range_key       = "ExpiryDate"
    projection_type = "ALL"
  }

  # GSI for owner-based queries
  global_secondary_index {
    name            = "OwnerIndex"
    hash_key        = "OwnerEmail"
    range_key       = "ExpiryDate"
    projection_type = "ALL"
  }

  # GSI for expiry date queries
  global_secondary_index {
    name            = "ExpiryIndex"
    hash_key        = "ExpiryDate"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${local.common_name}-certificates"
    }
  )
}

# ===================================================================
# CERTIFICATE LOGS TABLE
# ===================================================================

resource "aws_dynamodb_table" "certificate_logs" {
  name         = "${local.common_name}-certificate-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LogID"
  range_key    = "Timestamp"

  attribute {
    name = "LogID"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "S"
  }

  attribute {
    name = "CertificateID"
    type = "S"
  }

  attribute {
    name = "Action"
    type = "S"
  }

  # GSI for certificate-based log queries
  global_secondary_index {
    name            = "CertificateLogsIndex"
    hash_key        = "CertificateID"
    range_key       = "Timestamp"
    projection_type = "ALL"
  }

  # GSI for action-based queries
  global_secondary_index {
    name            = "ActionIndex"
    hash_key        = "Action"
    range_key       = "Timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${local.common_name}-certificate-logs"
    }
  )
}
