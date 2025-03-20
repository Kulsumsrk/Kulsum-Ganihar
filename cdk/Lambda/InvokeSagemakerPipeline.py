import json
import boto3
import cfnresponse


def handler(event, context):
    sagemaker_client = boto3.client("sagemaker")
    response_data = {}
    try:
        print(event)
        pipeline_name = event["PipelineName"]
        pipeline_parameters_str = event.get("PipelineParameters", "{}")
        try:
            pipeline_parameters = json.loads(pipeline_parameters_str)
        except Exception as e:
            pipeline_parameters = {}

        parameters_list = [{"Name": k, "Value": str(v)} for k, v in pipeline_parameters.items()]
        response = sagemaker_client.start_pipeline_execution(
            PipelineName=pipeline_name,
            PipelineParameters=parameters_list
        )
        response_data["PipelineExecutionArn"] = response.get("PipelineExecutionArn", pipeline_name)
        print("Success", response_data)
    except Exception as e:
        response_data["Message"] = str(e)
        print("Error", response_data)
