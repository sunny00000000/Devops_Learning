# Billinger DevOps Bot — Exact Command and Scenario Coverage

Release: **2.0.1**

## Important scope statement

This is a broad, structured DevOps curriculum, not every command or every company-specific situation in existence. Commands and practices vary by operating system, product version, cloud, organization, policy, and job role.

Learning examples are intentionally broader than the Safe Real Lab execution allowlist. Some examples teach production concepts or configuration syntax but are not executed against the host computer.

## Bundled content totals

- **Domains:** 21
- **Levels:** 84
- **Lessons:** 336
- **Practice Labs:** 84
- **Command Examples:** 336
- **Unique Command Examples:** 296
- **Test Questions:** 255
- **Interview Questions:** 341
- **Company Tickets:** 84
- **Incidents:** 21
- **Capstones:** 21

## Safe Real Lab execution boundary

Learning examples are wider than executable Safe Lab commands. The Safe Lab intentionally executes only a restricted allowlist; destructive, privileged, remote, and host-administration operations are blocked.

### Allowed executable names

`ansible`, `ansible-config`, `ansible-doc`, `cat`, `date`, `dir`, `docker`, `echo`, `find`, `git`, `grep`, `head`, `hostname`, `kubectl`, `ls`, `mkdir`, `pwd`, `py`, `python`, `sort`, `tail`, `terraform`, `touch`, `tree`, `type`, `uniq`, `wc`, `where`, `whoami`

### Restricted subcommands

- **ansible:** `--version`, `config`, `doc`, `inventory`, `version`
- **ansible-config:** `dump`, `list`, `view`
- **ansible-doc:** `--list`, `--version`
- **docker:** `images`, `info`, `inspect`, `logs`, `ps`, `stats`, `version`
- **git:** `branch`, `diff`, `log`, `remote`, `rev-parse`, `show`, `status`
- **kubectl:** `api-resources`, `cluster-info`, `config`, `describe`, `explain`, `get`, `logs`, `top`, `version`
- **py:** `--version`, `-V`
- **python:** `--version`, `-V`
- **terraform:** `fmt`, `graph`, `output`, `providers`, `show`, `validate`, `version`

## 🖥️ Linux Administration

**Category:** Foundations  
**Included:** 16 lessons, 4 practice labs, 16 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Operate, secure, troubleshoot, and automate Linux servers used by engineering teams.

**Company relevance:** Most cloud workloads, containers, CI runners, and production services run on Linux. DevOps engineers must understand processes, filesystems, services, permissions, logs, packages, and performance.

### Command and configuration examples

- `auditctl -l`
- `cd /var/log`
- `chmod 640 file`
- `df -h`
- `du -sh /var/log/*`
- `findmnt`
- `iostat -xz 1`
- `journalctl -u nginx --since "30 min ago"`
- `ls -lah`
- `pwd`
- `sar -u 1 5`
- `ss -tulpn`
- `sysctl -a`
- `systemd-analyze blame`
- `top`
- `vmstat 1`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer receives a ticket, connects to a non-production server, inspects the filesystem, applies an approved package or permission change, validates the service, and records evidence.

**Lessons:** Terminal Navigation; Files And Directories; Permissions And Ownership; Packages And Processes

- **linux-lab-1 — Beginner company lab:** Prepare a web-service account, directory structure, permissions, and a service health report.

#### Intermediate

**Company workflow:** An engineer handles an alert by checking service state, reading recent logs, validating listening ports, confirming disk space, applying a reversible fix, and updating the incident ticket.

**Lessons:** Systemd Services; Journald And Log Analysis; Storage And Mounts; Network Diagnostics

- **linux-lab-2 — Intermediate company lab:** Troubleshoot a simulated service outage caused by a full filesystem and incorrect service configuration.

#### Advanced

**Company workflow:** A senior engineer reviews baseline metrics, identifies a bottleneck, tests changes in staging, uses configuration control, implements backup validation, and creates a rollback plan.

**Lessons:** Performance Tuning; Security Hardening; Backup And Recovery; Shell Automation

- **linux-lab-3 — Advanced company lab:** Build a repeatable server-hardening and backup verification procedure with evidence.

#### Master

**Company workflow:** A platform lead defines fleet standards, automates compliance, establishes SLO-linked alerts, runs game days, and approves production changes through peer review.

**Lessons:** Fleet Standards; Capacity Engineering; Incident Command; Golden Images

- **linux-lab-4 — Master company lab:** Design a Linux operating model for 200 servers including patching, observability, security, backup, and disaster recovery.

### Company tickets

- **BILL-0101 — Beginner — Prepare a web-service account, directory structure, permissions, and a service health report:** Prepare a web-service account, directory structure, permissions, and a service health report. **Business impact:** Internal team productivity
- **BILL-0102 — Intermediate — Troubleshoot a simulated service outage caused by a full filesystem and incorrect service configuration:** Troubleshoot a simulated service outage caused by a full filesystem and incorrect service configuration. **Business impact:** Staging reliability and release flow
- **BILL-0103 — Advanced — Build a repeatable server-hardening and backup verification procedure with evidence:** Build a repeatable server-hardening and backup verification procedure with evidence. **Business impact:** Customer-facing production reliability
- **BILL-0104 — Master — Design a Linux operating model for 200 servers including patching, observability, security, backup, and disaster recovery:** Design a Linux operating model for 200 servers including patching, observability, security, backup, and disaster recovery. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-001 — SEV-2 — Production degradation involving Linux Administration:** Build a repeatable server-hardening and backup verification procedure with evidence. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-001 — Enterprise Linux Administration delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Linux Administration as part of an end-to-end DevOps platform.

## 🌐 Networking, DNS & HTTP

**Category:** Foundations  
**Included:** 16 lessons, 4 practice labs, 14 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Understand how applications communicate across hosts, networks, load balancers, DNS, and the web.

**Company relevance:** Many production incidents are connectivity, DNS, TLS, routing, firewall, or proxy problems. DevOps engineers need a systematic diagnostic model.

### Command and configuration examples

- `curl -vk https://service`
- `curl -w "%{time_connect} %{time_starttransfer} %{time_total}\n" -o NUL -s URL`
- `dig +trace example.com`
- `dig SRV _service._tcp.example.com`
- `ip addr`
- `ip route`
- `iperf3 -c host`
- `mtr host`
- `nslookup example.com`
- `openssl s_client -connect host:443`
- `ping -c 4 host`
- `ss -s`
- `tcpdump -w capture.pcap`
- `traceroute host`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer verifies hostname resolution, checks reachability, tests the application port, and captures the exact error before escalation.

**Lessons:** Ip Addressing; Ports And Protocols; Dns Basics; Http Request-Response

- **networking-lab-1 — Beginner company lab:** Diagnose why a client can ping a server but cannot open the web application.

#### Intermediate

**Company workflow:** An engineer traces client-to-service traffic through DNS, firewall, load balancer, proxy, and application, validating each hop.

**Lessons:** Subnets And Routing; Firewalls And Nat; Tls Certificates; Reverse Proxies

- **networking-lab-2 — Intermediate company lab:** Fix a reverse-proxy outage caused by a certificate and upstream routing mismatch.

#### Advanced

**Company workflow:** A senior engineer compares healthy and unhealthy flows, examines packets and metrics, then implements least-privilege rules with staged rollout.

**Lessons:** Load Balancing; Service Discovery; Network Policies; Packet Analysis

- **networking-lab-3 — Advanced company lab:** Design and validate active-active traffic routing across two application zones.

#### Master

**Company workflow:** A platform architect models latency, throughput, dependencies, blast radius, and failover before approving the production topology.

**Lessons:** Global Traffic Management; Zero Trust Networking; Capacity And Latency; Failure Domains

- **networking-lab-4 — Master company lab:** Create a global DNS, CDN, load-balancing, and failover design with measurable SLOs.

### Company tickets

- **BILL-0201 — Beginner — Diagnose why a client can ping a server but cannot open the web application:** Diagnose why a client can ping a server but cannot open the web application. **Business impact:** Internal team productivity
- **BILL-0202 — Intermediate — Fix a reverse-proxy outage caused by a certificate and upstream routing mismatch:** Fix a reverse-proxy outage caused by a certificate and upstream routing mismatch. **Business impact:** Staging reliability and release flow
- **BILL-0203 — Advanced — Design and validate active-active traffic routing across two application zones:** Design and validate active-active traffic routing across two application zones. **Business impact:** Customer-facing production reliability
- **BILL-0204 — Master — Create a global DNS, CDN, load-balancing, and failover design with measurable SLOs:** Create a global DNS, CDN, load-balancing, and failover design with measurable SLOs. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-002 — SEV-2 — Production degradation involving Networking, DNS & HTTP:** Design and validate active-active traffic routing across two application zones. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-002 — Enterprise Networking, DNS & HTTP delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Networking, DNS & HTTP as part of an end-to-end DevOps platform.

## 🔀 Git & Collaborative Development

**Category:** Source Control  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Manage source history, branches, reviews, releases, and safe collaboration.

**Company relevance:** Git is the audit trail and collaboration backbone for application code, infrastructure code, pipelines, and documentation.

### Command and configuration examples

- `git add .`
- `git bisect start`
- `git bundle create repo.bundle --all`
- `git cherry-pick SHA`
- `git commit -m "feat: add health check"`
- `git fetch --all`
- `git init`
- `git log --graph --oneline --decorate`
- `git mergetool`
- `git rebase origin/main`
- `git status`
- `git tag -a v1.0.0`
- `git verify-commit SHA`
- `git verify-tag v1.0.0`
- `git worktree add ../hotfix hotfix`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer creates a small branch, commits an atomic change, pushes it, and opens a review with test evidence.

**Lessons:** Repositories And Commits; Branches; Diff And Status; Remote Workflows

- **git-lab-1 — Beginner company lab:** Create a repository, commit three logical changes, and prepare a clean pull request.

#### Intermediate

**Company workflow:** An engineer updates a branch, resolves conflicts, runs tests, requests review, and uses revert rather than rewriting shared history after release.

**Lessons:** Merge And Rebase; Conflict Resolution; Tags And Releases; Revert And Reset

- **git-lab-2 — Intermediate company lab:** Resolve a merge conflict and release a tagged version with a rollback commit.

#### Advanced

**Company workflow:** A senior engineer defines short-lived branches, required checks, CODEOWNERS, signed releases, and protected environments.

**Lessons:** Trunk-Based Development; Branch Protection; Signed Commits; Monorepo Strategies

- **git-lab-3 — Advanced company lab:** Implement a governed repository workflow for an application and infrastructure repository.

#### Master

**Company workflow:** A platform lead defines organization-wide policies, release provenance, dependency controls, and migration plans with measurable adoption.

**Lessons:** Repository Governance; Release Engineering; Supply-Chain Provenance; Large-Scale Migration

- **git-lab-4 — Master company lab:** Design source-control governance for 50 teams, including exceptions, audit, and emergency changes.

### Company tickets

- **BILL-0301 — Beginner — Create a repository, commit three logical changes, and prepare a clean pull request:** Create a repository, commit three logical changes, and prepare a clean pull request. **Business impact:** Internal team productivity
- **BILL-0302 — Intermediate — Resolve a merge conflict and release a tagged version with a rollback commit:** Resolve a merge conflict and release a tagged version with a rollback commit. **Business impact:** Staging reliability and release flow
- **BILL-0303 — Advanced — Implement a governed repository workflow for an application and infrastructure repository:** Implement a governed repository workflow for an application and infrastructure repository. **Business impact:** Customer-facing production reliability
- **BILL-0304 — Master — Design source-control governance for 50 teams, including exceptions, audit, and emergency changes:** Design source-control governance for 50 teams, including exceptions, audit, and emergency changes. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-003 — SEV-1 — Production degradation involving Git & Collaborative Development:** Implement a governed repository workflow for an application and infrastructure repository. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-003 — Enterprise Git & Collaborative Development delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Git & Collaborative Development as part of an end-to-end DevOps platform.

## ⌨️ Shell Scripting

**Category:** Automation  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Automate repeatable operating tasks safely with Bash and PowerShell-friendly concepts.

**Company relevance:** Small, reliable scripts glue together build, deployment, validation, backup, and incident workflows.

### Command and configuration examples

- `awk`
- `curl --fail --retry 3`
- `exit 1`
- `flock /tmp/job.lock command`
- `for f in *.log; do echo "$f"; done`
- `getopts`
- `grep -E`
- `if [ -f file ]; then echo ok; fi`
- `mktemp -d`
- `name="app"`
- `set -Eeuo pipefail`
- `sha256sum artifact`
- `shellcheck script.sh`
- `timeout 30 command`
- `xargs -P 4`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer automates a documented manual check and validates it against sample inputs before team use.

**Lessons:** Variables And Quoting; Conditions And Loops; Exit Codes; Input And Output

- **shell-lab-1 — Beginner company lab:** Write a script that validates a service, disk space, and required files.

#### Intermediate

**Company workflow:** An engineer adds argument validation, structured logs, dry-run mode, and clear error handling before scheduling a script.

**Lessons:** Functions And Arguments; Strict Mode; Logging; Text Processing

- **shell-lab-2 — Intermediate company lab:** Build a safe log-rotation script with dry-run and retention settings.

#### Advanced

**Company workflow:** A senior engineer ensures reruns are safe, secrets are not printed, failures are isolated, and automated tests cover critical branches.

**Lessons:** Parallelism; Api Calls; Idempotency; Testing Shell Scripts

- **shell-lab-3 — Advanced company lab:** Automate deployment validation across several hosts with bounded parallelism.

#### Master

**Company workflow:** A platform lead decides when shell is appropriate, defines libraries and review gates, and migrates complex scripts to maintainable services.

**Lessons:** Automation Standards; Cross-Platform Strategy; Security Review; Operational Ownership

- **shell-lab-4 — Master company lab:** Create an enterprise shell-automation standard with examples, controls, and migration criteria.

### Company tickets

- **BILL-0401 — Beginner — Write a script that validates a service, disk space, and required files:** Write a script that validates a service, disk space, and required files. **Business impact:** Internal team productivity
- **BILL-0402 — Intermediate — Build a safe log-rotation script with dry-run and retention settings:** Build a safe log-rotation script with dry-run and retention settings. **Business impact:** Staging reliability and release flow
- **BILL-0403 — Advanced — Automate deployment validation across several hosts with bounded parallelism:** Automate deployment validation across several hosts with bounded parallelism. **Business impact:** Customer-facing production reliability
- **BILL-0404 — Master — Create an enterprise shell-automation standard with examples, controls, and migration criteria:** Create an enterprise shell-automation standard with examples, controls, and migration criteria. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-004 — SEV-2 — Production degradation involving Shell Scripting:** Automate deployment validation across several hosts with bounded parallelism. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-004 — Enterprise Shell Scripting delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Shell Scripting as part of an end-to-end DevOps platform.

## 🐍 Python for DevOps Automation

**Category:** Automation  
**Included:** 16 lessons, 4 practice labs, 11 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Build maintainable automation, integrations, CLIs, and operational services with Python.

**Company relevance:** Python is widely used for cloud automation, API integration, data processing, testing, and internal tooling.

### Command and configuration examples

- `python -m build`
- `python -m compileall .`
- `python -m json.tool file.json`
- `python -m pip audit`
- `python -m pip check`
- `python -m pip install -r requirements.txt`
- `python -m unittest`
- `python -m unittest discover -v`
- `python -m venv .venv`
- `python -X dev app.py`
- `python app.py`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer converts a manual report into a small script with input validation and clear errors.

**Lessons:** Syntax And Data Structures; Functions And Modules; Files And Json; Exceptions

- **python-automation-lab-1 — Beginner company lab:** Read inventory JSON, validate hosts, and generate a deployment summary.

#### Intermediate

**Company workflow:** An engineer builds a CLI client, handles retries and timeouts, logs actions, and writes tests using mocked responses.

**Lessons:** Http Apis; Cli Design; Logging; Unit Testing

- **python-automation-lab-2 — Intermediate company lab:** Build a CLI that calls a health API, retries transient failures, and exports JSON.

#### Advanced

**Company workflow:** A senior engineer designs safe concurrency, externalized config, secret injection, schema migrations, and release automation.

**Lessons:** Concurrency; Configuration And Secrets; Packaging; Database Access

- **python-automation-lab-3 — Advanced company lab:** Create an inventory service that checks hosts concurrently and stores auditable results.

#### Master

**Company workflow:** A platform lead defines ownership, service levels, compatibility, telemetry, and security for shared automation products.

**Lessons:** Internal Developer Platforms; Service Reliability; Api Contracts; Governance

- **python-automation-lab-4 — Master company lab:** Design an internal automation platform with plugins, RBAC, audit logs, and lifecycle management.

### Company tickets

- **BILL-0501 — Beginner — Read inventory JSON, validate hosts, and generate a deployment summary:** Read inventory JSON, validate hosts, and generate a deployment summary. **Business impact:** Internal team productivity
- **BILL-0502 — Intermediate — Build a CLI that calls a health API, retries transient failures, and exports JSON:** Build a CLI that calls a health API, retries transient failures, and exports JSON. **Business impact:** Staging reliability and release flow
- **BILL-0503 — Advanced — Create an inventory service that checks hosts concurrently and stores auditable results:** Create an inventory service that checks hosts concurrently and stores auditable results. **Business impact:** Customer-facing production reliability
- **BILL-0504 — Master — Design an internal automation platform with plugins, RBAC, audit logs, and lifecycle management:** Design an internal automation platform with plugins, RBAC, audit logs, and lifecycle management. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-005 — SEV-2 — Production degradation involving Python for DevOps Automation:** Create an inventory service that checks hosts concurrently and stores auditable results. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-005 — Enterprise Python for DevOps Automation delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Python for DevOps Automation as part of an end-to-end DevOps platform.

## 📦 Docker & Containers

**Category:** Containers  
**Included:** 16 lessons, 4 practice labs, 14 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Package applications into reproducible, secure containers and operate them across environments.

**Company relevance:** Containers standardize application runtime, accelerate delivery, and form the workload unit for modern platforms.

### Command and configuration examples

- `docker build -t app:1.0 .`
- `docker buildx build --platform linux/amd64,linux/arm64 .`
- `docker compose up -d`
- `docker diff container`
- `docker history image`
- `docker inspect container`
- `docker logs container`
- `docker manifest inspect image`
- `docker network ls`
- `docker ps`
- `docker run --rm -p 8080:8080 app:1.0`
- `docker save image -o image.tar`
- `docker stats`
- `docker system df`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer builds an image, runs it locally, verifies health, tags it, and pushes it to an approved registry.

**Lessons:** Images And Containers; Dockerfiles; Ports And Volumes; Registries

- **docker-lab-1 — Beginner company lab:** Containerize a small web application with a health check and persistent data.

#### Intermediate

**Company workflow:** An engineer creates a smaller production image, defines dependent services, sets limits, and validates startup and shutdown behavior.

**Lessons:** Multi-Stage Builds; Compose; Networks; Resource Limits

- **docker-lab-2 — Intermediate company lab:** Build a multi-service development environment and troubleshoot failed service discovery.

#### Advanced

**Company workflow:** A senior engineer scans images, pins dependencies, runs as non-root, signs artifacts, and defines exception handling.

**Lessons:** Image Security; Rootless Execution; Supply Chain; Runtime Diagnostics

- **docker-lab-3 — Advanced company lab:** Harden an image, reduce size, document vulnerabilities, and prove runtime restrictions.

#### Master

**Company workflow:** A platform lead defines base images, retention, provenance, vulnerability gates, and migration from legacy workloads.

**Lessons:** Registry Governance; Platform Standards; Cost And Capacity; Migration Strategy

- **docker-lab-4 — Master company lab:** Design a governed container supply chain for multiple teams and environments.

### Company tickets

- **BILL-0601 — Beginner — Containerize a small web application with a health check and persistent data:** Containerize a small web application with a health check and persistent data. **Business impact:** Internal team productivity
- **BILL-0602 — Intermediate — Build a multi-service development environment and troubleshoot failed service discovery:** Build a multi-service development environment and troubleshoot failed service discovery. **Business impact:** Staging reliability and release flow
- **BILL-0603 — Advanced — Harden an image, reduce size, document vulnerabilities, and prove runtime restrictions:** Harden an image, reduce size, document vulnerabilities, and prove runtime restrictions. **Business impact:** Customer-facing production reliability
- **BILL-0604 — Master — Design a governed container supply chain for multiple teams and environments:** Design a governed container supply chain for multiple teams and environments. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-006 — SEV-1 — Production degradation involving Docker & Containers:** Harden an image, reduce size, document vulnerabilities, and prove runtime restrictions. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-006 — Enterprise Docker & Containers delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Docker & Containers as part of an end-to-end DevOps platform.

## ☸️ Kubernetes

**Category:** Containers  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Deploy, scale, secure, observe, and troubleshoot containerized applications on Kubernetes.

**Company relevance:** Kubernetes provides a common control plane for scheduling, networking, configuration, scaling, and recovery of container workloads.

### Command and configuration examples

- `kubectl api-resources`
- `kubectl apply -f app.yaml`
- `kubectl auth can-i --list`
- `kubectl debug node/NODE -it --image=busybox`
- `kubectl describe pod POD`
- `kubectl diff -f manifests/`
- `kubectl drain NODE --ignore-daemonsets`
- `kubectl get events --sort-by=.lastTimestamp`
- `kubectl get hpa`
- `kubectl get pods -A`
- `kubectl logs POD`
- `kubectl port-forward svc/app 8080:80`
- `kubectl rollout undo deploy/app`
- `kubectl top pods`
- `kubectl wait --for=condition=available deploy/app`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer applies reviewed manifests to a sandbox namespace, checks rollout and logs, then documents the service endpoint.

**Lessons:** Pods And Deployments; Services; Config Maps And Secrets; Kubectl Basics

- **kubernetes-lab-1 — Beginner company lab:** Deploy a web application with configuration, health probes, and a ClusterIP service.

#### Intermediate

**Company workflow:** An engineer prepares environment overlays, capacity requests, ingress, persistent storage, and rollback validation.

**Lessons:** Ingress; Persistent Volumes; Requests And Limits; Rolling Updates

- **kubernetes-lab-2 — Intermediate company lab:** Troubleshoot a rollout with failing readiness probes and insufficient resources.

#### Advanced

**Company workflow:** A senior engineer applies least privilege, isolates namespaces, tunes autoscaling, and diagnoses control-plane or node symptoms.

**Lessons:** Rbac And Policies; Autoscaling; Network Policies; Cluster Troubleshooting

- **kubernetes-lab-3 — Advanced company lab:** Secure and scale a multi-tier application while preserving availability during node maintenance.

#### Master

**Company workflow:** A platform lead defines tenancy, fleet upgrades, disaster recovery, developer abstractions, SLOs, and cluster economics.

**Lessons:** Multi-Cluster Design; Platform Apis; Upgrade Strategy; Cost And Reliability

- **kubernetes-lab-4 — Master company lab:** Design a production Kubernetes platform for 30 teams with governance and self-service.

### Company tickets

- **BILL-0701 — Beginner — Deploy a web application with configuration, health probes, and a ClusterIP service:** Deploy a web application with configuration, health probes, and a ClusterIP service. **Business impact:** Internal team productivity
- **BILL-0702 — Intermediate — Troubleshoot a rollout with failing readiness probes and insufficient resources:** Troubleshoot a rollout with failing readiness probes and insufficient resources. **Business impact:** Staging reliability and release flow
- **BILL-0703 — Advanced — Secure and scale a multi-tier application while preserving availability during node maintenance:** Secure and scale a multi-tier application while preserving availability during node maintenance. **Business impact:** Customer-facing production reliability
- **BILL-0704 — Master — Design a production Kubernetes platform for 30 teams with governance and self-service:** Design a production Kubernetes platform for 30 teams with governance and self-service. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-007 — SEV-2 — Production degradation involving Kubernetes:** Secure and scale a multi-tier application while preserving availability during node maintenance. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-007 — Enterprise Kubernetes delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Kubernetes as part of an end-to-end DevOps platform.

## 🚀 CI/CD Engineering

**Category:** Delivery  
**Included:** 16 lessons, 4 practice labs, 16 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Design reliable pipelines that build, test, secure, release, deploy, verify, and roll back software.

**Company relevance:** CI/CD turns source changes into controlled, traceable production outcomes while reducing risk and lead time.

### Command and configuration examples

- `abort and rollback`
- `approve production`
- `build`
- `canary 5%`
- `change failure rate`
- `deploy staging`
- `deployment frequency`
- `lead time`
- `mean time to restore`
- `package`
- `promote 25%`
- `publish`
- `rollback release`
- `smoke test`
- `test`
- `verify SLO`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer pushes a change; the pipeline validates formatting, tests, builds an immutable artifact, and publishes evidence.

**Lessons:** Continuous Integration; Pipeline Stages; Artifacts; Basic Deployment

- **cicd-lab-1 — Beginner company lab:** Create a pipeline plan for lint, unit test, package, and artifact retention.

#### Intermediate

**Company workflow:** An engineer promotes the same artifact through test and staging, uses protected secrets, obtains approval, deploys, and validates health.

**Lessons:** Environment Promotion; Secrets; Approvals; Rollback

- **cicd-lab-2 — Intermediate company lab:** Design a three-environment pipeline with approvals and automated rollback criteria.

#### Advanced

**Company workflow:** A senior engineer combines canary rollout, policy checks, backward-compatible migrations, telemetry, and automated decision gates.

**Lessons:** Progressive Delivery; Security Gates; Database Changes; Pipeline Observability

- **cicd-lab-3 — Advanced company lab:** Create a progressive-delivery runbook for a risky API and database change.

#### Master

**Company workflow:** A platform lead provides reusable pipeline components, policy-as-code, scorecards, and disaster-recovery exercises.

**Lessons:** Delivery Platform; Dora Metrics; Governance; Resilience Testing

- **cicd-lab-4 — Master company lab:** Design an organization-wide CI/CD product with paved roads and controlled exceptions.

### Company tickets

- **BILL-0801 — Beginner — Create a pipeline plan for lint, unit test, package, and artifact retention:** Create a pipeline plan for lint, unit test, package, and artifact retention. **Business impact:** Internal team productivity
- **BILL-0802 — Intermediate — Design a three-environment pipeline with approvals and automated rollback criteria:** Design a three-environment pipeline with approvals and automated rollback criteria. **Business impact:** Staging reliability and release flow
- **BILL-0803 — Advanced — Create a progressive-delivery runbook for a risky API and database change:** Create a progressive-delivery runbook for a risky API and database change. **Business impact:** Customer-facing production reliability
- **BILL-0804 — Master — Design an organization-wide CI/CD product with paved roads and controlled exceptions:** Design an organization-wide CI/CD product with paved roads and controlled exceptions. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-008 — SEV-2 — Production degradation involving CI/CD Engineering:** Create a progressive-delivery runbook for a risky API and database change. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-008 — Enterprise CI/CD Engineering delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using CI/CD Engineering as part of an end-to-end DevOps platform.

## 🏗️ Jenkins

**Category:** Delivery  
**Included:** 16 lessons, 4 practice labs, 14 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Build and operate Jenkins pipelines, agents, credentials, plugins, and shared libraries.

**Company relevance:** Jenkins remains common in enterprises for customizable build and deployment automation across diverse systems.

### Command and configuration examples

- `@Library("company-lib") _`
- `agent { label "linux" }`
- `archiveArtifacts`
- `build queue analysis`
- `disableConcurrentBuilds()`
- `junit`
- `options { timeout(...) }`
- `parameters`
- `pipeline { agent any }`
- `post { always {} }`
- `quietDown`
- `safeRestart`
- `stage("Test")`
- `withCredentials`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer adds a Jenkinsfile, triggers a branch build, reads console output, and archives test reports.

**Lessons:** Jobs And Pipelines; Jenkinsfile; Stages And Steps; Artifacts

- **jenkins-lab-1 — Beginner company lab:** Create a declarative pipeline for checkout, test, package, and archive.

#### Intermediate

**Company workflow:** An engineer routes jobs to labeled agents, injects credentials safely, parameterizes releases, and sends failure notifications.

**Lessons:** Agents; Credentials; Parameters; Post Actions

- **jenkins-lab-2 — Intermediate company lab:** Build a parameterized deployment pipeline using protected credentials.

#### Advanced

**Company workflow:** A senior engineer centralizes approved steps, limits plugins, backs up configuration, and reviews script approvals.

**Lessons:** Shared Libraries; Plugin Governance; Controller Backup; Pipeline Security

- **jenkins-lab-3 — Advanced company lab:** Create a shared pipeline library and recovery plan for a Jenkins controller.

#### Master

**Company workflow:** A platform lead decides controller boundaries, agent elasticity, service objectives, and migration to managed or cloud-native alternatives.

**Lessons:** High Availability Strategy; Migration; Capacity; Governance

- **jenkins-lab-4 — Master company lab:** Design Jenkins as a governed internal service for 40 teams.

### Company tickets

- **BILL-0901 — Beginner — Create a declarative pipeline for checkout, test, package, and archive:** Create a declarative pipeline for checkout, test, package, and archive. **Business impact:** Internal team productivity
- **BILL-0902 — Intermediate — Build a parameterized deployment pipeline using protected credentials:** Build a parameterized deployment pipeline using protected credentials. **Business impact:** Staging reliability and release flow
- **BILL-0903 — Advanced — Create a shared pipeline library and recovery plan for a Jenkins controller:** Create a shared pipeline library and recovery plan for a Jenkins controller. **Business impact:** Customer-facing production reliability
- **BILL-0904 — Master — Design Jenkins as a governed internal service for 40 teams:** Design Jenkins as a governed internal service for 40 teams. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-009 — SEV-1 — Production degradation involving Jenkins:** Create a shared pipeline library and recovery plan for a Jenkins controller. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-009 — Enterprise Jenkins delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Jenkins as part of an end-to-end DevOps platform.

## ⚙️ GitHub Actions

**Category:** Delivery  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Automate repository workflows with reusable GitHub Actions, environments, runners, and security controls.

**Company relevance:** GitHub Actions integrates source, review, automation, security, and release workflows close to the repository.

### Command and configuration examples

- `actions/cache`
- `artifact retention`
- `environment: production`
- `on: pull_request`
- `permissions: id-token: write`
- `required workflows`
- `run: test-command`
- `runner groups`
- `runs-on: self-hosted`
- `secrets.TOKEN`
- `strategy.matrix`
- `uses: actions/checkout`
- `uses: actions/upload-artifact`
- `uses: owner/action@SHA`
- `workflow_call`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer opens a pull request; the workflow checks out code, tests it, and publishes a report.

**Lessons:** Workflow Syntax; Events; Jobs And Steps; Artifacts

- **github-actions-lab-1 — Beginner company lab:** Create a pull-request workflow with tests and artifacts.

#### Intermediate

**Company workflow:** An engineer tests multiple versions, caches dependencies, protects production, and uses environment-scoped secrets.

**Lessons:** Matrices; Caching; Environments; Secrets

- **github-actions-lab-2 — Intermediate company lab:** Build a matrix pipeline and protected deployment environment.

#### Advanced

**Company workflow:** A senior engineer replaces long-lived cloud keys with OIDC, centralizes workflows, and pins third-party actions.

**Lessons:** Oidc; Reusable Workflows; Self-Hosted Runners; Supply-Chain Controls

- **github-actions-lab-3 — Advanced company lab:** Create a secure reusable deployment workflow using cloud federation.

#### Master

**Company workflow:** A platform lead defines approved actions, runner isolation, retention, audit, and service-level objectives.

**Lessons:** Organization Policy; Runner Platform; Cost; Compliance

- **github-actions-lab-4 — Master company lab:** Design GitHub Actions governance for an enterprise organization.

### Company tickets

- **BILL-1001 — Beginner — Create a pull-request workflow with tests and artifacts:** Create a pull-request workflow with tests and artifacts. **Business impact:** Internal team productivity
- **BILL-1002 — Intermediate — Build a matrix pipeline and protected deployment environment:** Build a matrix pipeline and protected deployment environment. **Business impact:** Staging reliability and release flow
- **BILL-1003 — Advanced — Create a secure reusable deployment workflow using cloud federation:** Create a secure reusable deployment workflow using cloud federation. **Business impact:** Customer-facing production reliability
- **BILL-1004 — Master — Design GitHub Actions governance for an enterprise organization:** Design GitHub Actions governance for an enterprise organization. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-010 — SEV-2 — Production degradation involving GitHub Actions:** Create a secure reusable deployment workflow using cloud federation. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-010 — Enterprise GitHub Actions delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using GitHub Actions as part of an end-to-end DevOps platform.

## 🏛️ Terraform & Infrastructure as Code

**Category:** Infrastructure as Code  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Provision and change infrastructure through reviewed, repeatable, state-managed code.

**Company relevance:** Infrastructure as Code makes environments reproducible, reviewable, testable, and auditable.

### Command and configuration examples

- `ephemeral plans`
- `module versioning`
- `policy checks`
- `terraform fmt -check`
- `terraform import`
- `terraform init`
- `terraform output`
- `terraform plan`
- `terraform plan -detailed-exitcode`
- `terraform state list`
- `terraform state mv`
- `terraform state pull`
- `terraform test`
- `terraform validate`
- `terraform workspace list`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer changes infrastructure code, formats and validates it, reviews the plan, then applies in a sandbox.

**Lessons:** Providers And Resources; Variables And Outputs; Plan And Apply; State Basics

- **terraform-lab-1 — Beginner company lab:** Provision a small network and compute resource with variables and outputs.

#### Intermediate

**Company workflow:** An engineer uses versioned modules, remote locking, separate environment state, and imports existing resources carefully.

**Lessons:** Modules; Remote State; Workspaces And Environments; Imports

- **terraform-lab-2 — Intermediate company lab:** Refactor repeated infrastructure into modules without recreating resources.

#### Advanced

**Company workflow:** A senior engineer adds policy checks, detects drift, protects state, plans recovery, and avoids secrets in outputs.

**Lessons:** Testing And Policy; State Recovery; Drift; Secrets

- **terraform-lab-3 — Advanced company lab:** Recover from an incorrect state move and establish drift detection.

#### Master

**Company workflow:** A platform lead defines account structure, approved modules, policy-as-code, exceptions, and self-service workflows.

**Lessons:** Landing Zones; Module Registry; Governance; Platform Integration

- **terraform-lab-4 — Master company lab:** Design an enterprise IaC operating model with security, audit, and disaster recovery.

### Company tickets

- **BILL-1101 — Beginner — Provision a small network and compute resource with variables and outputs:** Provision a small network and compute resource with variables and outputs. **Business impact:** Internal team productivity
- **BILL-1102 — Intermediate — Refactor repeated infrastructure into modules without recreating resources:** Refactor repeated infrastructure into modules without recreating resources. **Business impact:** Staging reliability and release flow
- **BILL-1103 — Advanced — Recover from an incorrect state move and establish drift detection:** Recover from an incorrect state move and establish drift detection. **Business impact:** Customer-facing production reliability
- **BILL-1104 — Master — Design an enterprise IaC operating model with security, audit, and disaster recovery:** Design an enterprise IaC operating model with security, audit, and disaster recovery. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-011 — SEV-2 — Production degradation involving Terraform & Infrastructure as Code:** Recover from an incorrect state move and establish drift detection. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-011 — Enterprise Terraform & Infrastructure as Code delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Terraform & Infrastructure as Code as part of an end-to-end DevOps platform.

## 🧩 Ansible Configuration Automation

**Category:** Infrastructure as Code  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Configure systems and orchestrate repeatable operations using inventories, playbooks, roles, and idempotent modules.

**Company relevance:** Ansible is used for server configuration, patching, deployment orchestration, and operational automation without agents.

### Command and configuration examples

- `--check`
- `--diff`
- `--limit group`
- `--tags deploy`
- `ansible all -m ping`
- `ansible-galaxy init role`
- `ansible-inventory --graph`
- `ansible-playbook site.yml`
- `ansible-vault encrypt`
- `credential types`
- `execution environments`
- `job templates`
- `max_fail_percentage`
- `serial: 10%`
- `strategy: free`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer targets a sandbox group, checks connectivity, runs a reviewed playbook, and confirms changed versus unchanged hosts.

**Lessons:** Inventory; Ad-Hoc Commands; Playbooks; Modules

- **ansible-lab-1 — Beginner company lab:** Configure a web server package, service, and configuration idempotently.

#### Intermediate

**Company workflow:** An engineer separates reusable roles, validates variable precedence, templates config, and restarts only when required.

**Lessons:** Roles; Variables; Templates; Handlers

- **ansible-lab-2 — Intermediate company lab:** Create a reusable application role with validation and handlers.

#### Advanced

**Company workflow:** A senior engineer protects secrets, discovers cloud hosts dynamically, tests roles, and rolls changes through batches.

**Lessons:** Vault; Dynamic Inventory; Testing; Rolling Operations

- **ansible-lab-3 — Advanced company lab:** Patch a fleet in controlled batches with rollback and failure thresholds.

#### Master

**Company workflow:** A platform lead provides RBAC, approved content, isolated execution, audit trails, and event-driven runbooks.

**Lessons:** Automation Controller; Governance; Execution Environments; Event-Driven Automation

- **ansible-lab-4 — Master company lab:** Design a governed enterprise automation service for infrastructure and operations.

### Company tickets

- **BILL-1201 — Beginner — Configure a web server package, service, and configuration idempotently:** Configure a web server package, service, and configuration idempotently. **Business impact:** Internal team productivity
- **BILL-1202 — Intermediate — Create a reusable application role with validation and handlers:** Create a reusable application role with validation and handlers. **Business impact:** Staging reliability and release flow
- **BILL-1203 — Advanced — Patch a fleet in controlled batches with rollback and failure thresholds:** Patch a fleet in controlled batches with rollback and failure thresholds. **Business impact:** Customer-facing production reliability
- **BILL-1204 — Master — Design a governed enterprise automation service for infrastructure and operations:** Design a governed enterprise automation service for infrastructure and operations. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-012 — SEV-1 — Production degradation involving Ansible Configuration Automation:** Patch a fleet in controlled batches with rollback and failure thresholds. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-012 — Enterprise Ansible Configuration Automation delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Ansible Configuration Automation as part of an end-to-end DevOps platform.

## ☁️ AWS Cloud

**Category:** Cloud  
**Included:** 16 lessons, 4 practice labs, 13 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Design, deploy, secure, and operate workloads on Amazon Web Services.

**Company relevance:** AWS provides compute, storage, networking, identity, databases, observability, and managed services used by many organizations.

### Command and configuration examples

- `aws cloudtrail lookup-events`
- `aws cloudwatch get-metric-data`
- `aws configservice describe-config-rules`
- `aws configure list`
- `aws ec2 describe-instances`
- `aws logs tail`
- `aws organizations list-accounts`
- `aws route53 list-hosted-zones`
- `aws s3 ls`
- `aws sts get-caller-identity`
- `cost allocation tags`
- `service control policies`
- `well-architected review`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer works in a sandbox account using least privilege, tags resources, validates access, and cleans up temporary resources.

**Lessons:** Iam; Ec2; S3; Vpc Basics

- **aws-lab-1 — Beginner company lab:** Create a secure static-site and compute sandbox design with cost controls.

#### Intermediate

**Company workflow:** An engineer deploys a multi-tier service, configures monitoring and backups, tests scaling, and documents recovery.

**Lessons:** Load Balancing And Autoscaling; Rds; Cloudwatch; Route 53

- **aws-lab-2 — Intermediate company lab:** Design and troubleshoot a highly available web application across availability zones.

#### Advanced

**Company workflow:** A senior engineer applies account boundaries, centralized logs, guardrails, automated detection, and tested recovery patterns.

**Lessons:** Organizations And Accounts; Security Services; Event-Driven Systems; Disaster Recovery

- **aws-lab-3 — Advanced company lab:** Create a multi-account security and disaster-recovery operating model.

#### Master

**Company workflow:** A cloud lead defines paved roads, service ownership, budgets, quotas, resilience tiers, and architectural review.

**Lessons:** Landing Zones; Platform Products; Finops; Global Architecture

- **aws-lab-4 — Master company lab:** Design an AWS landing zone and internal platform for multiple business units.

### Company tickets

- **BILL-1301 — Beginner — Create a secure static-site and compute sandbox design with cost controls:** Create a secure static-site and compute sandbox design with cost controls. **Business impact:** Internal team productivity
- **BILL-1302 — Intermediate — Design and troubleshoot a highly available web application across availability zones:** Design and troubleshoot a highly available web application across availability zones. **Business impact:** Staging reliability and release flow
- **BILL-1303 — Advanced — Create a multi-account security and disaster-recovery operating model:** Create a multi-account security and disaster-recovery operating model. **Business impact:** Customer-facing production reliability
- **BILL-1304 — Master — Design an AWS landing zone and internal platform for multiple business units:** Design an AWS landing zone and internal platform for multiple business units. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-013 — SEV-2 — Production degradation involving AWS Cloud:** Create a multi-account security and disaster-recovery operating model. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-013 — Enterprise AWS Cloud delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using AWS Cloud as part of an end-to-end DevOps platform.

## 🔷 Microsoft Azure

**Category:** Cloud  
**Included:** 16 lessons, 4 practice labs, 13 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Build and operate secure workloads using Azure identity, compute, networking, data, and platform services.

**Company relevance:** Azure is common in Microsoft-centric enterprises and supports hybrid identity, governance, and managed cloud services.

### Command and configuration examples

- `az account show`
- `az group list`
- `az identity list`
- `az monitor metrics list`
- `az network vnet list`
- `az policy assignment list`
- `az role assignment list`
- `az storage account list`
- `az vm list`
- `az webapp log tail`
- `cost management exports`
- `management groups`
- `policy initiatives`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer deploys tagged resources in a sandbox group with approved identity and budget boundaries.

**Lessons:** Subscriptions And Resource Groups; Microsoft Entra Id; Virtual Machines; Storage

- **azure-lab-1 — Beginner company lab:** Design a sandbox resource group with VM, storage, identity, and cleanup controls.

#### Intermediate

**Company workflow:** An engineer builds a multi-tier environment, configures diagnostics, validates private connectivity, and tests backup restore.

**Lessons:** Virtual Networks; Application Gateway; Azure Monitor; Managed Databases

- **azure-lab-2 — Intermediate company lab:** Troubleshoot an application that cannot reach a private managed database.

#### Advanced

**Company workflow:** A senior engineer applies policy at hierarchy level, replaces secrets with managed identities, and validates regional recovery.

**Lessons:** Management Groups; Policy; Managed Identities; Disaster Recovery

- **azure-lab-3 — Advanced company lab:** Create a governed multi-subscription design with central logging and recovery.

#### Master

**Company workflow:** A cloud lead defines management hierarchy, connectivity, identity, platform subscriptions, budgets, and self-service products.

**Lessons:** Enterprise-Scale Landing Zone; Hybrid Platform; Finops; Platform Engineering

- **azure-lab-4 — Master company lab:** Design an Azure enterprise landing zone for regulated workloads.

### Company tickets

- **BILL-1401 — Beginner — Design a sandbox resource group with VM, storage, identity, and cleanup controls:** Design a sandbox resource group with VM, storage, identity, and cleanup controls. **Business impact:** Internal team productivity
- **BILL-1402 — Intermediate — Troubleshoot an application that cannot reach a private managed database:** Troubleshoot an application that cannot reach a private managed database. **Business impact:** Staging reliability and release flow
- **BILL-1403 — Advanced — Create a governed multi-subscription design with central logging and recovery:** Create a governed multi-subscription design with central logging and recovery. **Business impact:** Customer-facing production reliability
- **BILL-1404 — Master — Design an Azure enterprise landing zone for regulated workloads:** Design an Azure enterprise landing zone for regulated workloads. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-014 — SEV-2 — Production degradation involving Microsoft Azure:** Create a governed multi-subscription design with central logging and recovery. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-014 — Enterprise Microsoft Azure delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Microsoft Azure as part of an end-to-end DevOps platform.

## 🌤️ Google Cloud Platform

**Category:** Cloud  
**Included:** 16 lessons, 4 practice labs, 13 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Operate workloads using Google Cloud identity, compute, networking, data, observability, and managed platforms.

**Company relevance:** GCP is strong in data, Kubernetes, analytics, and globally distributed managed services.

### Command and configuration examples

- `billing export`
- `gcloud compute instances list`
- `gcloud compute networks list`
- `gcloud config list`
- `gcloud iam service-accounts list`
- `gcloud logging sinks list`
- `gcloud monitoring policies list`
- `gcloud projects list`
- `gcloud resource-manager org-policies list`
- `gcloud sql instances list`
- `gcloud storage ls`
- `organization policy`
- `shared VPC`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer uses a sandbox project, service account, labels, budget alert, and cleans up resources after validation.

**Lessons:** Projects And Billing; Iam; Compute Engine; Cloud Storage

- **gcp-lab-1 — Beginner company lab:** Design a project with compute, storage, identity, and budget safeguards.

#### Intermediate

**Company workflow:** An engineer deploys a multi-tier service, configures private networking and monitoring, and validates backup recovery.

**Lessons:** Vpc And Load Balancing; Cloud Sql; Cloud Monitoring; Cloud Dns

- **gcp-lab-2 — Intermediate company lab:** Troubleshoot a service that fails through the load balancer but works directly.

#### Advanced

**Company workflow:** A senior engineer defines folders and guardrails, eliminates static keys, centralizes logs, and tests regional failover.

**Lessons:** Organization Policies; Workload Identity; Event Systems; Disaster Recovery

- **gcp-lab-3 — Advanced company lab:** Design a governed folder/project structure and recovery plan.

#### Master

**Company workflow:** A cloud lead creates reusable foundations, shared VPCs, budgets, service catalogs, and architecture standards.

**Lessons:** Landing Zones; Data Platform; Finops; Global Architecture

- **gcp-lab-4 — Master company lab:** Design a GCP landing zone and internal developer platform.

### Company tickets

- **BILL-1501 — Beginner — Design a project with compute, storage, identity, and budget safeguards:** Design a project with compute, storage, identity, and budget safeguards. **Business impact:** Internal team productivity
- **BILL-1502 — Intermediate — Troubleshoot a service that fails through the load balancer but works directly:** Troubleshoot a service that fails through the load balancer but works directly. **Business impact:** Staging reliability and release flow
- **BILL-1503 — Advanced — Design a governed folder/project structure and recovery plan:** Design a governed folder/project structure and recovery plan. **Business impact:** Customer-facing production reliability
- **BILL-1504 — Master — Design a GCP landing zone and internal developer platform:** Design a GCP landing zone and internal developer platform. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-015 — SEV-1 — Production degradation involving Google Cloud Platform:** Design a governed folder/project structure and recovery plan. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-015 — Enterprise Google Cloud Platform delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Google Cloud Platform as part of an end-to-end DevOps platform.

## 📈 Prometheus, Grafana & Observability

**Category:** Operations  
**Included:** 16 lessons, 4 practice labs, 12 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Collect, query, visualize, alert on, and use metrics, logs, and traces to operate systems.

**Company relevance:** Observability helps teams understand system behavior, detect failures, diagnose causes, and manage service objectives.

### Command and configuration examples

- `burn-rate alerts`
- `histogram_quantile`
- `increase(errors_total[10m])`
- `label_replace`
- `promtool check config`
- `rate(http_requests_total[5m])`
- `retention tiers`
- `sampling policy`
- `sum by (service)`
- `telemetry contracts`
- `topk`
- `up`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer checks target health, runs a basic query, reads a dashboard, and links an alert to a runbook.

**Lessons:** Metrics And Labels; Prometheus Scraping; Grafana Dashboards; Basic Alerts

- **observability-lab-1 — Beginner company lab:** Create a service dashboard with traffic, errors, latency, and saturation.

#### Intermediate

**Company workflow:** An engineer adds recording rules, removes noisy alerts, routes notifications, and validates exporter failure behavior.

**Lessons:** Recording Rules; Alertmanager; Exporters; Dashboard Design

- **observability-lab-2 — Intermediate company lab:** Design alerts that identify user impact without paging on harmless symptoms.

#### Advanced

**Company workflow:** A senior engineer defines SLIs, controls cardinality, scales storage, and correlates traces, logs, and metrics.

**Lessons:** Slos And Error Budgets; High Availability; Cardinality; Tracing Integration

- **observability-lab-3 — Advanced company lab:** Implement multi-window burn-rate alerting for an API SLO.

#### Master

**Company workflow:** A platform lead defines telemetry standards, tenant boundaries, retention, cost allocation, and adoption scorecards.

**Lessons:** Observability Platform; Governance; Cost Controls; Incident Learning

- **observability-lab-4 — Master company lab:** Design an observability platform for 100 services with measurable reliability outcomes.

### Company tickets

- **BILL-1601 — Beginner — Create a service dashboard with traffic, errors, latency, and saturation:** Create a service dashboard with traffic, errors, latency, and saturation. **Business impact:** Internal team productivity
- **BILL-1602 — Intermediate — Design alerts that identify user impact without paging on harmless symptoms:** Design alerts that identify user impact without paging on harmless symptoms. **Business impact:** Staging reliability and release flow
- **BILL-1603 — Advanced — Implement multi-window burn-rate alerting for an API SLO:** Implement multi-window burn-rate alerting for an API SLO. **Business impact:** Customer-facing production reliability
- **BILL-1604 — Master — Design an observability platform for 100 services with measurable reliability outcomes:** Design an observability platform for 100 services with measurable reliability outcomes. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-016 — SEV-2 — Production degradation involving Prometheus, Grafana & Observability:** Implement multi-window burn-rate alerting for an API SLO. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-016 — Enterprise Prometheus, Grafana & Observability delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Prometheus, Grafana & Observability as part of an end-to-end DevOps platform.

## 🧾 Centralized Logging & OpenSearch/ELK

**Category:** Operations  
**Included:** 16 lessons, 4 practice labs, 12 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Collect, parse, store, search, retain, and govern application and infrastructure logs.

**Company relevance:** Central logs provide incident evidence, security visibility, audit trails, and operational insight across distributed systems.

### Command and configuration examples

- `archive tiers`
- `field caps`
- `grep request_id`
- `grok patterns`
- `index templates`
- `journalctl -o json`
- `JSON fields`
- `lifecycle policies`
- `mapping templates`
- `retention matrix`
- `snapshot and restore`
- `tenant quotas`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer confirms logs are emitted as structured events, finds a request ID, and records the timeline.

**Lessons:** Structured Logging; Collectors; Indexes; Search Basics

- **logging-lab-1 — Beginner company lab:** Convert plain application logs into structured events and search an incident timeline.

#### Intermediate

**Company workflow:** An engineer parses events, routes indexes, applies retention, creates operational views, and restricts sensitive data.

**Lessons:** Pipelines And Parsing; Index Lifecycle; Dashboards; Access Control

- **logging-lab-2 — Intermediate company lab:** Build an ingestion pipeline for web, application, and audit logs.

#### Advanced

**Company workflow:** A senior engineer controls mappings, shard growth, redaction, recovery, and correlation with metrics and traces.

**Lessons:** Cluster Scaling; Schema Governance; Pii Controls; Cross-Signal Correlation

- **logging-lab-3 — Advanced company lab:** Recover a degraded logging cluster and prevent repeat shard exhaustion.

#### Master

**Company workflow:** A platform lead defines data classes, retention tiers, legal holds, chargeback, and self-service onboarding.

**Lessons:** Logging Platform; Compliance Retention; Cost Optimization; Tenant Governance

- **logging-lab-4 — Master company lab:** Design a compliant logging platform for engineering and security teams.

### Company tickets

- **BILL-1701 — Beginner — Convert plain application logs into structured events and search an incident timeline:** Convert plain application logs into structured events and search an incident timeline. **Business impact:** Internal team productivity
- **BILL-1702 — Intermediate — Build an ingestion pipeline for web, application, and audit logs:** Build an ingestion pipeline for web, application, and audit logs. **Business impact:** Staging reliability and release flow
- **BILL-1703 — Advanced — Recover a degraded logging cluster and prevent repeat shard exhaustion:** Recover a degraded logging cluster and prevent repeat shard exhaustion. **Business impact:** Customer-facing production reliability
- **BILL-1704 — Master — Design a compliant logging platform for engineering and security teams:** Design a compliant logging platform for engineering and security teams. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-017 — SEV-2 — Production degradation involving Centralized Logging & OpenSearch/ELK:** Recover a degraded logging cluster and prevent repeat shard exhaustion. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-017 — Enterprise Centralized Logging & OpenSearch/ELK delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Centralized Logging & OpenSearch/ELK as part of an end-to-end DevOps platform.

## 🛡️ DevSecOps & Supply-Chain Security

**Category:** Security  
**Included:** 16 lessons, 4 practice labs, 14 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Integrate identity, secrets, scanning, policy, provenance, and runtime controls into delivery workflows.

**Company relevance:** Security controls must operate continuously across source, dependencies, builds, artifacts, infrastructure, deployment, and runtime.

### Command and configuration examples

- `admission policy`
- `control mapping`
- `dependency scan`
- `evidence automation`
- `generate SBOM`
- `least privilege review`
- `policy evaluate`
- `risk acceptance`
- `scan image`
- `scan source`
- `scan Terraform`
- `secret scan`
- `sign artifact`
- `verify provenance`

### Learning and practice by level

#### Beginner

**Company workflow:** A developer removes hard-coded secrets, fixes critical findings, and records an approved exception when necessary.

**Lessons:** Least Privilege; Secret Handling; Basic Scanning; Secure Defaults

- **devsecops-lab-1 — Beginner company lab:** Identify and remediate secrets and vulnerable dependencies in a sample repository.

#### Intermediate

**Company workflow:** An engineer integrates multiple scanners, deduplicates findings, applies severity thresholds, and avoids blocking on low-confidence noise.

**Lessons:** Sast And Dast; Container Scanning; Iac Scanning; Policy Gates

- **devsecops-lab-2 — Intermediate company lab:** Build a risk-based pipeline gate with evidence and exception expiry.

#### Advanced

**Company workflow:** A senior engineer produces provenance, signs artifacts, uses short-lived identity, models threats, and monitors runtime drift.

**Lessons:** Sbom And Signing; Oidc; Threat Modeling; Runtime Controls

- **devsecops-lab-3 — Advanced company lab:** Secure a container supply chain from commit to production admission.

#### Master

**Company workflow:** A security platform lead provides reusable controls, measures risk reduction, maps evidence to controls, and runs response exercises.

**Lessons:** Security Platform; Risk Governance; Compliance Evidence; Incident Response

- **devsecops-lab-4 — Master company lab:** Design a DevSecOps operating model for regulated software delivery.

### Company tickets

- **BILL-1801 — Beginner — Identify and remediate secrets and vulnerable dependencies in a sample repository:** Identify and remediate secrets and vulnerable dependencies in a sample repository. **Business impact:** Internal team productivity
- **BILL-1802 — Intermediate — Build a risk-based pipeline gate with evidence and exception expiry:** Build a risk-based pipeline gate with evidence and exception expiry. **Business impact:** Staging reliability and release flow
- **BILL-1803 — Advanced — Secure a container supply chain from commit to production admission:** Secure a container supply chain from commit to production admission. **Business impact:** Customer-facing production reliability
- **BILL-1804 — Master — Design a DevSecOps operating model for regulated software delivery:** Design a DevSecOps operating model for regulated software delivery. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-018 — SEV-1 — Production degradation involving DevSecOps & Supply-Chain Security:** Secure a container supply chain from commit to production admission. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-018 — Enterprise DevSecOps & Supply-Chain Security delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using DevSecOps & Supply-Chain Security as part of an end-to-end DevOps platform.

## 🚨 SRE & Incident Management

**Category:** Operations  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Operate services with SLOs, error budgets, incident response, capacity planning, and continuous reliability improvement.

**Company relevance:** SRE practices balance reliability and delivery speed using measurable service objectives and disciplined operations.

### Command and configuration examples

- `availability SLI`
- `capacity model`
- `check dashboard`
- `communications lead`
- `declare incident`
- `error budget`
- `incident commander`
- `latency SLI`
- `open runbook`
- `operations lead`
- `record timeline`
- `reliability roadmap`
- `risk register`
- `service tiering`
- `toil register`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior responder acknowledges an alert, checks the runbook, gathers evidence, communicates status, and escalates early.

**Lessons:** Service Health; Runbooks; On-Call Basics; Incident Severity

- **sre-lab-1 — Beginner company lab:** Respond to a simulated service outage using a clear incident checklist.

#### Intermediate

**Company workflow:** An engineer defines user-centered indicators, reviews budget consumption, writes a blameless postmortem, and automates repetitive work.

**Lessons:** Slis And Slos; Error Budgets; Postmortems; Toil Reduction

- **sre-lab-2 — Intermediate company lab:** Create an SLO and postmortem for an API with recurring latency incidents.

#### Advanced

**Company workflow:** A senior engineer coordinates roles, manages communications, models demand, tests failure modes, and negotiates dependency objectives.

**Lessons:** Incident Command; Capacity Planning; Chaos Testing; Dependency Reliability

- **sre-lab-3 — Advanced company lab:** Run a game day for loss of a critical dependency and produce actions.

#### Master

**Company workflow:** An SRE lead aligns investment with risk, creates reliability tiers, governs exceptions, and reports business impact.

**Lessons:** Reliability Strategy; Organizational Incentives; Platform Resilience; Executive Reporting

- **sre-lab-4 — Master company lab:** Design a reliability program for a portfolio of business-critical services.

### Company tickets

- **BILL-1901 — Beginner — Respond to a simulated service outage using a clear incident checklist:** Respond to a simulated service outage using a clear incident checklist. **Business impact:** Internal team productivity
- **BILL-1902 — Intermediate — Create an SLO and postmortem for an API with recurring latency incidents:** Create an SLO and postmortem for an API with recurring latency incidents. **Business impact:** Staging reliability and release flow
- **BILL-1903 — Advanced — Run a game day for loss of a critical dependency and produce actions:** Run a game day for loss of a critical dependency and produce actions. **Business impact:** Customer-facing production reliability
- **BILL-1904 — Master — Design a reliability program for a portfolio of business-critical services:** Design a reliability program for a portfolio of business-critical services. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-019 — SEV-2 — Production degradation involving SRE & Incident Management:** Run a game day for loss of a critical dependency and produce actions. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-019 — Enterprise SRE & Incident Management delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using SRE & Incident Management as part of an end-to-end DevOps platform.

## 🏗️ System Design & Platform Engineering

**Category:** Architecture  
**Included:** 16 lessons, 4 practice labs, 15 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Design scalable systems and internal platforms that improve developer productivity and operational consistency.

**Company relevance:** Senior DevOps and platform roles require architectural trade-offs, service boundaries, reliability, security, and product thinking.

### Command and configuration examples

- `architecture decision record`
- `backpressure`
- `capacity estimate`
- `circuit breaker`
- `context diagram`
- `control plane`
- `data plane`
- `developer experience metrics`
- `functional requirements`
- `idempotency`
- `non-functional requirements`
- `RTO and RPO`
- `sequence diagram`
- `tenant boundary`
- `unit economics`

### Learning and practice by level

#### Beginner

**Company workflow:** An engineer clarifies users, traffic, constraints, dependencies, and failure expectations before drawing components.

**Lessons:** Requirements; Components And Data Flow; Availability Basics; Documentation

- **system-design-lab-1 — Beginner company lab:** Design a small deployment service and explain its request flow.

#### Intermediate

**Company workflow:** An engineer estimates load, chooses stateless boundaries, adds queues and caches deliberately, and defines retries and timeouts.

**Lessons:** Scaling Patterns; Caching And Queues; Data Choices; Failure Handling

- **system-design-lab-2 — Intermediate company lab:** Design a build-event processing system that handles bursts safely.

#### Advanced

**Company workflow:** A senior engineer defines failure domains, consistency, tenant isolation, identity, audit, and operational controls.

**Lessons:** Multi-Region Design; Platform Apis; Tenancy; Security Architecture

- **system-design-lab-3 — Advanced company lab:** Design a multi-tenant internal deployment platform with regional recovery.

#### Master

**Company workflow:** A platform leader measures adoption and outcomes, maintains paved roads, funds reliability, and evolves architecture through evidence.

**Lessons:** Platform As Product; Economics; Governance; Evolutionary Architecture

- **system-design-lab-4 — Master company lab:** Create a three-year platform strategy with product roadmap, operating model, and success metrics.

### Company tickets

- **BILL-2001 — Beginner — Design a small deployment service and explain its request flow:** Design a small deployment service and explain its request flow. **Business impact:** Internal team productivity
- **BILL-2002 — Intermediate — Design a build-event processing system that handles bursts safely:** Design a build-event processing system that handles bursts safely. **Business impact:** Staging reliability and release flow
- **BILL-2003 — Advanced — Design a multi-tenant internal deployment platform with regional recovery:** Design a multi-tenant internal deployment platform with regional recovery. **Business impact:** Customer-facing production reliability
- **BILL-2004 — Master — Create a three-year platform strategy with product roadmap, operating model, and success metrics:** Create a three-year platform strategy with product roadmap, operating model, and success metrics. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-020 — SEV-2 — Production degradation involving System Design & Platform Engineering:** Design a multi-tenant internal deployment platform with regional recovery. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-020 — Enterprise System Design & Platform Engineering delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using System Design & Platform Engineering as part of an end-to-end DevOps platform.

## 🗄️ Databases for DevOps

**Category:** Data  
**Included:** 16 lessons, 4 practice labs, 14 unique command/configuration examples, 12 test questions, 16 interview questions, 4 company tickets, 1 incident, 1 capstone.

Operate relational and NoSQL databases with safe changes, backup, observability, and recovery.

**Company relevance:** Applications depend on data systems, and deployment or infrastructure changes can create irreversible data risk.

### Command and configuration examples

- `backup command`
- `connection test`
- `EXPLAIN`
- `failover rehearsal`
- `migration up/down`
- `PITR target`
- `pool metrics`
- `replica lag`
- `restore verify`
- `retention policy`
- `RPO tiers`
- `RTO tiers`
- `SELECT 1`
- `slow query log`

### Learning and practice by level

#### Beginner

**Company workflow:** A junior engineer checks connectivity and capacity, performs an approved backup, and verifies the backup file and logs.

**Lessons:** Relational Concepts; Connections; Backups; Basic Monitoring

- **databases-lab-1 — Beginner company lab:** Create a backup and restore validation checklist for a small database.

#### Intermediate

**Company workflow:** An engineer stages a backward-compatible migration, checks query plans, monitors replicas, and validates application pools.

**Lessons:** Indexes And Queries; Replication; Migrations; Connection Pooling

- **databases-lab-2 — Intermediate company lab:** Plan a zero-downtime schema change for a busy application.

#### Advanced

**Company workflow:** A senior engineer tests failover and PITR, reviews encryption and access, and resolves bottlenecks using evidence.

**Lessons:** High Availability; Point-In-Time Recovery; Data Security; Performance

- **databases-lab-3 — Advanced company lab:** Recover a database to a point before an accidental change and document data loss.

#### Master

**Company workflow:** A platform lead defines service tiers, backup objectives, ownership, audit, and managed-service standards.

**Lessons:** Data Platform Governance; Resilience Tiers; Capacity Economics; Compliance

- **databases-lab-4 — Master company lab:** Design a database platform operating model for multiple application teams.

### Company tickets

- **BILL-2101 — Beginner — Create a backup and restore validation checklist for a small database:** Create a backup and restore validation checklist for a small database. **Business impact:** Internal team productivity
- **BILL-2102 — Intermediate — Plan a zero-downtime schema change for a busy application:** Plan a zero-downtime schema change for a busy application. **Business impact:** Staging reliability and release flow
- **BILL-2103 — Advanced — Recover a database to a point before an accidental change and document data loss:** Recover a database to a point before an accidental change and document data loss. **Business impact:** Customer-facing production reliability
- **BILL-2104 — Master — Design a database platform operating model for multiple application teams:** Design a database platform operating model for multiple application teams. **Business impact:** Enterprise platform, governance, and business continuity

### Production incident

- **INC-021 — SEV-1 — Production degradation involving Databases for DevOps:** Recover a database to a point before an accidental change and document data loss. **Customer impact:** Customer-facing production reliability

### Enterprise capstone

- **CAP-021 — Enterprise Databases for DevOps delivery project:** Design, implement, validate, secure, document, and operationalize a company-grade solution using Databases for DevOps as part of an end-to-end DevOps platform.
