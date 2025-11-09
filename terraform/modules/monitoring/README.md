# Monitoring Module

This module creates a CloudWatch dashboard for monitoring Lambda functions, DynamoDB tables, and overall system health.

## Purpose

Provides centralized operational visibility with real-time metrics for all AWS resources in the certificate management system.

## Resources Created

### CloudWatch Dashboard (`aws_cloudwatch_dashboard.main`)
- **Name**: `{project_name}-{environment}-dashboard`
- **Widgets**: Time series graphs for Lambda and DynamoDB metrics
- **Refresh**: Auto-refresh every 1 minute
- **Time Range**: Last 3 hours (configurable)

## Dashboard Widgets

### Lambda Metrics
For each Lambda function (certificate-monitor, excel-processor, dashboard-api):

1. **Duration** - Execution time in milliseconds
2. **Errors** - Number of invocation errors
3. **Invocations** - Total invocation count
4. **Throttles** - Number of throttled invocations

### DynamoDB Metrics
For each table (certificates, certificate-logs):

1. **Consumed Read Capacity** - Read capacity units consumed
2. **Consumed Write Capacity** - Write capacity units consumed
3. **User Errors** - 400-level errors (client errors)
4. **System Errors** - 500-level errors (server errors)

## Inputs

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `project_name` | `string` | Project name prefix | Yes |
| `environment` | `string` | Environment name | Yes |
| `certificate_monitor_function_name` | `string` | Certificate monitor function name | Yes |
| `excel_processor_function_name` | `string` | Excel processor function name | Yes |
| `dashboard_api_function_name` | `string` | Dashboard API function name | Yes |
| `certificates_table_name` | `string` | Certificates table name | Yes |
| `logs_table_name` | `string` | Logs table name | Yes |
| `aws_region` | `string` | AWS region | Yes |

## Outputs

| Output | Description |
|--------|-------------|
| `dashboard_name` | CloudWatch dashboard name |
| `dashboard_arn` | CloudWatch dashboard ARN |

## Example Usage

```hcl
module "monitoring" {
  source = "../../modules/monitoring"

  project_name                       = var.project_name
  environment                        = var.environment
  certificate_monitor_function_name  = module.lambda_secure.certificate_monitor_function_name
  excel_processor_function_name      = module.lambda_secure.excel_processor_function_name
  dashboard_api_function_name        = module.lambda_secure.dashboard_api_function_name
  certificates_table_name            = module.database.certificates_table_name
  logs_table_name                    = module.database.logs_table_name
  aws_region                         = var.aws_region
}
```

## Accessing the Dashboard

### AWS Console
1. Open CloudWatch console
2. Navigate to "Dashboards"
3. Select `cert-management-dev-secure-dashboard`

### AWS CLI
```bash
aws cloudwatch get-dashboard \
  --dashboard-name cert-management-dev-secure-dashboard \
  --region eu-west-1
```

### Direct URL
```
https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#dashboards:name=cert-management-dev-secure-dashboard
```

## Dashboard JSON Structure

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", {"stat": "Average", "label": "Avg Duration"}],
          ["...", {"stat": "Maximum", "label": "Max Duration"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "eu-west-1",
        "title": "Lambda Duration",
        "yAxis": {"left": {"label": "Milliseconds"}}
      }
    }
  ]
}
```

## Key Metrics to Monitor

### Lambda Health Indicators
- **Duration** > 80% of timeout → Increase timeout or optimize code
- **Errors** > 0 → Check CloudWatch Logs for stack traces
- **Throttles** > 0 → Increase concurrency limit
- **Invocations** dropping → Check EventBridge schedule or API Gateway

### DynamoDB Health Indicators
- **Consumed Capacity** approaching limits → Switch to provisioned capacity
- **User Errors** (400s) → Application validation issues
- **System Errors** (500s) → AWS service issues, contact support
- **Throttled Requests** > 0 → Increase capacity or optimize queries

## CloudWatch Alarms (Recommended)

### Lambda Error Alarm
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name cert-monitor-errors \
  --alarm-description "Alert when certificate monitor has errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=cert-management-dev-secure-certificate-monitor \
  --alarm-actions arn:aws:sns:eu-west-1:123456789012:alerts
```

### DynamoDB Throttling Alarm
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name dynamodb-throttling \
  --metric-name UserErrors \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=TableName,Value=cert-management-dev-secure-certificates
```

## Cost

CloudWatch pricing:
- **Dashboards**: First 3 dashboards free, then $3/dashboard/month
- **Metrics**: First 10 custom metrics free, then $0.30/metric/month
- **Alarms**: First 10 alarms free, then $0.10/alarm/month

**Total Cost**: $0/month (within free tier for small deployments)

## Best Practices

1. **Anomaly Detection**: Set up CloudWatch Anomaly Detection for automatic alerting
2. **Composite Alarms**: Combine multiple alarms to reduce noise
3. **SNS Integration**: Send alarm notifications to email, Slack, PagerDuty
4. **Custom Metrics**: Add business metrics (certificates processed, emails sent)
5. **Log Insights**: Use CloudWatch Logs Insights for advanced log analysis
6. **Dashboard Sharing**: Share dashboard URL with team

## Dependencies

- **Lambda Functions**: All three Lambda functions must exist
- **DynamoDB Tables**: Both tables must exist

## Related Modules

- **Lambda Secure**: Provides Lambda function names
- **Database**: Provides table names

## References

- [CloudWatch Dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html)
- [CloudWatch Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html)
- [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/)
