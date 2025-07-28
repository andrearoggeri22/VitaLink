# AWS Secrets Configuration for VitaLink GitHub Actions

This document describes the required secrets and their configuration for the VitaLink CI/CD workflows.

## Required GitHub Secrets

Configure these secrets in your repository settings (Settings > Secrets and variables > Actions):

### AWS Credentials
- `AWS_ACCESS_KEY_ID`: Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key  
- `AWS_SESSION_TOKEN`: Your AWS session token (for AWS Education accounts)

### Application Secrets
- `DATABASE_PASSWORD`: PostgreSQL database password (should match the one in your PowerShell script)
  - Example: `VitaLink2025!DB#Pass`

## Secret Configuration Instructions

### 1. AWS Credentials Setup

For AWS Education accounts, you need to update these credentials regularly (they expire every few hours):

```bash
# Get your current credentials from AWS Academy
aws sts get-caller-identity

# Copy the credentials from your AWS Academy session
```

### 2. GitHub Repository Setup

1. Go to your repository on GitHub
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret" for each required secret
4. Add the secrets with the exact names listed above

### 3. Environment Protection (Optional)

For production deployments, consider setting up environment protection:

1. Go to Settings > Environments
2. Create a new environment called "production"
3. Add protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches

## Security Best Practices

### Credential Rotation
- AWS Education credentials expire frequently - set up notifications
- Rotate database passwords regularly
- Use GitHub's secret scanning to detect exposed secrets

### Access Control
- Use environment protection for production deployments
- Limit repository access to authorized team members
- Enable audit logging for secret access

### Monitoring
- Set up CloudWatch alarms for unusual AWS activity
- Monitor deployment logs for security events
- Use AWS CloudTrail for API call auditing

## Workflow Triggers

The workflows are configured with these triggers:

### Build and Push (`aws-build-push.yml`)
- **Trigger automatico**: Push su `main` o `CLOUD_MOBILE_PROJECT` branches
- **Trigger automatico**: Pull requests su `main`
- **Trigger manuale**: Via `workflow_dispatch`
- **Post-build**: Automaticamente triggera il CloudFormation deployment tramite `workflow_dispatch` e `repository_dispatch`

### CloudFormation Deploy (`aws-cloudformation-deploy.yml`)
- **Trigger automatico**: Dopo successful completion del workflow "AWS ECR Build and Push" (via `workflow_run`)
- **Trigger automatico**: Via `repository_dispatch` con event type `deploy-cloudformation`
- **Trigger manuale**: Con parametri per environment e image URI
- **Dipendenze**: Richiede artifact dal workflow di build (image URI) o parametri espliciti
- **Note**: Usa `dawidd6/action-download-artifact@v3` per scaricare artifact da workflow runs precedenti
- Automatic after successful build
- Manual trigger with parameters
- Environment-specific deployments

### Infrastructure Monitoring (`aws-monitoring.yml`)
- Scheduled runs (every 30 minutes during business hours)
- Manual trigger for detailed checks

### Cleanup (`aws-cleanup.yml`)
- Manual trigger only (requires "DELETE" confirmation)
- Optional ECR repository cleanup

## Troubleshooting

### Common Issues

1. **AWS Credentials Expired**
   - Update the AWS secrets in GitHub
   - Check AWS Academy for new session credentials

2. **CloudFormation Deploy not triggering after build**
   - Verify the build workflow completed successfully
   - Check that artifact upload succeeded in build workflow
   - Ensure branch matches trigger configuration (main or CLOUD_MOBILE_PROJECT)
   - The build workflow now attempts multiple trigger methods:
     - Primary: `workflow_dispatch` to CloudFormation workflow
     - Fallback: `repository_dispatch` with `deploy-cloudformation` event
   - Use "Test Workflow Integration" workflow to debug:
     - Choose `repository_dispatch` to test the fallback method
     - Choose `workflow_dispatch` to test the primary method
     - Choose `simulate_build` to test with artifacts
   - Check the debug job output in CloudFormation Deploy workflow

3. **CloudFormation Stack Errors**
   - Check the AWS CloudFormation console for detailed error messages
   - Review the stack events in the workflow logs

4. **ECS Task Failures**
   - Check ECS service logs in CloudWatch
   - Verify the Docker image build and push succeeded

5. **Database Connection Issues**
   - Ensure the database password secret matches the deployment
   - Check RDS instance status and security groups

### Getting Help

- Check workflow run logs in GitHub Actions tab
- Review AWS CloudFormation stack events
- Monitor AWS CloudWatch logs
- Use AWS CLI for manual debugging:
  ```bash
  aws cloudformation describe-stack-events --stack-name VitaLink-Stack
  aws ecs describe-services --cluster VitaLink-Cluster-production --services vitalink-service-production
  ```

## Cost Management

### Monitoring Costs
- Set up AWS billing alerts
- Use AWS Cost Explorer to track spending
- Monitor the scheduled runs of the monitoring workflow

### Cost Optimization
- Adjust ECS task count based on usage
- Use appropriate RDS instance sizes
- Clean up resources when not needed using the cleanup workflow

## Compliance Notes

### AWS Education Limitations
- Some AWS services may not be available
- Resource limits may apply
- Credentials have shorter expiration times

### Security Compliance
- All secrets are encrypted at rest in GitHub
- AWS credentials follow least-privilege principle
- Infrastructure follows AWS security best practices
