terraform {
  backend "s3" {
    bucket = "backend-ga"
    key    = "state/terraform.tfstate"
    region = "us-east-1"
  }
}
