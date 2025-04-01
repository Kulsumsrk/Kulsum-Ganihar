from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_codestarconnections as codestar,
    aws_s3 as s3,
)
from constructs import Construct


class CICDPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        account_id = "474532148129"
        region = "eu-west-1"
        s3_bucket_name = f"codepipeline-{region}-201242848994"
        build_project_name = "test_code_pipeline_20250328"

        # 1. Artifact Bucket
        artifact_bucket = s3.Bucket.from_bucket_name(self, "ArtifactBucket", s3_bucket_name)

        # 2. Unified IAM Role for both CodePipeline and CodeBuild
        pipeline_role = iam.Role(
            self, "PipelineUnifiedRole",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
        )

        # 3. Attach custom S3 bucket permissions
        pipeline_role.add_to_policy(iam.PolicyStatement(
            sid="AllowS3BucketAccess",
            actions=[
                "s3:GetBucketVersioning",
                "s3:GetBucketAcl",
                "s3:GetBucketLocation",
            ],
            resources=[f"arn:aws:s3:::{s3_bucket_name}"],
            conditions={"StringEquals": {"aws:ResourceAccount": "474532148129"}},
        ))

        pipeline_role.add_to_policy(iam.PolicyStatement(
            sid="AllowS3ObjectAccess",
            actions=[
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:GetObjectVersion",
            ],
            resources=[f"arn:aws:s3:::{s3_bucket_name}/*"],
            conditions={"StringEquals": {"aws:ResourceAccount": "474532148129"}},
        ))

        # 4. Attach CodeBuild permissions
        pipeline_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "codebuild:BatchGetBuilds",
                "codebuild:StartBuild",
                "codebuild:BatchGetBuildBatches",
                "codebuild:StartBuildBatch",
            ],
            resources=[f"arn:aws:codebuild:*:{account_id}:project/{build_project_name}"]
        ))

        # 5. GitLab Connection
        gitlab_connection = codestar.CfnConnection(
            self, "GitLabConnection",
            connection_name="GitLabConnection",
            provider_type="GitLab"
        )

        # 6. Pipeline Artifact
        source_output = codepipeline.Artifact()

        # 7. CodeBuild Project using same role
        build_project = codebuild.PipelineProject(
            self, "CodeBuildProject",
            project_name=build_project_name,
            build_spec=codebuild.BuildSpec.from_source_filename("../buildspec_files/buildspec.yml"),
            role=pipeline_role,  # Shared role
        )

        # 8. Pipeline
        pipeline = codepipeline.Pipeline(
            self, "CodePipeline",
            pipeline_name="GitLabToCodeBuildPipeline",
            artifact_bucket=artifact_bucket,
            role=pipeline_role,
        )

        # 9. Source Stage
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                cpactions.CodeStarConnectionsSourceAction(
                    action_name="GitLab_Source",
                    owner="your-gitlab-username",
                    repo="your-repo-name",
                    branch="main",
                    output=source_output,
                    connection_arn=gitlab_connection.attr_connection_arn,
                )
            ]
        )

        # 10. Build Stage
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                cpactions.CodeBuildAction(
                    action_name="CodeBuild",
                    input=source_output,
                    project=build_project,
                )
            ]
        )
