from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    CfnOutput
)
from constructs import Construct
from aws_cdk.aws_servicecatalog import ProductStack


class CreateUpdateDomainLambda(ProductStack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        # Create a Lambda Layer with boto3 and cfnresponse
        lambda_layer = _lambda.LayerVersion(
            self,
            "LambdaLayer",
            code=_lambda.Code.from_asset("libs/boto3/boto3.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            layer_version_name="boto3_1_37",
            description="Layer containing boto3 and cfnresponse"
        )

        lambda_role = iam.Role(
            self,
            "SageMakerUpdateLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ]
        )

        # **Attach inline policy for SageMaker permissions**
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "sagemaker:UpdateDomain",
                "sagemaker:DescribeDomain",
                "sagemaker:ListDomains"
            ],
            resources=["*"]  # You can restrict this to specific domain ARNs
        ))

        # **Attach CloudWatch Logs permissions**
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*:*:*"]
        ))

        # Pass domain_id and lifecycle_config_arn as environment variables
        lambda_function = _lambda.Function(
            self, "SageMakerDomainUpdateLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="UpdateSagemakerDomain.lambda_handler",
            code=_lambda.Code.from_asset("cdk/Lambda"),  # Folder containing the lambda script
            timeout=Duration.seconds(60),
            memory_size=256,
            role=lambda_role,
            layers=[lambda_layer]
        )

        CfnOutput(self, "UpdateDomainLambdaArn", value=lambda_function.function_arn)