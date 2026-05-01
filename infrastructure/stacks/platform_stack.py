"""
HwrPlatformStack – eu-central-1 (Frankfurt)

Dieser Stack erstellt alle AWS-Ressourcen für das Dozierenden-Portal:
  - S3:         Datei-Uploads & Frontend-Hosting
  - Cognito:    Nutzer-Authentifizierung (Login, Passwörter, Gruppen)
  - RDS:        PostgreSQL-Datenbank
  - Lambda:     Python/FastAPI Backend (Docker-Image)
  - API Gateway: HTTP-Endpunkte für das Frontend
  - CloudFront: CDN für das Frontend (TLS/HTTPS)
  - Route53:    DNS-Einträge
  - SES:        E-Mail-Versand
  - EventBridge: Geplante Jobs (Reminder)
"""
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_cognito as cognito,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_ses as ses,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class HwrPlatformStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str,
        cloudfront_certificate,  # acm.ICertificate aus CertificateStack
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.domain_name = domain_name

        # ------------------------------------------------------------------ #
        #  DNS: Hosted Zone                                                    #
        # ------------------------------------------------------------------ #
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name=domain_name,
        )

        # ------------------------------------------------------------------ #
        #  TLS-Zertifikat (eu-central-1) – für API Gateway Custom Domain      #
        # ------------------------------------------------------------------ #
        api_certificate = acm.Certificate(
            self, "ApiCertificate",
            domain_name=f"api.{domain_name}",
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # ------------------------------------------------------------------ #
        #  S3: Bucket für hochgeladene Dokumente (Dozenten-Uploads)           #
        # ------------------------------------------------------------------ #
        uploads_bucket = s3.Bucket(
            self, "UploadsBucket",
            # Kein öffentlicher Zugriff – Dateien nur per signierter URL
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            # Versionierung = gelöschte Dateien wiederherstellbar
            versioned=True,
            # Ablauf: nach 1 Jahr alte Versionen löschen (Kosten sparen)
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(365),
                )
            ],
            removal_policy=RemovalPolicy.RETAIN,  # Bucket bleibt bei cdk destroy
        )

        # ------------------------------------------------------------------ #
        #  S3: Bucket für React-Frontend (statische Dateien)                  #
        # ------------------------------------------------------------------ #
        website_bucket = s3.Bucket(
            self, "WebsiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ------------------------------------------------------------------ #
        #  Cognito: User Pool (Nutzerverwaltung & Login)                      #
        # ------------------------------------------------------------------ #
        user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="hwr-dozierenden-portal",
            # Nutzer können sich NICHT selbst registrieren –
            # nur Admins können Nutzer anlegen
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=10,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
                temp_password_validity=Duration.days(7),
            ),
            # E-Mail-Templates für Einladungen (Cognito Standard)
            user_invitation=cognito.UserInvitationConfig(
                email_subject="Einladung zum HWR Dozierenden-Portal",
                email_body=(
                    "Hallo {username},\n\n"
                    "Sie wurden zum HWR Dozierenden-Portal eingeladen.\n\n"
                    "Ihr temporäres Passwort lautet: {####}\n\n"
                    "Bitte melden Sie sich unter https://" + domain_name +
                    " an und vergeben Sie ein neues Passwort.\n\n"
                    "Mit freundlichen Grüßen\nIhr Fachbereichsbüro"
                ),
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                fullname=cognito.StandardAttribute(required=False, mutable=True),
            ),
            # Benutzerdefiniertes Attribut: Fachbereich-ID
            custom_attributes={
                "department_id": cognito.StringAttribute(mutable=True),
                "role": cognito.StringAttribute(mutable=True),
            },
            removal_policy=RemovalPolicy.RETAIN,
        )

        # App Client – wird vom React-Frontend genutzt
        user_pool_client = user_pool.add_client(
            "WebClient",
            user_pool_client_name="hwr-web-client",
            auth_flows=cognito.AuthFlow(
                user_srp=True,      # Standard Passwort-Auth
                user_password=True, # Einfache Passwort-Auth (für Admin-SDK)
            ),
            # Kein Client-Secret (für Browser-Apps nicht geeignet)
            generate_secret=False,
            access_token_validity=Duration.hours(8),
            id_token_validity=Duration.hours(8),
            refresh_token_validity=Duration.days(30),
        )

        # Gruppen definieren
        for group_name, description in [
            ("admin", "Platform-Administratoren – sehen alles"),
            ("buero", "Fachbereichsbüros – stellen Anforderungen"),
            ("dozent", "Dozierende – liefern Dokumente"),
        ]:
            cognito.CfnUserPoolGroup(
                self, f"Group{group_name.capitalize()}",
                user_pool_id=user_pool.user_pool_id,
                group_name=group_name,
                description=description,
            )

        # ------------------------------------------------------------------ #
        #  RDS: PostgreSQL-Datenbank                                          #
        # ------------------------------------------------------------------ #
        # HINWEIS: Wir verzichten auf eine VPC für Lambda/RDS,
        # um die Kosten für ein NAT-Gateway (~32€/Monat) zu sparen.
        # RDS ist öffentlich erreichbar, aber SSL-verschlüsselt und
        # passwortgeschützt. Für eine höhere Sicherheitsstufe kann
        # später auf VPC + NAT Gateway umgestellt werden.

        db_security_group = ec2.SecurityGroup(
            self, "DbSecurityGroup",
            vpc=ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True),
            description="RDS PostgreSQL – Zugriff nur über SSL",
            allow_all_outbound=False,
        )
        # Port 5432 von überall erlauben (Schutz durch Passwort + SSL)
        # TODO: Auf spezifische IP-Ranges einschränken wenn möglich
        db_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(5432),
            "PostgreSQL Zugriff",
        )

        db_instance = rds.DatabaseInstance(
            self, "Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            vpc=ec2.Vpc.from_lookup(self, "DefaultVpc2", is_default=True),
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_groups=[db_security_group],
            publicly_accessible=True,
            # Zugangsdaten werden automatisch in Secrets Manager gespeichert
            credentials=rds.Credentials.from_generated_secret("hwrdbadmin"),
            database_name="hwrportal",
            allocated_storage=20,           # GB – reicht für diese Anwendung
            max_allocated_storage=100,      # Auto-Scaling bis 100 GB
            backup_retention=Duration.days(7),  # 7 Tage Backups
            deletion_protection=True,       # Verhindert versehentliches Löschen
            removal_policy=RemovalPolicy.RETAIN,
            # Performance Insights für Datenbankanalyse (kostenlos für t3.micro)
            enable_performance_insights=True,
        )

        # ------------------------------------------------------------------ #
        #  IAM: Rolle für Lambda-Funktionen                                   #
        # ------------------------------------------------------------------ #
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # S3-Zugriff (Uploads lesen/schreiben)
        uploads_bucket.grant_read_write(lambda_role)

        # Cognito Admin-Operationen (Nutzer anlegen, in Gruppen einteilen)
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminAddUserToGroup",
                "cognito-idp:AdminGetUser",
                "cognito-idp:ListUsers",
                "cognito-idp:AdminUpdateUserAttributes",
            ],
            resources=[user_pool.user_pool_arn],
        ))

        # SES E-Mail-Versand
        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["ses:SendEmail", "ses:SendTemplatedEmail"],
            resources=["*"],
        ))

        # Datenbank-Zugangsdaten aus Secrets Manager lesen
        db_instance.secret.grant_read(lambda_role)

        # ------------------------------------------------------------------ #
        #  Lambda: FastAPI Backend (Docker-Image)                             #
        # ------------------------------------------------------------------ #
        # CDK baut das Docker-Image lokal und pusht es automatisch nach ECR.
        # Das erfordert, dass Docker beim Deployment läuft.
        backend_image = lambda_.DockerImageCode.from_image_asset(
            "../backend",
        )

        common_env = {
            "DB_SECRET_ARN": db_instance.secret.secret_arn,
            "DB_HOST": db_instance.db_instance_endpoint_address,
            "DB_PORT": db_instance.db_instance_endpoint_port,
            "DB_NAME": "hwrportal",
            "S3_UPLOADS_BUCKET": uploads_bucket.bucket_name,
            "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
            "COGNITO_CLIENT_ID": user_pool_client.user_pool_client_id,
            "AWS_REGION_NAME": self.region,
            "DOMAIN": domain_name,
            "FRONTEND_URL": f"https://{domain_name}",
        }

        backend_lambda = lambda_.DockerImageFunction(
            self, "BackendLambda",
            code=backend_image,
            role=lambda_role,
            environment=common_env,
            timeout=Duration.seconds(30),
            memory_size=512,
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        # ------------------------------------------------------------------ #
        #  Lambda: Reminder-Job (täglich per EventBridge ausgelöst)           #
        # ------------------------------------------------------------------ #
        reminder_lambda = lambda_.DockerImageFunction(
            self, "ReminderLambda",
            # Selbes Docker-Image, anderer Einstiegspunkt
            code=lambda_.DockerImageCode.from_image_asset(
                "../backend",
                cmd=["app.reminder.handler"],
            ),
            role=lambda_role,
            environment=common_env,
            timeout=Duration.minutes(5),
            memory_size=256,
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        # EventBridge: täglich um 08:00 UTC (= 09:00/10:00 Berliner Zeit)
        reminder_schedule = events.Rule(
            self, "ReminderSchedule",
            schedule=events.Schedule.cron(hour="8", minute="0"),
            description="Täglich Deadlines prüfen und Erinnerungen versenden",
        )
        reminder_schedule.add_target(
            events_targets.LambdaFunction(reminder_lambda)
        )

        # ------------------------------------------------------------------ #
        #  API Gateway: HTTP-API vor dem Backend-Lambda                       #
        # ------------------------------------------------------------------ #
        api = apigw.RestApi(
            self, "Api",
            rest_api_name="hwr-dozierenden-portal-api",
            description="REST API für das HWR Dozierenden-Portal",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=[f"https://{domain_name}"],
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            ),
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                logging_level=apigw.MethodLoggingLevel.INFO,
            ),
        )

        # Alle Requests an Lambda weiterleiten (Proxy-Integration)
        backend_integration = apigw.LambdaIntegration(
            backend_lambda, proxy=True
        )
        proxy_resource = api.root.add_resource("{proxy+}")
        proxy_resource.add_method("ANY", backend_integration)
        api.root.add_method("ANY", backend_integration)

        # API Gateway Custom Domain
        api_domain = apigw.DomainName(
            self, "ApiDomain",
            domain_name=f"api.{domain_name}",
            certificate=api_certificate,
            endpoint_type=apigw.EndpointType.REGIONAL,
        )
        apigw.BasePathMapping(
            self, "ApiMapping",
            domain_name=api_domain,
            rest_api=api,
        )

        # ------------------------------------------------------------------ #
        #  CloudFront: CDN für React-Frontend                                 #
        # ------------------------------------------------------------------ #
        # Origin Access Control: CloudFront darf auf den S3-Bucket zugreifen,
        # aber S3 ist nicht direkt öffentlich zugänglich.
        oac = cloudfront.S3OriginAccessControl(self, "OAC")

        s3_origin = origins.S3BucketOrigin.with_origin_access_control(
            website_bucket,
            origin_access_control=oac,
        )

        distribution = cloudfront.Distribution(
            self, "WebDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            domain_names=[domain_name, f"www.{domain_name}"],
            certificate=cloudfront_certificate,  # aus CertificateStack (us-east-1)
            # React Router: alle 404s → index.html
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
            default_root_object="index.html",
        )

        # ------------------------------------------------------------------ #
        #  Route53: DNS-Einträge                                              #
        # ------------------------------------------------------------------ #
        # Frontend → CloudFront
        route53.ARecord(
            self, "FrontendARecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution)
            ),
        )
        route53.ARecord(
            self, "FrontendWwwARecord",
            zone=hosted_zone,
            record_name="www",
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(distribution)
            ),
        )

        # API → API Gateway
        route53.ARecord(
            self, "ApiARecord",
            zone=hosted_zone,
            record_name="api",
            target=route53.RecordTarget.from_alias(
                route53_targets.ApiGatewayDomain(api_domain)
            ),
        )

        # ------------------------------------------------------------------ #
        #  SES: E-Mail-Domain verifizieren                                    #
        # ------------------------------------------------------------------ #
        ses_identity = ses.EmailIdentity(
            self, "SesIdentity",
            identity=ses.Identity.domain(domain_name),
            # CDK fügt DKIM-Records automatisch in Route53 ein
            mail_from_domain=f"mail.{domain_name}",
        )

        # ------------------------------------------------------------------ #
        #  Outputs: Wichtige Werte nach dem Deployment anzeigen               #
        # ------------------------------------------------------------------ #
        CfnOutput(self, "FrontendUrl",
            value=f"https://{domain_name}",
            description="URL des Frontends")

        CfnOutput(self, "ApiUrl",
            value=f"https://api.{domain_name}",
            description="URL der REST API")

        CfnOutput(self, "CognitoUserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID (für Frontend-Konfiguration)")

        CfnOutput(self, "CognitoClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito App Client ID (für Frontend-Konfiguration)")

        CfnOutput(self, "UploadsBucketName",
            value=uploads_bucket.bucket_name,
            description="S3 Bucket für Uploads")

        CfnOutput(self, "WebsiteBucketName",
            value=website_bucket.bucket_name,
            description="S3 Bucket für Frontend-Dateien")

        CfnOutput(self, "CloudFrontDistributionId",
            value=distribution.distribution_id,
            description="CloudFront Distribution ID (für Cache-Invalidierung)")

        CfnOutput(self, "DbSecretArn",
            value=db_instance.secret.secret_arn,
            description="ARN des DB-Secrets in Secrets Manager")
