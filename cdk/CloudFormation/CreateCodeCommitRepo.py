from aws_cdk import (
    aws_codecommit as codecommit,
    CfnOutput,
)
from aws_cdk.aws_servicecatalog import ProductStack
from constructs import Construct


class DeltaCodeCommitRepo(ProductStack):
    def __init__(self, scope: Construct, id: str, repository_name: str = "DeltaCodeCommitRepo", **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        repo = codecommit.Repository(
            self, "DeltaCodeCommitRepo",
            repository_name=repository_name,
            description="Delta repository for source code management."
        )

        CfnOutput(self, "CodeCommitRepositoryCloneUrl", value=repo.repository_clone_url_http)
        # Export the repository instance so that it can be passed to the CodeBuild project.
        self.repository = repo
