"""
CertificateStack – us-east-1

CloudFront benötigt TLS-Zertifikate ZWINGEND in der Region us-east-1.
Deshalb wird dieses Zertifikat in einem separaten Stack deployed,
der explizit in us-east-1 läuft. Der Hauptstack in eu-central-1
referenziert das Zertifikat dann cross-region.
"""
from aws_cdk import (
    Stack,
    aws_certificatemanager as acm,
    aws_route53 as route53,
)
from constructs import Construct


class CertificateStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Bestehende Hosted Zone für unsere Domain suchen.
        # Die Zone wird erst existieren, nachdem cdk deploy das erste Mal
        # ausgeführt wurde UND die NS-Records beim Registrar eingetragen sind.
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name=domain_name,
        )

        # Zertifikat für Haupt-Domain + www-Subdomain
        # DNS-Validierung: CDK fügt automatisch CNAME-Records in Route53 ein
        self.certificate = acm.Certificate(
            self, "CloudFrontCertificate",
            domain_name=domain_name,
            subject_alternative_names=[f"www.{domain_name}"],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )
