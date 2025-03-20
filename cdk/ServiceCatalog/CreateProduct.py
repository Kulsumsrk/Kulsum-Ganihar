from aws_cdk import (
    Stack,
    aws_servicecatalog as servicecatalog,
    Fn,
)
from constructs import Construct
from aws_cdk.aws_servicecatalog import ProductStack


class ServiceCatalogProductFactory(Stack):
    def __init__(self, scope: Construct, id: str,
                 *,
                 portfolio_export_name: str,
                 product_logical_id: str,
                 product_name: str,
                 owner: str,
                 product_version_name: str,
                 product_stack: ProductStack,
                 description: str,
                 support_email: str,
                 support_url: str,
                 **kwargs) -> None:
        """
        :param portfolio_export_name: The CloudFormation export name of the portfolio ARN.
        :param product_logical_id: Unique identifier for this product within the stack.
        :param product_name: The display name for the product.
        :param owner: The owner string for the product.
        :param product_version_name: Version label (e.g., "v1").
        :param product_stack: An instance of a ProductStack that defines the CFN template for the product.
        :param description: Description of the product.
        :param support_email: Support email address.
        :param support_url: Support URL.
        """
        super().__init__(scope, id, **kwargs)

        # Import the portfolio ARN using the export name.
        imported_portfolio_arn = Fn.import_value(portfolio_export_name)

        # Import the portfolio.
        portfolio = servicecatalog.Portfolio.from_portfolio_arn(
            self,
            "ImportedPortfolio",
            portfolio_arn=imported_portfolio_arn
        )

        # Create the CloudFormation product.
        product = servicecatalog.CloudFormationProduct(
            self,
            product_logical_id,
            product_name=product_name,
            owner=owner,
            product_versions=[
                servicecatalog.CloudFormationProductVersion(
                    product_version_name=product_version_name,
                    cloud_formation_template=servicecatalog.CloudFormationTemplate.from_product_stack(
                        product_stack
                    ),
                    validate_template=True
                )
            ],
            description=description,
            support_email=support_email,
            support_url=support_url
        )

        # Add the product to the imported portfolio.
        portfolio.add_product(product)
