FROM public.ecr.aws/lambda/python:3.9

# 1. Install zip
RUN yum -y install zip

# 2. Create and set /app as the working directory
WORKDIR /app

# 3. Copy function code and requirements into /app
COPY lambda_function.py .
COPY requirements.txt .

# 4. Install your dependencies into the *current* directory (.)
RUN pip install --upgrade pip
RUN pip install --target . -r requirements.txt

# 5. Zip everything (lambda_function.py + installed packages) into /app/lambda_function.zip
RUN zip -r lambda_function.zip .
