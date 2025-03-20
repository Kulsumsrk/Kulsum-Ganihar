import json
import boto3

sagemaker = boto3.client("sagemaker")


def lambda_handler(event, context):
    try:
        domain_id = event["DomainId"]
        lifecycle_config_arn = event["LifecycleConfigArn"]

        response = sagemaker.update_domain(
            DomainId=domain_id,
            DefaultUserSettings={
                "StudioLifecycleConfigArns": [lifecycle_config_arn]
            },
            DefaultSpaceSettings={
                "StudioLifecycleConfigArns": [lifecycle_config_arn]
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Domain settings updated successfully", "response": response})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
