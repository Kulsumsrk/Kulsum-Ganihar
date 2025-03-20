import os
import json
from aws_cdk import App, Environment, Stack, Fn
from cdk.ServiceCatalog.CreatePortfolio import CreatePortfolio
from cdk.CloudFormation.CreateECRRepo import DeltaECRRepository
from cdk.CloudFormation.CreateCodeCommitRepo import DeltaCodeCommitRepo
from cdk.ServiceCatalog.CreateProduct import ServiceCatalogProductFactory
from cdk.CloudFormation.CreateCodeBuildProject import DeltaCodeBuildProject
from cdk.CloudFormation.CreateSagemakerPipeline import SageMakerPipelineTemplate
from cdk.CloudFormation.JupiterSpaceInStudioWithGitTemplate import JupiterSpaceInStudioWithGitTemplate
from cdk.CloudFormation.InvokeSagemakerPipeline import SageMakerPipelineInvokerStack

app = App()
env = Environment(account="474532148129", region="eu-west-1")


# =====================================================================
# IMPORTANT NOTE:
#
# ProductStack objects (stacks that extend ProductStack) must be defined
# within the scope of a non-product stack (or top-level App). This is a
# requirement of AWS Service Catalog and the CDK's product stack design.
#
# In our solution, we create a regular (non-product) parent stack called
# "ProductTemplates". All of our product stacks (e.g. SageMakerPipelineTemplate,
# DeltaECRRepository, etc.) are created as children of this parent stack.
#
# This approach ensures that when we reference these product stacks in our
# Service Catalog product factory (ServiceCatalogProductFactory), they have a
# valid non-product parent context. Without this structure, you'll encounter
# runtime errors like "Product stacks must be defined within scope of another
# non-product stack".
#
# Additionally, we create the Service Catalog products as separate top-level
# stacks (or they could also be children of App) and pass in references to the
# product stacks created under the "ProductTemplates" stack.
# =====================================================================

# Create a parent regular stack to hold all our product template stacks.
class ProductTemplates(Stack):
    pass


product_templates_stack = ProductTemplates(app, "ProductTemplates", env=env)

# =====================================================================
# Create individual product stacks as children of our non-product parent.
#
# By instantiating these product stacks under "ProductTemplates", we ensure
# that they meet the requirements of being defined in a non-product context.
#
# Each product stack defines the CloudFormation template for a particular
# Service Catalog product (e.g., a SageMaker pipeline, an ECR repository, etc.).
# =====================================================================

# Now create your product stacks as children of the non-product stack.
"""sagemaker_pipeline_product_stack = SageMakerPipelineTemplate(product_templates_stack, "SageMakerPipelineTemplate")
ecr_repo_product_stack = DeltaECRRepository(product_templates_stack, "DeltaECRRepo")
codecommit_repo_product_stack = DeltaCodeCommitRepo(product_templates_stack, "DeltaCodeCommitRepo")
codebuild_project_product_stack = DeltaCodeBuildProject(product_templates_stack, "DeltaCodeBuildProject",
                                                        repository=codecommit_repo_product_stack.repository)"""
jupiter_space_setup_product_stack = JupiterSpaceInStudioWithGitTemplate(product_templates_stack,
                                                                        "JupiterSpaceInStudioProduct")
"""
# =====================================================================
# Create portfolios.
#
# We create two separate portfolios to group our products logically.
# One for SageMaker products and one for MLOps integration tools.
# Each portfolio is exported using a CloudFormation output so that it can
# be referenced later when creating Service Catalog products.
# =====================================================================

# Creates a portfolio for Sagemaker products
CreatePortfolio(
    app,
    "SagemakerPipelineServiceCatalog",
    env=env,
    export_name="SagemakerPipelinePortfolioArn",
    portfolio_logical_id="Sagemaker Pipeline",
    portfolio_display_name="CDK - Sagemaker Pipeline",
    portfolio_provider_name="Kulsum",
    portfolio_description="A portfolio for Sagemaker products",
)

# Creates a portfolio for MLOPs integration tools products
CreatePortfolio(
    app,
    "MLOpsIntegrationToolsServiceCatalog",
    env=env,
    export_name="MLOpsIntegrationToolsPortfolioArn",
    portfolio_logical_id="MLOps Integration tools Pipeline",
    portfolio_display_name="CDK - MLOps Integration tools Pipeline",
    portfolio_provider_name="Kulsum",
    portfolio_description="A portfolio for MLOps Integration tools products",
)

# Creates a portfolio for well setup Jupiter space
CreatePortfolio(
    app,
    "SetupJupiterSpaceServiceCatalog",
    env=env,
    export_name="SetupJupiterSpacePortfolioArn",
    portfolio_logical_id="Setup Jupiter Space Pipeline",
    portfolio_display_name="CDK - Setup Jupiter Space Pipeline",
    portfolio_provider_name="Kulsum",
    portfolio_description="A portfolio for setting up Jupiter Space products",
)

# Creates Sagemaker pipeline
ServiceCatalogProductFactory(
    app,
    "MLOpsSageMakerPipelineProductStack",
    env=env,
    portfolio_export_name="SagemakerPipelinePortfolioArn",  # CloudFormation export name of your portfolio ARN.
    product_logical_id="CDK-SagemakerPipelineCreation",
    product_name="CDK - Sagemaker Pipeline Creation",
    owner="Kulsum",
    product_version_name="v1",
    product_stack=sagemaker_pipeline_product_stack,
    # Instance of your ProductStack subclass.
    description="SageMaker Pipeline provisioning Product",
    support_email="Syeda.Ganihgar@xebia.com",
    support_url="https://aws.amazon.com/servicecatalog/"
)

# =====================================================================
# Create Service Catalog products using a reusable factory.
#
# The ServiceCatalogProductFactory is a parameterized construct that allows
# you to create a Service Catalog product by passing in:
#   - The portfolio export name (to import the correct portfolio)
#   - Unique product identifiers and names
#   - The product template (a ProductStack instance) that defines the CFN
#     template for the product.
#
# We use our previously defined product stacks (which are children of the
# ProductTemplates stack) and pass them to the factory. This allows us to
# create multiple products (for SageMaker, ECR, CodeCommit, CodeBuild, etc.)
# in a consistent, reusable manner.
# =====================================================================

# Creates ECR Repo
ServiceCatalogProductFactory(
    app,
    "MLOpsECRRepoProductStack",
    env=env,
    portfolio_export_name="MLOpsIntegrationToolsPortfolioArn",  # CloudFormation export name of your portfolio ARN.
    product_logical_id="CDK-ECRRepoCreation",
    product_name="CDK - ECR Repo Creation",
    owner="Kulsum",
    product_version_name="v1",
    product_stack=ecr_repo_product_stack,
    # Instance of your ProductStack subclass.
    description="ECR Repository provisioning Product",
    support_email="Syeda.Ganihgar@xebia.com",
    support_url="https://aws.amazon.com/servicecatalog/"
)

# Creates CodeCommit Repo
ServiceCatalogProductFactory(
    app,
    "MLOpsCodeCommitRepoProductStack",
    env=env,
    portfolio_export_name="MLOpsIntegrationToolsPortfolioArn",  # CloudFormation export name of your portfolio ARN.
    product_logical_id="CDK-CodeCommitRepoCreation",
    product_name="CDK - CodeCommit Repo Creation",
    owner="Kulsum",
    product_version_name="v1",
    product_stack=codecommit_repo_product_stack,
    # Instance of your ProductStack subclass.
    description="CodeCommit Repository provisioning Product",
    support_email="Syeda.Ganihgar@xebia.com",
    support_url="https://aws.amazon.com/servicecatalog/"
)

# Creates CodeBuild Repo
ServiceCatalogProductFactory(
    app,
    "MLOpsCodeBuildProjectProductStack",
    env=env,
    portfolio_export_name="MLOpsIntegrationToolsPortfolioArn",  # CloudFormation export name of your portfolio ARN.
    product_logical_id="CDK-CodeBuildProjectCreation",
    product_name="CDK - CodeBuild Project Creation",
    owner="Kulsum",
    product_version_name="v1",
    product_stack=codebuild_project_product_stack,
    # Instance of your ProductStack subclass.
    description="CodeBuild Project provisioning Product",
    support_email="Syeda.Ganihgar@xebia.com",
    support_url="https://aws.amazon.com/servicecatalog/"
)"""

#  Provision a product that creates new SageMaker Studio user profile (a "Jupiter Space") and its associated lifecycle
#  configuration with Git initialization.

ServiceCatalogProductFactory(
    app,
    "SetupJupiterSpaceProductStack-v1",
    env=env,
    portfolio_export_name="SetupJupiterSpacePortfolioArn",  # CloudFormation export name of your portfolio ARN.
    product_logical_id="CDK-SetupJupiterSpaceCreation",
    product_name="CDK - Setup Jupiter Space Creation",
    owner="Kulsum",
    product_version_name="v1",
    product_stack=jupiter_space_setup_product_stack,
    # Instance of your ProductStack subclass.
    description="Jupiter Space provisioning Product",
    support_email="Syeda.Ganihgar@xebia.com",
    support_url="https://aws.amazon.com/servicecatalog/"
)

# Load pipeline parameters from config file
CONFIG_FILE = "pipeline-config.json"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config_data = json.load(f)
    pipeline_parameters = json.dumps(config_data.get("PipelineParameters", {}))  # Convert to JSON string
else:
    pipeline_parameters = "{}"  # Default empty JSON string

app = App()

# Read PipelineName from environment variables (passed from Git pipeline)
pipeline_name = app.node.try_get_context("PipelineName")

# Deploy stack
SageMakerPipelineInvokerStack(
    app, "SageMakerPipelineInvokerStack",
    pipeline_name=pipeline_name,
    pipeline_parameters=pipeline_parameters
)
app.synth()
