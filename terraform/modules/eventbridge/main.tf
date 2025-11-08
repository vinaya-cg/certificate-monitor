# EventBridge Module - Scheduled Monitoring
# Manages EventBridge rule for daily certificate monitoring

locals {
  common_name = "${var.project_name}-${var.environment}"
}

# ===================================================================
# EVENTBRIDGE RULE
# ===================================================================

resource "aws_cloudwatch_event_rule" "daily_monitor" {
  name                = "${local.common_name}-daily-monitor"
  description         = "Trigger certificate monitoring daily"
  schedule_expression = var.schedule_expression

}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_monitor.name
  target_id = "CertificateMonitorTarget"
  arn       = var.certificate_monitor_function_arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.certificate_monitor_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_monitor.arn
}
