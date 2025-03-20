from aws_cdk import (
    aws_codebuild as codebuild,
    aws_iam as iam,
    CfnOutput,
)
from aws_cdk.aws_servicecatalog import ProductStack
from constructs import Construct


class DeltaCodeBuildProject(ProductStack):
    def __init__(self, scope: Construct, id: str, repository, project_name: str = "DeltaCodeBuildProject",
                 **kwargs) -> None:
        """
        :param repository: An instance of codecommit.Repository created by DeltaCodeCommitRepo.
        """
        super().__init__(scope, id, **kwargs)

        # Create IAM Role for CodeBuild with necessary permissions.
        codebuild_role = iam.Role(
            self, "DeltaCodeBuildServiceRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            description="IAM Role for CodeBuild with permissions to access logs, S3, ECR and CodeCommit."
        )

        # Grant permissions for logging.
        codebuild_role.add_to_policy(iam.PolicyStatement(
            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            resources=["*"]
        ))
        # Grant permissions for S3 access.
        codebuild_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject"],
            resources=["*"]
        ))
        # Grant permissions for ECR access.
        codebuild_role.add_to_policy(iam.PolicyStatement(
            actions=["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer",
                     "ecr:BatchGetImage"],
            resources=["*"]
        ))
        # Grant permissions for CodeCommit access.
        codebuild_role.add_to_policy(iam.PolicyStatement(
            actions=["codecommit:GitPull"],
            resources=["*"]
        ))

        # Create the CodeBuild project, using the provided CodeCommit repository.
        project = codebuild.Project(
            self, "DeltaCodeBuildProject",
            project_name=project_name,
            role=codebuild_role,
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.SMALL,
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged=True
            ),
            source=codebuild.Source.code_commit(
                repository=repository
            )
        )

        CfnOutput(self, "CodeBuildProjectName", value=project.project_name)
