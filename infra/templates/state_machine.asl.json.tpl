{
  "Comment": "Scraper workflow (single Lambda)",
  "StartAt": "RunScraper",
  "States": {
    "RunScraper": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${lambda_arn}",
        "Payload.$": "$"
      },
      "OutputPath": "$.Payload",
      "End": true
    }
  }
}
