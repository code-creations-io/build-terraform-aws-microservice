# build-terraform-aws-microservice

- Created at: 2025-03-26
- Created by: `🐢 Arun Godwin Patel @ Code Creations`

## Table of contents

- [Setup](#setup)
  - [System](#system)
  - [Installation](#installation)
- [Walkthrough](#walkthrough)
  - [Code Structure](#code-structure)
  - [Tech stack](#tech-stack)
  - [Build from scratch](#build-from-scratch)
    - [1. Build the Docker container](#1-build-the-docker-container)
    - [2. Initialize the Terraform Configuration](#2-initialize-the-terraform-configuration)
    - [3. Review the Plan](#3-review-the-plan)
    - [4. Apply the Terraform Configuration](#4-apply-the-terraform-configuration)
    - [5. Destroy the resources](#5-destroy-the-resources)

## Setup

### System

This code repository was tested on the following computers:

- Windows 11

### Installation

1. Install Docker Desktop
2. Install Terraform
3. Zip utility
4. Create an AWS account
5. Create an IAM user with the necessary permissions
6. Install AWS CLI

## Walkthrough

### Code Structure

The code directory structure is as follows:

```plaintext
│   .gitignore
│   Dockerfile
│   lambda_function.py
│   main.tf
│   README.md
│   requirements.txt
```

The `Dockerfile` contains the instructions to build the Docker container.

The `main.tf` file contains the Terraform configuration to deploy the Lambda function, create an API Gateway endpoint, and set up the necessary IAM roles and policies.

The `lambda_function.py` file contains the Python code for the Lambda function, which is triggered by the API Gateway endpoint.

The `.gitignore` file specifies the files and directories that should be ignored by Git.

The `requirements.txt` file lists the Python packages required by the Lambda function.

### Tech stack

**Microservice**

- Containerisation: `Docker`
- REST API: `API Gateway`
- Infrastructure as Code: `Terraform`
- Lambda function: `Python`

### Build from scratch

This project was built from scratch using Python, Docker, Terraform, and AWS Lambda. The following steps outline how to build the project for yourself and deploy an AWS API Gateway endpoint powered by a Lambda function within seconds.

#### 1. Build the main.tf file

The `main.tf` file contains the Terraform configuration to deploy the Lambda function, create an API Gateway endpoint, and set up the necessary IAM roles and policies.

```hcl
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
```

Add an IAM role and attach a policy

```hcl
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
```

Create the Lambda function

```hcl
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
```

Create the API Gateway endpoint

```hcl
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
```

Output the API Gateway endpoint

```hcl
output "api_endpoint" {
  value = aws_apigatewayv2_api.formation_global_apollo_leads.api_endpoint
}
```

#### 2. Create the Lambda function

The `lambda_function.py` file contains the Python code for the Lambda function, which is triggered by the API Gateway endpoint.

For this Lambda function, we're going to route the request to different handlers based on the `endpoint` value within the request body.

```python
import json

def hello_handler(body):
    return {"message": "Hello there, welcome!"}, 200

def goodbye_handler(body):
    return {"message": "Okay, goodbye then!"}, 200
```

And now create the main handler function, which will route the request to the appropriate handler, process the request and format the REST API response.

```python
def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
    except Exception:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Invalid JSON in request body"})
        }

    endpoint = body.get("endpoint")
    if not endpoint:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "No endpoint provided in request body"})
        }

    # Route to the appropriate handler based on the "endpoint" field
    if endpoint == "hello":
        result, status = hello_handler(body)
    elif endpoint == "goodbye":
        result, status = goodbye_handler(body)
    else:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": f"Unknown endpoint: {endpoint}"})
        }

    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }
```

#### 3. Build the Docker container

Docker is used to package the Lambda function and its dependencies into a container. This container is then used to create the Lambda function in AWS.

```bash
docker build -t lambda-build .
```

Now we can run this container from this built image

```bash
docker create --name lambda-container lambda-build
```

Before we can deploy the Lambda function, we need to copy the files we need from inside the container to the host so that we have a packaged lambda function to submit with Terraform.

```bash
docker cp lambda-container:/app/lambda_function.zip ./
```

Finally, we can clean up the container and the image.

```bash
docker rm lambda-container
docker rmi lambda-build
```

#### 4. Initialize the Terraform Configuration

First, we must sign in with the correct AWS CLI IAM credentials:

```bash
aws configure
```

Next, we need to initialize Terraform. Run the following command to initialize Terraform:

```bash
terraform init
```

#### 5. Review the Plan

Before deploying the resources, it is a good idea to review the plan to see what changes will be made.

```bash
TF_LOG=DEBUG terraform plan -out=tfplan
```

#### 4. Apply the Terraform Configuration

Deploy the resources using:

```bash
TF_LOG=DEBUG terraform apply
```

#### 6. Destroy the resources

To destroy the resources created by Terraform, run the following command:

```bash
TF_LOG=DEBUG terraform destroy
```

This completes the setup of our AWS MIcroservice deployed using Terraform. If completed successfully, you now have a fully scalable, publicly available API that you can use to build your applications.

#### 7. Some useful commands

1. If you no longer need Terraform files or the deployment package, you can delete them:

```bash
rm -rf .terraform terraform.tfstate* lambda_function.zip python
```

2. Refresh the state if you're having issues with Terraform:

```bash
terraform refresh
```

3. If the problem persists, try deleting the `.terraform` directory and reinitializing:

```bash
rm -rf .terraform
terraform init
```

4. If `terraform plan` is getting stuck or not working and you're running this code on Mac, run this in the terminal and try again:

```bash
export GODEBUG=asyncpreemptoff=1;
```

## Happy coding! 🚀

```bash
🐢 Arun Godwin Patel @ Code Creations
```
