# API Gateway with Cognito Authorizer
# Replaces Lambda Function URL with secure authenticated API

# REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "Certificate Management API with Cognito authentication"

  endpoint_configuration {
    types = ["REGIONAL"]
  }


}

# Cognito Authorizer
resource "aws_api_gateway_authorizer" "cognito" {
  name            = "${var.project_name}-${var.environment}-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.main.id
  type            = "COGNITO_USER_POOLS"
  identity_source = "method.request.header.Authorization"
  provider_arns   = [var.cognito_user_pool_arn]
}

# Root Resource (/)
# The REST API automatically has a root resource

# Certificates Resource (/certificates)
resource "aws_api_gateway_resource" "certificates" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "certificates"
}

# GET /certificates - List all certificates
resource "aws_api_gateway_method" "get_certificates" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.certificates.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id

  request_parameters = {
    "method.request.querystring.status"      = false
    "method.request.querystring.environment" = false
  }
}

resource "aws_api_gateway_integration" "get_certificates" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.certificates.id
  http_method             = aws_api_gateway_method.get_certificates.http_method
  integration_http_method = "POST" # Lambda always uses POST
  type                    = "AWS_PROXY"
  uri                     = var.dashboard_api_lambda_invoke_arn
}

# POST /certificates - Add new certificate
resource "aws_api_gateway_method" "post_certificates" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.certificates.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "post_certificates" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.certificates.id
  http_method             = aws_api_gateway_method.post_certificates.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.dashboard_api_lambda_invoke_arn
}

# PUT /certificates - Update certificate
resource "aws_api_gateway_method" "put_certificates" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.certificates.id
  http_method   = "PUT"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "put_certificates" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.certificates.id
  http_method             = aws_api_gateway_method.put_certificates.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.dashboard_api_lambda_invoke_arn
}

# DELETE /certificates - Delete certificate
resource "aws_api_gateway_method" "delete_certificates" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.certificates.id
  http_method   = "DELETE"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
}

resource "aws_api_gateway_integration" "delete_certificates" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.certificates.id
  http_method             = aws_api_gateway_method.delete_certificates.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.dashboard_api_lambda_invoke_arn
}

# CORS for Certificates endpoint
resource "aws_api_gateway_method" "options_certificates" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.certificates.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_certificates" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.certificates.id
  http_method = aws_api_gateway_method.options_certificates.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_certificates_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.certificates.id
  http_method = aws_api_gateway_method.options_certificates.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_certificates" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.certificates.id
  http_method = aws_api_gateway_method.options_certificates.http_method
  status_code = aws_api_gateway_method_response.options_certificates_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT,DELETE'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.options_certificates]
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.dashboard_api_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# API Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.certificates.id,
      aws_api_gateway_method.get_certificates.id,
      aws_api_gateway_method.post_certificates.id,
      aws_api_gateway_method.put_certificates.id,
      aws_api_gateway_method.delete_certificates.id,
      aws_api_gateway_integration.get_certificates.id,
      aws_api_gateway_integration.post_certificates.id,
      aws_api_gateway_integration.put_certificates.id,
      aws_api_gateway_integration.delete_certificates.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.get_certificates,
    aws_api_gateway_integration.post_certificates,
    aws_api_gateway_integration.put_certificates,
    aws_api_gateway_integration.delete_certificates,
    aws_api_gateway_integration.options_certificates
  ]
}

# API Stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  # CloudWatch logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  # Method settings
  xray_tracing_enabled = var.enable_xray_tracing


}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}-api"
  retention_in_days = 30


}

# Method Settings (optional throttling and caching)
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    data_trace_enabled = var.enable_detailed_logging

    # Throttling
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit

    # Caching (optional)
    caching_enabled = false
  }
}

# Usage Plan (optional, for API key management)
resource "aws_api_gateway_usage_plan" "main" {
  count = var.enable_usage_plan ? 1 : 0

  name        = "${var.project_name}-${var.environment}-usage-plan"
  description = "Usage plan for ${var.project_name} ${var.environment}"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  quota_settings {
    limit  = var.quota_limit
    period = "DAY"
  }

  throttle_settings {
    burst_limit = var.throttling_burst_limit
    rate_limit  = var.throttling_rate_limit
  }


}
