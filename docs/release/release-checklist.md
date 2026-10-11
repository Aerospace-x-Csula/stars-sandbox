# STARS Release Checklist

> **Status:** Draft. This checklist will be expanded as the release process and deployment package mature.

## Release Identification

- [ ] Release version selected
- [ ] Release scope confirmed
- [ ] Required pull requests merged
- [ ] Git release tag prepared
- [ ] Release notes prepared
- [ ] CHANGELOG updated if used by the project

## Source and Configuration

- [ ] Required source code is committed
- [ ] Required configuration is committed
- [ ] Helm charts/manifests are versioned
- [ ] Infrastructure scripts are versioned
- [ ] Required container image versions are documented
- [ ] No required configuration exists only on a developer laptop

## Security

- [ ] No passwords or tokens are committed
- [ ] Secret-handling procedure is documented
- [ ] RBAC/service-account requirements are documented
- [ ] Required privileges have been reviewed

## Deployment

- [ ] Clean deployment procedure tested
- [ ] Required prerequisites documented
- [ ] Configuration inputs documented
- [ ] Environment verification procedure tested

## Observability

- [ ] Required logs are received
- [ ] Required metrics are received
- [ ] Required traces are received where applicable
- [ ] Required dashboards load correctly
- [ ] Telemetry validation procedure passes

## Failure and Recovery Testing

- [ ] Required failure scenarios tested
- [ ] Detection verified
- [ ] Investigation procedure verified
- [ ] Remediation verified where applicable
- [ ] Post-action validation verified
- [ ] Rollback verified where applicable
- [ ] Audit evidence retained

## Documentation

- [ ] Architecture documentation is current
- [ ] Onboarding documentation is current
- [ ] Deployment documentation is current
- [ ] Troubleshooting documentation is current
- [ ] Required runbooks are current
- [ ] Known limitations are documented

## Handoff

- [ ] Operator training material prepared
- [ ] Developer/onboarding material prepared
- [ ] Final demonstration procedure tested
- [ ] Final test results packaged
- [ ] Known limitations reviewed
- [ ] Recommended next steps documented

## Final Approval

- [ ] Documentation & Release review complete
- [ ] Relevant technical sub-leads have reviewed their material
- [ ] Project Lead approval complete
