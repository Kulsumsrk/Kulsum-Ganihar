from aws_cdk import (
    Stack,
    CfnOutput,
    aws_servicecatalog as servicecatalog,
)
from constructs import Construct


class CreatePortfolio(Stack):
    def __init__(self, scope: Construct, id: str,
                 *,
                 export_name,
                 portfolio_logical_id,
                 portfolio_display_name,
                 portfolio_provider_name,
                 portfolio_description,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a Service Catalog Portfolio
        self.portfolio = servicecatalog.Portfolio(
            self,
            portfolio_logical_id,
            display_name=portfolio_display_name,
            provider_name=portfolio_provider_name,
            description=portfolio_description
        )

        # Export the portfolio ARN for use in other stacks
        CfnOutput(
            self,
            "PortfolioArnOutput",
            value=self.portfolio.portfolio_arn,
            export_name=export_name
        )
