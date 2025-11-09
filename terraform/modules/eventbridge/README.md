# EventBridge Module

This module creates an EventBridge scheduled rule to trigger the certificate monitor Lambda function daily.

## Purpose

Provides automated daily scheduling for certificate expiry monitoring using Amazon EventBridge (formerly CloudWatch Events).

## Resources Created

### EventBridge Rule (`aws_cloudwatch_event_rule.certificate_monitor`)
- **Name**: `{project_name}-{environment}-certificate-monitor`
- **Schedule**: `cron(0 9 * * ? *)` - Daily at 9 AM UTC
- **State**: ENABLED
- **Description**: Daily trigger for certificate expiry monitoring

### EventBridge Target (`aws_cloudwatch_event_target.certificate_monitor`)
- **Rule**: certificate_monitor rule
- **Target**: certificate-monitor Lambda function
- **ARN**: Lambda function ARN

### Lambda Permission (`aws_lambda_permission.eventbridge`)
- **Action**: `lambda:InvokeFunction`
- **Principal**: `events.amazonaws.com`
- **Source ARN**: EventBridge rule ARN
- **Allows**: EventBridge to invoke Lambda function

## Inputs

| Variable | Type | Description | Required | Default |
|----------|------|-------------|----------|---------|
| `project_name` | `string` | Project name prefix | Yes | - |
| `environment` | `string` | Environment name | Yes | - |
| `certificate_monitor_function_arn` | `string` | Lambda function ARN | Yes | - |
| `certificate_monitor_function_name` | `string` | Lambda function name | Yes | - |
| `schedule_expression` | `string` | Cron expression for schedule | No | `cron(0 9 * * ? *)` |

## Outputs

| Output | Description |
|--------|-------------|
| `rule_arn` | EventBridge rule ARN |
| `rule_name` | EventBridge rule name |

## Example Usage

```hcl
module "eventbridge" {
  source = "../../modules/eventbridge"

  project_name                        = var.project_name
  environment                         = var.environment
  certificate_monitor_function_arn    = module.lambda_secure.certificate_monitor_function_arn
  certificate_monitor_function_name   = module.lambda_secure.certificate_monitor_function_name
  schedule_expression                 = "cron(0 9 * * ? *)"  # Daily at 9 AM UTC
}
```

## Schedule Expressions

EventBridge supports cron expressions:

```
cron(minute hour day-of-month month day-of-week year)
```

### Examples

| Description | Expression |
|-------------|------------|
| Daily at 9 AM UTC | `cron(0 9 * * ? *)` |
| Every 6 hours | `cron(0 */6 * * ? *)` |
| Weekdays at 8 AM | `cron(0 8 ? * MON-FRI *)` |
| First day of month | `cron(0 9 1 * ? *)` |
| Every 15 minutes | `cron(0/15 * * * ? *)` |

### Rate Expressions

Alternative to cron:

```
rate(value unit)
```

| Description | Expression |
|-------------|------------|
| Every day | `rate(1 day)` |
| Every 12 hours | `rate(12 hours)` |
| Every 5 minutes | `rate(5 minutes)` |

## How It Works

```
EventBridge Rule (Daily at 9 AM UTC)
         ↓
Evaluates cron expression
         ↓
If match → Trigger target
         ↓
Invoke certificate-monitor Lambda
         ↓
Lambda checks DynamoDB for expiring certificates
         ↓
Lambda sends SES emails to certificate owners
         ↓
Lambda logs results to CloudWatch
```

## Monitoring

### View Rule Details
```bash
aws events describe-rule \
  --name cert-management-dev-secure-certificate-monitor \
  --region eu-west-1
```

### View Rule Targets
```bash
aws events list-targets-by-rule \
  --rule cert-management-dev-secure-certificate-monitor \
  --region eu-west-1
```

### Check Invocation History
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=cert-management-dev-secure-certificate-monitor \
  --start-time 2025-11-08T00:00:00Z \
  --end-time 2025-11-09T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Testing

### Manually Trigger Rule
```bash
# Disable rule temporarily
aws events disable-rule \
  --name cert-management-dev-secure-certificate-monitor \
  --region eu-west-1

# Invoke Lambda directly for testing
aws lambda invoke \
  --function-name cert-management-dev-secure-certificate-monitor \
  --region eu-west-1 \
  response.json

# Re-enable rule
aws events enable-rule \
  --name cert-management-dev-secure-certificate-monitor \
  --region eu-west-1
```

## Troubleshooting

### Issue: Lambda not being invoked
**Cause**: Missing Lambda permission or rule disabled  
**Solution**: Check permission exists, verify rule is ENABLED

### Issue: Wrong schedule time
**Cause**: Time zone confusion (EventBridge uses UTC)  
**Solution**: Convert local time to UTC in cron expression

## Cost

EventBridge pricing:
- **Custom Rules**: Free (up to 14 million invocations/month)
- **Lambda Invocations**: Billed separately by Lambda

**Total Cost**: $0/month (within free tier)

## Dependencies

- **Lambda Function**: certificate-monitor must exist

## Related Modules

- **Lambda Secure**: Provides certificate-monitor function

## References

- [EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
- [Cron Expressions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html#eb-cron-expressions)
- [EventBridge Pricing](https://aws.amazon.com/eventbridge/pricing/)
