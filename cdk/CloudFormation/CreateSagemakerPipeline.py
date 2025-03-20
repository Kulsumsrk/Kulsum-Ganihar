from aws_cdk import (
    aws_sagemaker as sagemaker,
    CfnParameter,
    Fn,
    CfnCondition,
    CfnOutput,
)
from constructs import Construct
from aws_cdk.aws_servicecatalog import ProductStack

cfn_parameters = {
    "PipelineName": {"Type": "String", "Description": "Name for the SageMaker Pipeline."},
}


class SageMakerPipelineTemplate(ProductStack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define CFN parameters
        pipeline_name_param = CfnParameter(
            self,
            "PipelineName",
            type="String",
            description="Name for the SageMaker Pipeline."
        )

        pipeline_execution_role_param = CfnParameter(
            self,
            "PipelineExecutionRoleArn",
            type="String",
            description="IAM Role ARN for the pipeline's execution."
        )

        s3_bucket_param = CfnParameter(
            self, "S3Bucket",
            type="String",
            description="S3 bucket containing the pipeline definition JSON."
        )

        s3_key_param = CfnParameter(
            self,
            "S3Key",
            type="String",
            description="S3 key (path/filename) for the pipeline definition JSON."
        )

        # Create the SageMaker Pipeline resource
        pipeline = sagemaker.CfnPipeline(
            self,
            "SageMakerPipeline",
            pipeline_name=pipeline_name_param.value_as_string,
            role_arn=pipeline_execution_role_param.value_as_string,
            pipeline_definition={
                "PipelineDefinitionS3Location": {
                    "Bucket": s3_bucket_param.value_as_string,
                    "Key": s3_key_param.value_as_string
                }
            }
        )

        # Output the pipeline name (optional)
        CfnOutput(
            self,
            "SageMakerPipelineName",
            description="Name of the created SageMaker pipeline.",
            value=pipeline.pipeline_name
        )
