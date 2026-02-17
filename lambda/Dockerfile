FROM amazon/aws-lambda-python:3.13
# Install pip dependencies
RUN pip install curl-cffi pandas beautifulsoup4 openpyxl
# Copy the main application code
COPY main.py prompt.py ./
# Command to run the Lambda function
CMD [ "main.lambda_handler" ]