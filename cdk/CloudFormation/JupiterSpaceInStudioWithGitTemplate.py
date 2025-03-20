import textwrap
from aws_cdk import (
    CfnParameter,
    CfnOutput,
    Fn,
    aws_lambda as _lambda,
    aws_iam as iam,
    custom_resources as cr,
    Duration
)
import json
from constructs import Construct
from aws_cdk import aws_sagemaker as sagemaker
from aws_cdk.aws_servicecatalog import ProductStack


class JupiterSpaceInStudioWithGitTemplate(ProductStack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Define parameters dynamically
        param_definitions = {
            "DomainId": {"type": "String", "description": "SageMaker Studio Domain ID"},
            "ProjectName": {"type": "String",
                            "description": "Folder name inside Jupyter Space for the DataZone project"},
            "RemoteRepoUrl": {"type": "String", "description": "SSH/HTTPS Git repository URL"},
            "GitAuthMethod": {"type": "String", "description": "Authentication method for Git (SSH or HTTPS)",
                              "default": "SSH"},
            "GitUsername": {"type": "String", "description": "Git Username (only for HTTPS)", "default": ""},
            "GitPassword": {"type": "String", "description": "Git Password (only for HTTPS)", "default": "",
                            "no_echo": True},
            "ComputeType": {"type": "String", "description": "SageMaker instance type for JupyterLab Space",
                            "default": "ml.t3.medium"},
            "StorageSizeGB": {"type": "Number", "description": "Storage size in GB", "default": 5},
            "SharingType": {"type": "String", "description": "Specifies the sharing type of the space.",
                            "default": "Shared"},
            "OwnerUserProfileName": {"type": "String", "description": "SageMaker Studio User Profile Name"}
        }

        # Create parameters dynamically. Their names will be used in Fn.sub substitution.
        parameters = {
            key: CfnParameter(self, key,
                              type=value["type"],
                              description=value["description"],
                              default=value.get("default"),
                              no_echo=value.get("no_echo", False)
                              ).value_as_string
            for key, value in param_definitions.items()
        }

        # Updated Lifecycle Script with idempotency checks
        raw_lifecycle_script = textwrap.dedent("""\
            #!/bin/bash
            set -e

            PROJECT_PATH="/home/sagemaker-user/${ProjectName}"
            LOG_FILE="/home/sagemaker-user/setup_log.txt"

            # Create project directory if it doesn't exist
            mkdir -p $PROJECT_PATH
            cd $PROJECT_PATH

            # Initialize git repo only if .git doesn't exist
            if [ ! -d ".git" ]; then
                git init
            fi

            # Add remote origin only if not already added
            if ! git remote | grep -q "^origin$"; then
                git remote add origin ${RemoteRepoUrl}
            fi

            # For SSH, add key if not already added (optional check can be implemented if needed)
            if [ "${GitAuthMethod}" = "SSH" ]; then
                eval "$(ssh-agent -s)"
                [ -f "/home/sagemaker-user/.ssh/id_rsa" ] && ssh-add /home/sagemaker-user/.ssh/id_rsa
                # Update remote URL in case it has changed
                git remote set-url origin ${RemoteRepoUrl}
            elif [ "${GitAuthMethod}" = "HTTPS" ]; then
                git config --global credential.helper store
                echo "https://${GitUsername}:${GitPassword}@${RemoteRepoUrl}" > ~/.git-credentials
                chmod 600 ~/.git-credentials
            fi

            # Set Git configuration if not already set
            if ! git config --global user.email > /dev/null; then
                git config --global user.email "syeda.ganihar@xebia.com"
            fi
            if ! git config --global user.name > /dev/null; then
                git config --global user.name "Kulsum"
            fi

            # Create or update README file idempotently
            if [ ! -f "README.md" ]; then
                echo "# ${ProjectName} Repository" > README.md
                echo "This repository is initialized as part of SageMaker Jupyter Space provisioning." >> README.md
                git add README.md
                git commit -m "Initial commit with README"
                git branch -M main
                git push -u origin main || echo "Git push failed."
            else
                echo "README.md already exists. Skipping initial commit."
            fi
        """)

        # Use Fn.sub with an explicit mapping to substitute parameters at deploy time.
        substituted_script = Fn.sub(raw_lifecycle_script, {
            "ProjectName": parameters["ProjectName"],
            "RemoteRepoUrl": parameters["RemoteRepoUrl"],
            "GitAuthMethod": parameters["GitAuthMethod"],
            "GitUsername": parameters["GitUsername"],
            "GitPassword": parameters["GitPassword"]
        })
        encoded_script = Fn.base64(substituted_script)

        # AWS SageMaker Lifecycle Configuration
        lifecycle_config = sagemaker.CfnStudioLifecycleConfig(
            self,
            "SageMakerLifecycleConfig",
            studio_lifecycle_config_app_type="JupyterLab",
            studio_lifecycle_config_name=Fn.sub("${ProjectName}-LifecycleConfig"),
            studio_lifecycle_config_content=encoded_script
        )

        # Create the SageMaker Studio JupyterLab Space
        sagemaker_space = sagemaker.CfnSpace(
            self,
            "SageMakerJupyterSpace",
            domain_id=parameters["DomainId"],
            space_name=parameters["ProjectName"] + "-" + parameters["OwnerUserProfileName"] + "- V1",
            space_display_name=parameters["ProjectName"] + "-" + parameters["OwnerUserProfileName"] + "- V1",
            space_settings=sagemaker.CfnSpace.SpaceSettingsProperty(
                app_type="JupyterLab",
                jupyter_lab_app_settings=sagemaker.CfnSpace.SpaceJupyterLabAppSettingsProperty(
                    default_resource_spec=sagemaker.CfnSpace.ResourceSpecProperty(
                        instance_type=parameters["ComputeType"],
                        lifecycle_config_arn=lifecycle_config.attr_studio_lifecycle_config_arn,
                        sage_maker_image_arn="arn:aws:sagemaker:eu-west-1:819792524951:image/sagemaker-distribution-cpu"
                    )
                ),
                jupyter_server_app_settings=sagemaker.CfnSpace.JupyterServerAppSettingsProperty(
                    default_resource_spec=sagemaker.CfnSpace.ResourceSpecProperty(
                        instance_type="system",  # SageMaker Spaces require "system"
                        lifecycle_config_arn=lifecycle_config.attr_studio_lifecycle_config_arn,
                        sage_maker_image_arn="arn:aws:sagemaker:eu-west-1:470317259841:image/jupyter-server-3"
                    ),
                    lifecycle_config_arns=[lifecycle_config.attr_studio_lifecycle_config_arn]
                ),
                space_storage_settings=sagemaker.CfnSpace.SpaceStorageSettingsProperty(
                    ebs_storage_settings=sagemaker.CfnSpace.EbsStorageSettingsProperty(
                        ebs_volume_size_in_gb=5
                    )
                )
            ),
            space_sharing_settings=sagemaker.CfnSpace.SpaceSharingSettingsProperty(
                sharing_type=parameters["SharingType"]
            ),
            ownership_settings=sagemaker.CfnSpace.OwnershipSettingsProperty(
                owner_user_profile_name=parameters["OwnerUserProfileName"]
            )
        )

        sagemaker_space.add_dependency(lifecycle_config)

        # Create a Lambda Layer with boto3 and cfnresponse
        # lambda_layer = _lambda.LayerVersion(
        #     self,
        #     "LambdaLayer",
        #     code=_lambda.Code.from_asset("libs/boto3/boto3.zip"),
        #     compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
        #     description="Layer containing boto3 and cfnresponse"
        # )

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
            role=lambda_role
            # layers=[lambda_layer]
        )

        lambda_payload = {
            "DomainId": parameters["DomainId"],
            "LifecycleConfigArn": lifecycle_config.attr_studio_lifecycle_config_arn
        }

        # Custom Resource to invoke Lambda
        update_domain_custom_resource = cr.AwsCustomResource(
            self, "UpdateSageMakerDomain",
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["lambda:InvokeFunction"],
                    resources=[lambda_function.function_arn]
                )
            ]),
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": lambda_function.function_name,
                    "InvocationType": "Event",
                    "Payload": json.dumps(lambda_payload)
                },
                physical_resource_id=cr.PhysicalResourceId.of("UpdateSageMakerDomainOnCreate")
            ),
            on_update=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": lambda_function.function_name,
                    "InvocationType": "Event",
                    "Payload": json.dumps(lambda_payload)
                },
                physical_resource_id=cr.PhysicalResourceId.of("UpdateSageMakerDomainOnUpdate")
            )
        )

        # Outputs
        CfnOutput(self, "UpdateDomainLambdaArn", value=lambda_function.function_arn)
        CfnOutput(self, "UpdateDomainCustomResource", value=update_domain_custom_resource.node.path)
        CfnOutput(self, "SageMakerJupyterSpaceName", value=sagemaker_space.space_name)
