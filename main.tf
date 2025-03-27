terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

data "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
}

resource "aws_lambda_function" "lambda_function" {
  function_name = "formation-global-apollo-leads"
  runtime       = "python3.9"
  handler       = "lambda_function.lambda_handler"
  role          = data.aws_iam_role.lambda_role.arn

  filename = "lambda_function.zip"

  timeout = 900 # Timeout in seconds

  # Memory size in MB
  memory_size = 4000

  # Ephemeral storage in MB (Default: 512 MB, Max: 10,240 MB)
  ephemeral_storage {
    size = 2000 # 1 GB
  }

  source_code_hash = filebase64sha256("lambda_function.zip")

  environment {
    variables = {}
  }
}

resource "aws_apigatewayv2_api" "formation_global_apollo_leads" {
  name          = "formation-global-apollo-leads"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id               = aws_apigatewayv2_api.formation_global_apollo_leads.id
  integration_type     = "AWS_PROXY"
  integration_uri      = aws_lambda_function.lambda_function.arn
  passthrough_behavior = "WHEN_NO_MATCH"

  depends_on = [aws_lambda_function.lambda_function]
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.formation_global_apollo_leads.id
  route_key = "POST /"

  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_lambda_permission" "apigw_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.formation_global_apollo_leads.execution_arn}/*/*"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.formation_global_apollo_leads.id
  name        = "$default"
  auto_deploy = true
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.formation_global_apollo_leads.api_endpoint
}
