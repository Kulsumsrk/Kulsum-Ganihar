import aws_cdk as cdk
from aws_cdk import (
    aws_ecr as ecr,
    CfnOutput,
    Duration,
)
from aws_cdk.aws_servicecatalog import ProductStack
from constructs import Construct


class DeltaECRRepository(ProductStack):
    def __init__(self, scope: Construct, id: str, repository_name: str = "delta-container-repo", **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        repository = ecr.Repository(
            self, "DeltaECRRepository",
            repository_name=repository_name,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    rule_priority=1,
                    description="Expire untagged images older than 30 days",
                    max_image_age=Duration.days(30),
                    tag_status=ecr.TagStatus.UNTAGGED
                )
            ]
        )

        CfnOutput(self, "ECRRepositoryUri", value=repository.repository_uri)
        # Export the repository if you need to reference it in other stacks.
        self.repository = repository
