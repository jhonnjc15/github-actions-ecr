FROM public.ecr.aws/lambda/python:3.11

WORKDIR /var/task
COPY main.py .

# handler
CMD ["main.lambda_handler"]