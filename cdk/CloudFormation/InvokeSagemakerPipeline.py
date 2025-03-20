from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    custom_resources as cr
)
import json
from constructs import Construct


class SageMakerPipelineInvokerStack(Stack):
    def __init__(self, scope: Construct, id: str, pipeline_name: str, pipeline_parameters: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # IAM Role for Lambda
        invoke_pipeline_lambda_role = iam.Role(self, "InvokePipelineLambdaRole",
                                               assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                               )
        invoke_pipeline_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["sagemaker:StartPipelineExecution"],
            resources=["*"]  # Restrict this to specific pipeline ARNs in production
        ))
        invoke_pipeline_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            resources=["*"]
        ))

        # Create a Lambda Layer with boto3 and cfnresponse
        lambda_layer = _lambda.LayerVersion(
            self,
            "LambdaLayer",
            code=_lambda.Code.from_asset("lambda_layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="Layer containing boto3 and cfnresponse"
        )

        # Lambda Function to Invoke the Pipeline
        lambda_sagemaker_pipeline_invoke = _lambda.Function(
            scope=self,
            id="lambda_sagemaker_pipeline_invoke",
            function_name='lambda_sagemaker_pipeline_invoke',
            description="Creates Datazone Domain Units",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="InvokeSagemakerPipeline.handler",
            code=_lambda.Code.from_asset("cdk/Lambda"),
            layers=[
                lambda_layer
            ],
            timeout=Duration.seconds(30),
            role=invoke_pipeline_lambda_role
        )

        lambda_payload = {
            "PipelineName": pipeline_name.value_as_string,
            "PipelineParameters": pipeline_parameters.value_as_string
        }

        print("Lambda payload", lambda_payload, type(lambda_payload))

        invoke_sagemaker_pipeline = cr.AwsCustomResource(
            scope=self,
            id="invoke_sagemaker_pipeline",
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": lambda_sagemaker_pipeline_invoke.function_name,
                    "InvocationType": "Event",
                    "Payload": json.dumps(lambda_payload)
                },
                physical_resource_id=cr.PhysicalResourceId.of("invoke_sagemaker_pipeline")
            ),
            on_update=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": lambda_sagemaker_pipeline_invoke.function_name,
                    "InvocationType": "Event",
                    "Payload": json.dumps(lambda_payload)
                },
                physical_resource_id=cr.PhysicalResourceId.of("invoke_sagemaker_pipeline")
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["lambda:InvokeFunction"],
                    resources=[lambda_sagemaker_pipeline_invoke.function_arn]
                )
            ])
        )

        # Output
        CfnOutput(self, "PipelineInvocationOutput",
                  description="Output from the pipeline invocation (check CloudWatch logs for details)",
                  value="Pipeline invoked. See CloudWatch Logs for execution details.")
