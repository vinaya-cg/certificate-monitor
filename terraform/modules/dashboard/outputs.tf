# Dashboard Module - Outputs

output "uploaded_files" {
  description = "List of files uploaded to S3"
  value = [
    aws_s3_object.index_html.key,
    aws_s3_object.login_html.key,
    aws_s3_object.error_html.key,
    aws_s3_object.auth_js.key,
    aws_s3_object.dashboard_js.key,
    aws_s3_object.postnl_logo.key,
    aws_s3_object.sogeti_logo.key
  ]
}
