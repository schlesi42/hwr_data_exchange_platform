#!/usr/bin/env python3
"""
CDK App – Einstiegspunkt für das Deployment.

Zwei Stacks:
  1. HwrCertStack   (us-east-1) – TLS-Zertifikat für CloudFront
  2. HwrPlatformStack (eu-central-1) – alle anderen AWS-Ressourcen

Reihenfolge:
  cdk deploy --all     → deployed beide Stacks in der richtigen Reihenfolge
"""
import os
import aws_cdk as cdk

from stacks.certificate_stack import CertificateStack
from stacks.platform_stack import HwrPlatformStack

app = cdk.App()

DOMAIN = "hwr-fb2-dozierenden-portal.de"
ACCOUNT = os.environ.get("CDK_DEFAULT_ACCOUNT")

# Stack 1: TLS-Zertifikat muss in us-east-1 sein (CloudFront-Anforderung)
cert_stack = CertificateStack(
    app, "HwrCertStack",
    domain_name=DOMAIN,
    env=cdk.Environment(account=ACCOUNT, region="us-east-1"),
    # Ermöglicht Cross-Region-Referenzen (CDK v2-Feature)
    cross_region_references=True,
)

# Stack 2: Hauptstack in Frankfurt
platform_stack = HwrPlatformStack(
    app, "HwrPlatformStack",
    domain_name=DOMAIN,
    cloudfront_certificate=cert_stack.certificate,
    env=cdk.Environment(account=ACCOUNT, region="eu-central-1"),
    cross_region_references=True,
)

# Sicherstellen, dass das Zertifikat vor der Platform deployed wird
platform_stack.add_dependency(cert_stack)

app.synth()
