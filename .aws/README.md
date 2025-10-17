# AWS Deployment Notes

## Profiles and Region
- Active profiles: `gentacalc` (default).
- Region for all services: `eu-north-1` (Stockholm).
- Credentials are stored in `.aws/credentials`; rotate them when sharing the project.

## Elastic Beanstalk
- Application: `gentacalc`
- Environment: `gentacalc-prod`
- Platform: `64bit Amazon Linux 2023 v4.7.3 running Python 3.11`
- CNAME: `gentacalc-no.eu-north-1.elasticbeanstalk.com`
- Latest application bundle deployed from S3 key `gentacalc-YYYYMMDDHHMMSS.zip`.
- Deployment steps:
  1. `zip -r gentacalc-<timestamp>.zip app.py wsgi.py runtime.txt requirements.txt gentacalc templates`
  2. `aws s3 cp gentacalc-<timestamp>.zip s3://gentacalc-eb-artifacts/`
  3. `aws elasticbeanstalk create-application-version --application-name gentacalc --version-label vgentacalc-<timestamp> --source-bundle S3Bucket=gentacalc-eb-artifacts,S3Key=gentacalc-<timestamp>.zip`
  4. `aws elasticbeanstalk update-environment --environment-name gentacalc-prod --version-label vgentacalc-<timestamp>`

## S3
- Artifact bucket: `gentacalc-eb-artifacts` (region `eu-north-1`).
- Stores zipped application versions consumed by Elastic Beanstalk.

## IAM Roles
- Instance role & profile: `aws-elasticbeanstalk-ec2-role` with policies `AWSElasticBeanstalkWebTier` and `AmazonS3ReadOnlyAccess`.
- Service-linked role: `AWSServiceRoleForElasticBeanstalk` (created automatically by AWS).

## SSL/TLS
- ACM certificate ARN: `arn:aws:acm:eu-north-1:656466598770:certificate/caad6c1c-46af-4fbc-abfc-becea8ac5285`
- Covers domains: `gentacalc.no`, `www.gentacalc.no`
- Validation CNAMEs (must remain in DNS for auto-renewal):
  - `_9c4a90acac4a6988e8f9f37cecae52dd.gentacalc.no -> _0273e621d496d177dbc3c0fa7f5439af.xlfgrmvvlj.acm-validations.aws`
  - `_b32e2f7976e8711ba796d88aa9dccbf9.www.gentacalc.no -> _75d5b408aac49b172ec648b6f0f5c9a5.xlfgrmvvlj.acm-validations.aws`
- HTTPS listener is enabled on the EB load balancer; HTTP remains open until redirect logic is implemented.

## DNS / Domain Notes
- Domain registrar: GoDaddy.
- `www.gentacalc.no` CNAME → `gentacalc-no.eu-north-1.elasticbeanstalk.com`.
- Apex forwarding (handled in GoDaddy) should point to `https://www.gentacalc.no`.

## Helpful Commands
- Check environment health: `aws elasticbeanstalk describe-environments --environment-name gentacalc-prod --output table`
- Tail logs: request with `aws elasticbeanstalk request-environment-info --environment-name gentacalc-prod --info-type tail` and retrieve after a short wait.
- Certificate status: `aws acm describe-certificate --certificate-arn <arn> --query 'Certificate.Status' --output text`

## To-Do / Follow-Up
- Decide whether to enforce HTTP → HTTPS redirect (e.g., via ALB listener rules or nginx platform hooks).
- Move DNS hosting to Route 53 if tighter integration is desired.
- Remove `aws_keys` and rotate the credentials when handing off the project.
