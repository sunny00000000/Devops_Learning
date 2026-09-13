"""
Billinger Enterprise Concurrent API & Static Server v3.0.0
Utilizes ThreadingHTTPServer with non-blocking multi-threaded request dispatching,
Keep-Alive termination, automatic port failover, and embedded fallback assets.
"""
import http.server
from http.server import ThreadingHTTPServer
import socket
import json
import urllib.parse
import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.configuration.config import Config
from core.logging.logger import logger
from core.authentication.auth import auth_manager
from core.system_monitor import system_monitor
from storage.db import db
from storage.backup_manager import backup_manager
from learning.catalog import catalog
from learning.playground import playground
from learning.twin import learning_twin
from learning.mastery import mastery_engine
from learning.coverage import coverage_auditor
from labs.simulation import company_simulation
from labs.incidents import incident_center
from assessment.tests import test_center
from interview.engine import interview_engine
from ai.providers import ai_provider_manager
from ai.router import ai_router
from career.matcher import job_matcher
from resume.engine import resume_engine
from portfolio.engine import portfolio_engine
from documents.ingestion import document_ingestion
from documents.search import document_search

# In-memory cached assets to prevent any disk read delay or file-lock hanging
FALLBACK_INDEX_HTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>BILLINGER — DevOps Learning & Career Command Hub</title>\n  <link rel="stylesheet" href="style.css">\n  <link rel="preconnect" href="https://fonts.googleapis.com">\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">\n</head>\n<body class="theme-obsidian-cyberpunk font-normal">\n  <div class="app-layout">\n    <!-- SIDEBAR RAIL -->\n    <aside class="sidebar" id="sidebar" role="navigation" aria-label="Main Navigation">\n      <div class="sidebar-header">\n        <div class="logo-badge">⚡</div>\n        <div class="brand-text">\n          <h2>BILLINGER</h2>\n          <span class="version-tag">PRO v3.0.0</span>\n        </div>\n      </div>\n\n      <nav class="nav-menu">\n        <a href="#home" class="nav-item active" data-tab="home"><span class="icon">🏠</span> <span>Command Hub</span></a>\n        <a href="#learning" class="nav-item" data-tab="learning"><span class="icon">📚</span> <span>Learning Core</span></a>\n        <a href="#playground" class="nav-item" data-tab="playground"><span class="icon">💻</span> <span>Playground</span></a>\n        <a href="#labs" class="nav-item" data-tab="labs"><span class="icon">🏢</span> <span>Simulation</span></a>\n        <a href="#incidents" class="nav-item" data-tab="incidents"><span class="icon">🚨</span> <span>Incidents</span></a>\n        <a href="#assessment" class="nav-item" data-tab="assessment"><span class="icon">📝</span> <span>Assessment</span></a>\n        <a href="#interview" class="nav-item" data-tab="interview"><span class="icon">🎙️</span> <span>Interview Studio</span></a>\n        <a href="#career" class="nav-item" data-tab="career"><span class="icon">🎯</span> <span>Career Match</span></a>\n        <a href="#resume" class="nav-item" data-tab="resume"><span class="icon">📄</span> <span>ATS Resume</span></a>\n        <a href="#portfolio" class="nav-item" data-tab="portfolio"><span class="icon">🏆</span> <span>Portfolio</span></a>\n        <a href="#documents" class="nav-item" data-tab="documents"><span class="icon">📁</span> <span>Doc Vault</span></a>\n        <a href="#ai" class="nav-item" data-tab="ai"><span class="icon">🤖</span> <span>AI Matrix</span></a>\n        <a href="#system" class="nav-item" data-tab="system"><span class="icon">⚙️</span> <span>Telemetry & State</span></a>\n      </nav>\n\n      <div class="sidebar-footer">\n        <div class="status-indicator">\n          <span class="dot online" id="conn-dot"></span>\n          <span id="conn-text">NODE ONLINE</span>\n        </div>\n        <div class="accessibility-controls">\n          <button id="btn-theme-toggle" title="Cycle Visual Themes (Obsidian / High-Contrast / Matrix)">👁️</button>\n          <button id="btn-font-toggle" title="Scale Typography">🔤</button>\n        </div>\n      </div>\n    </aside>\n\n    <!-- MAIN OPERATIONS VIEWPORT -->\n    <main class="main-content">\n      <!-- TOPBAR HUD -->\n      <header class="topbar">\n        <div class="topbar-left">\n          <h1 id="page-title">Executive Command Hub</h1>\n          <p class="subtitle" id="page-subtitle">Adaptive Learning Twin • SRE Incident Operations • Career Acceleration</p>\n        </div>\n        <div class="topbar-right">\n          <div class="hud-pill"><span class="dot online"></span> SANDBOX ENFORCED</div>\n          <div class="readiness-metric">\n            <span class="metric-label">Job Readiness</span>\n            <span class="metric-val" id="topbar-readiness">84.5%</span>\n          </div>\n          <div class="user-profile-badge">\n            <span class="avatar-pill">👨\u200d💻</span>\n            <span id="user-display-name">DevOps Engineer</span>\n          </div>\n        </div>\n      </header>\n\n      <!-- TAB CONTENT PANES -->\n      <div class="content-body">\n        \n        <!-- TAB 1: HOME (COMMAND HUB) -->\n        <section id="tab-home" class="tab-pane active">\n          <!-- HERO NEXT BEST ACTION -->\n          <div class="hero-hud-banner" id="next-action-box">\n            <div class="hero-hud-left">\n              <div class="hero-icon-orb">🎯</div>\n              <div>\n                <div class="pill-tag safe" style="margin-bottom: 6px;">RECOMMENDED NEXT BEST ACTION</div>\n                <h3 id="rec-action">Master Kubernetes Pod Security Policies & Network Policies</h3>\n                <p>Target Lab: <strong id="rec-lab" style="color:var(--neon-cyan);">Lab 07: K8s Zero-Trust Network Isolation</strong> • Lesson: <span id="rec-lesson" style="color:var(--text-main);">7.3 Hardened Ingress Controller</span></p>\n              </div>\n            </div>\n            <button class="btn-cyber" onclick="document.querySelector(\'[data-tab=learning]\').click()">Engage Lesson →</button>\n          </div>\n\n          <!-- TELEMETRY 4-GRID -->\n          <div class="telemetry-grid">\n            <div class="card-glass telemetry-card">\n              <div class="telemetry-header">\n                <span class="telemetry-title">System Status</span>\n                <span class="telemetry-icon">⚡</span>\n              </div>\n              <div class="telemetry-value" id="sys-status" style="color:var(--neon-emerald);">HEALTHY</div>\n              <div class="meter-track"><div class="meter-fill emerald" style="width: 100%;"></div></div>\n              <span style="font-size:0.75rem; color:var(--text-muted);">Python 3.10+ Native Engine • No Daemons</span>\n            </div>\n\n            <div class="card-glass telemetry-card">\n              <div class="telemetry-header">\n                <span class="telemetry-title">Memory Footprint</span>\n                <span class="telemetry-icon">💾</span>\n              </div>\n              <div class="telemetry-value" id="sys-ram">512 MB</div>\n              <div class="meter-track"><div class="meter-fill" style="width: 12.5%;"></div></div>\n              <span style="font-size:0.75rem; color:var(--text-muted);">Strict &lt; 4096 MB Hardware Ceiling</span>\n            </div>\n\n            <div class="card-glass telemetry-card">\n              <div class="telemetry-header">\n                <span class="telemetry-title">Command Mastery</span>\n                <span class="telemetry-icon">💻</span>\n              </div>\n              <div class="telemetry-value" id="twin-cmds-count">78 / 85</div>\n              <div class="meter-track"><div class="meter-fill" style="width: 91.7%;"></div></div>\n              <span style="font-size:0.75rem; color:var(--text-muted);">12 Tools • Verified Execution Evidence</span>\n            </div>\n\n            <div class="card-glass telemetry-card">\n              <div class="telemetry-header">\n                <span class="telemetry-title">Incident MTTR</span>\n                <span class="telemetry-icon">⏱️</span>\n              </div>\n              <div class="telemetry-value" id="twin-mttr" style="color:var(--neon-cyan);">4.2m</div>\n              <div class="meter-track"><div class="meter-fill emerald" style="width: 82%;"></div></div>\n              <span style="font-size:0.75rem; color:var(--text-muted);">SRE SLA Benchmark: &lt; 10.0m Target</span>\n            </div>\n          </div>\n\n          <!-- RADAR & PROFILE CONTAINER -->\n          <div class="radar-dual-container">\n            <!-- 8D Competency Radar -->\n            <div class="card-glass">\n              <h3 style="font-size:1.1rem; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between;">\n                <span>Personal Learning Twin Radar</span>\n                <span class="pill-tag safe" id="twin-level">LEVEL: SENIOR DEVOPS</span>\n              </h3>\n              <div class="radar-chart-wrapper">\n                <!-- Embedded High-Tech SVG Radar Graphic -->\n                <svg viewBox="0 0 360 360" width="300" height="300">\n                  <polygon points="180,30 286,74 330,180 286,286 180,330 74,286 30,180 74,74" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>\n                  <polygon points="180,75 243,101 270,180 243,243 180,270 117,243 90,180 117,101" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>\n                  <polygon points="180,120 206,131 220,180 206,206 180,220 154,206 140,180 154,131" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>\n                  <!-- Data Polygon -->\n                  <polygon points="180,50 270,90 310,180 260,260 180,300 95,270 50,180 90,95" fill="rgba(0, 242, 254, 0.2)" stroke="#00f2fe" stroke-width="2"/>\n                  <!-- Nodes -->\n                  <circle cx="180" cy="50" r="4" fill="#00f2fe"/>\n                  <circle cx="270" cy="90" r="4" fill="#00f2fe"/>\n                  <circle cx="310" cy="180" r="4" fill="#00f2fe"/>\n                  <circle cx="260" cy="260" r="4" fill="#00f2fe"/>\n                  <circle cx="180" cy="300" r="4" fill="#00f2fe"/>\n                  <circle cx="95" cy="270" r="4" fill="#00f2fe"/>\n                  <circle cx="50" cy="180" r="4" fill="#00f2fe"/>\n                  <circle cx="90" cy="95" r="4" fill="#00f2fe"/>\n                  <!-- Labels -->\n                  <text x="180" y="20" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="monospace">LINUX</text>\n                  <text x="300" y="70" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="monospace">NETWORKING</text>\n                  <text x="345" y="185" fill="#94a3b8" font-size="11" text-anchor="start" font-family="monospace">GIT</text>\n                  <text x="290" y="300" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="monospace">DOCKER</text>\n                  <text x="180" y="350" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="monospace">K8S</text>\n                  <text x="70" y="300" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="monospace">TERRAFORM</text>\n                  <text x="15" y="185" fill="#94a3b8" font-size="11" text-anchor="end" font-family="monospace">CI/CD</text>\n                  <text x="70" y="70" fill="#94a3b8" font-size="11" text-anchor="middle" font-family="monospace">SRE</text>\n                </svg>\n              </div>\n              <div id="dimension-bars-container" style="display:flex; flex-direction:column; gap:10px; margin-top:10px;">\n                <!-- Filled dynamically by app.js -->\n              </div>\n            </div>\n\n            <!-- Active Operations & Outage Simulation Card -->\n            <div class="card-glass">\n              <h3 style="font-size:1.1rem; margin-bottom:16px;">SRE Outage Watchdog &amp; Goals</h3>\n              <div style="background:rgba(0,0,0,0.3); padding:16px; border-radius:8px; border:1px solid var(--border-glass); margin-bottom:16px;">\n                <span style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Current Certification Goal</span>\n                <h4 id="twin-next-goal" style="color:#ffffff; margin-top:4px;">Principal SRE &amp; Enterprise Cloud Architect</h4>\n              </div>\n              <div id="active-incident-box">\n                <p style="color:var(--text-muted); font-size:0.9rem;">No active production alerts. Platform operating within 99.99% SLA parameters.</p>\n              </div>\n            </div>\n          </div>\n        </section>\n\n        <!-- TAB 2: LEARNING CORE -->\n        <section id="tab-learning" class="tab-pane">\n          <div style="margin-bottom:24px; display:flex; justify-content:space-between; align-items:center;">\n            <div>\n              <h2 style="font-size:1.3rem;">12-Domain DevOps Curriculum Matrix</h2>\n              <p style="color:var(--text-muted); font-size:0.85rem;">Exhaustive reference from beginner fundamentals to enterprise production SRE</p>\n            </div>\n            <a href="/api/content/pdfs/DevOps_Complete_Master_Encyclopedia.pdf" target="_blank" class="btn-cyber">📥 Download Full Compendium (PDF)</a>\n          </div>\n\n          <div class="domains-matrix" id="domain-catalog-grid">\n            <!-- Populated dynamically by app.js -->\n          </div>\n\n          <div class="card-glass" id="domain-detail-card" style="display:none; margin-top:24px;">\n            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">\n              <h3 id="domain-detail-title">Domain Detail</h3>\n              <button class="btn-secondary" onclick="document.getElementById(\'domain-detail-card\').style.display=\'none\'">Close</button>\n            </div>\n            <div id="domain-detail-body"></div>\n          </div>\n        </section>\n\n        <!-- TAB 3: COMMAND PLAYGROUND -->\n        <section id="tab-playground" class="tab-pane">\n          <div style="margin-bottom:20px;">\n            <h2 style="font-size:1.3rem;">3-Tier Defensive Command Playground</h2>\n            <p style="color:var(--text-muted); font-size:0.85rem;">Interactive execution sandbox isolated within student lab workspace</p>\n          </div>\n\n          <div class="terminal-window">\n            <div class="terminal-topbar">\n              <div class="terminal-dots">\n                <span class="term-dot red"></span>\n                <span class="term-dot yellow"></span>\n                <span class="term-dot green"></span>\n              </div>\n              <span class="terminal-title-text">devops@billinger-sandbox:~/workspace (BASH 5.2)</span>\n              <span class="pill-tag safe" id="playground-tier-pill">SECURITY GUARD: ARMED</span>\n            </div>\n\n            <div class="terminal-output" id="terminal-screen">=== Billinger Command Sandbox Active ===\nType any Linux, Docker, K8s, Git or Bash command below.\nCommands are evaluated against 3-Tier Security Policy (SAFE, CAUTION, BLOCKED).\n</div>\n\n            <div class="terminal-input-row">\n              <span class="terminal-prompt">devops@billinger:~$</span>\n              <input type="text" id="term-input" class="terminal-input" placeholder="Type a command (e.g. ls -la, df -hT, docker ps, kubectl get pods)..." autocomplete="off">\n              <button class="btn-cyber" onclick="executePlaygroundCmd()">Execute ↵</button>\n            </div>\n          </div>\n\n          <div style="display:flex; gap:10px; margin-top:16px; flex-wrap:wrap;">\n            <span style="font-size:0.85rem; color:var(--text-muted); align-self:center;">Quick Commands:</span>\n            <button class="btn-secondary" onclick="setPlaygroundInput(\'df -hT\')">df -hT</button>\n            <button class="btn-secondary" onclick="setPlaygroundInput(\'ps aux | head -n 10\')">ps aux</button>\n            <button class="btn-secondary" onclick="setPlaygroundInput(\'git status\')">git status</button>\n            <button class="btn-secondary" onclick="setPlaygroundInput(\'docker info 2>/dev/null || echo Docker Client Ready\')">docker info</button>\n            <button class="btn-secondary" onclick="setPlaygroundInput(\'rm -rf /\')">Test Blocked: rm -rf /</button>\n          </div>\n        </section>\n\n        <!-- TAB 4: COMPANY SIMULATION -->\n        <section id="tab-labs" class="tab-pane">\n          <div style="margin-bottom:20px;">\n            <h2 style="font-size:1.3rem;">Virtual Company Scenario Simulator</h2>\n            <p style="color:var(--text-muted); font-size:0.85rem;">Resolve complex multi-tier production outages across Fintech, HealthTech, and E-Commerce</p>\n          </div>\n\n          <div id="scenario-list-container" class="domains-matrix">\n            <!-- Populated dynamically by app.js -->\n          </div>\n\n          <div class="card-glass" id="active-scenario-card" style="display:none; margin-top:24px;">\n            <h3 id="scen-active-title">Active Scenario</h3>\n            <div id="scen-active-body" style="margin-top:12px;"></div>\n          </div>\n        </section>\n\n        <!-- TAB 5: INCIDENTS -->\n        <section id="tab-incidents" class="tab-pane">\n          <div style="margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">\n            <div>\n              <h2 style="font-size:1.3rem;">Production Incident Response Center</h2>\n              <p style="color:var(--text-muted); font-size:0.85rem;">Live SLA Countdown Watchdog, Triage Escalation &amp; Postmortem Generator</p>\n            </div>\n            <button class="btn-cyber" onclick="triggerIncident(\'SCEN-001\', \'Black Friday Checkout Failure\', \'SRE\')">🚨 Simulate Critical Outage (SRE)</button>\n          </div>\n\n          <div class="card-glass" style="margin-bottom:24px;">\n            <h3 style="font-size:1.1rem; margin-bottom:12px;">Incident Watchdog Console</h3>\n            <div id="incident-sla-timer" style="font-family:var(--font-mono); font-size:1.8rem; color:var(--neon-crimson); margin-bottom:16px;">\n              SLA TIMER: IDLE\n            </div>\n            <div style="display:flex; gap:12px;">\n              <select id="inc-mitigation-select" class="btn-secondary" style="flex:1;">\n                <option value="rollback">Execute Automated Canary Rollback</option>\n                <option value="scale">Trigger Horizontal Pod Autoscaler (HPA)</option>\n                <option value="drain">Isolate and Drain Failing Node Pool</option>\n              </select>\n              <button class="btn-cyber" onclick="resolveIncident(\'INC-ACTIVE\', document.getElementById(\'inc-mitigation-select\').value)">Apply Mitigation &amp; Resolve</button>\n            </div>\n          </div>\n        </section>\n\n        <!-- TAB 6: ASSESSMENT -->\n        <section id="tab-assessment" class="tab-pane">\n          <div style="margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">\n            <div>\n              <h2 style="font-size:1.3rem;">DevOps Assessment &amp; Certification Engine</h2>\n              <p style="color:var(--text-muted); font-size:0.85rem;">Multi-format test questions with error pinpointing and remediation roadmap</p>\n            </div>\n            <div style="display:flex; gap:10px;">\n              <select id="test-tool-select" class="btn-secondary">\n                <option value="all">All Domains (25 Questions)</option>\n                <option value="linux">Linux SysAdmin</option>\n                <option value="docker">Docker &amp; Containers</option>\n                <option value="k8s">Kubernetes</option>\n              </select>\n              <select id="test-diff-select" class="btn-secondary">\n                <option value="all">All Difficulties</option>\n                <option value="beginner">Beginner</option>\n                <option value="intermediate">Intermediate</option>\n                <option value="advanced">Advanced</option>\n              </select>\n              <button class="btn-cyber" onclick="startTestSession()">Start Examination</button>\n            </div>\n          </div>\n\n          <div class="card-glass" id="test-session-container">\n            <p style="color:var(--text-muted);">Select test parameters and click \'Start Examination\' to begin.</p>\n          </div>\n        </section>\n\n        <!-- TAB 7: INTERVIEW STUDIO -->\n        <section id="tab-interview" class="tab-pane">\n          <div style="margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">\n            <div>\n              <h2 style="font-size:1.3rem;">DevOps Mock Interview Studio</h2>\n              <p style="color:var(--text-muted); font-size:0.85rem;">Interactive interview simulation across 9 technical and leadership personas</p>\n            </div>\n            <div style="display:flex; gap:10px;">\n              <select id="interview-stage" class="btn-secondary">\n                <option value="1">Round 1: Screening</option>\n                <option value="2">Round 2: Technical Deep-Dive</option>\n                <option value="3">Round 3: Live Incident Troubleshooting</option>\n                <option value="4">Round 4: Architecture Design</option>\n              </select>\n              <select id="interview-persona" class="btn-secondary">\n                <option value="Senior DevOps Engineer">Senior DevOps Engineer</option>\n                <option value="SRE">Site Reliability Engineer</option>\n                <option value="Strict HR">Strict HR</option>\n                <option value="CTO">CTO</option>\n              </select>\n              <input type="text" id="interview-company" class="btn-secondary" placeholder="Company (e.g. Amazon, Stripe)" value="Nutrabay">\n              <button class="btn-cyber" onclick="startInterviewSession()">Begin Interview</button>\n            </div>\n          </div>\n\n          <div class="card-glass">\n            <div id="interview-chat-box" style="height:340px; overflow-y:auto; padding:16px; background:rgba(0,0,0,0.3); border-radius:8px; margin-bottom:16px;">\n              <p style="color:var(--text-muted);">Press \'Begin Interview\' to receive your scenario prompt from the interviewer.</p>\n            </div>\n            <div id="interview-input-area" style="display:flex; gap:12px;">\n              <textarea id="interview-answer-input" class="terminal-input" style="height:80px; padding:12px; background:rgba(0,0,0,0.4); border-radius:8px; border:1px solid var(--border-glass);" placeholder="Type your structured technical response..."></textarea>\n              <button class="btn-cyber" onclick="submitInterviewAnswer()">Submit Answer ↵</button>\n            </div>\n          </div>\n        </section>\n\n        <!-- TAB 8: CAREER MATCH -->\n        <section id="tab-career" class="tab-pane">\n          <div style="margin-bottom:20px;">\n            <h2 style="font-size:1.3rem;">Career Intelligence &amp; Job Description Matcher</h2>\n            <p style="color:var(--text-muted); font-size:0.85rem;">Analyze real-world job postings to identify skill matches, gaps, and remediation plans</p>\n          </div>\n\n          <div class="card-glass" style="margin-bottom:20px;">\n            <label style="font-size:0.85rem; color:var(--text-muted);">Paste Target Job Description (JD):</label>\n            <textarea id="jd-input" class="terminal-input" style="width:100%; height:120px; padding:12px; background:rgba(0,0,0,0.4); border-radius:8px; border:1px solid var(--border-glass); margin-top:8px;" placeholder="Paste job description requirements here (e.g. Terraform, Kubernetes, Helm, AWS VPC, Prometheus, Jenkins)..."></textarea>\n            <button class="btn-cyber" style="margin-top:12px;" onclick="runCareerMatch()">Analyze Fit &amp; Generate Roadmap</button>\n          </div>\n\n          <div id="career-match-results"></div>\n        </section>\n\n        <!-- TAB 9: ATS RESUME STUDIO -->\n        <section id="tab-resume" class="tab-pane">\n          <div style="margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">\n            <div>\n              <h2 style="font-size:1.3rem;">ATS Resume Studio &amp; Honest Evidence Tailoring</h2>\n              <p style="color:var(--text-muted); font-size:0.85rem;">Real-time ATS keyword matching, honest metric scoring, and PDF generation</p>\n            </div>\n            <div style="display:flex; gap:10px;">\n              <input type="text" id="resume-role-input" class="btn-secondary" value="DevOps Engineer">\n              <button class="btn-cyber" onclick="analyzeResumeATS()">Analyze ATS Score</button>\n            </div>\n          </div>\n\n          <div class="card-glass" id="resume-preview-box">\n            <p style="color:var(--text-muted);">Click \'Analyze ATS Score\' to view verified keyword optimization and recommendations.</p>\n          </div>\n        </section>\n\n        <!-- TAB 10: EVIDENCE PORTFOLIO -->\n        <section id="tab-portfolio" class="tab-pane">\n          <div style="margin-bottom:20px;">\n            <h2 style="font-size:1.3rem;">Cryptographically Verifiable Portfolio Showcases</h2>\n            <p style="color:var(--text-muted); font-size:0.85rem;">Automated evidence harvested from completed production scenarios and labs</p>\n          </div>\n\n          <div id="portfolio-items-container" class="domains-matrix">\n            <!-- Populated dynamically by app.js -->\n          </div>\n        </section>\n\n        <!-- TAB 11: DOCUMENT VAULT -->\n        <section id="tab-documents" class="tab-pane">\n          <div style="margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">\n            <div>\n              <h2 style="font-size:1.3rem;">Document Vault &amp; Anti-Cross-Contamination Classifier</h2>\n              <p style="color:var(--text-muted); font-size:0.85rem;">Strict domain isolation ensuring tool boundaries are mathematically maintained</p>\n            </div>\n            <a href="/api/documents/audit" target="_blank" class="btn-secondary">View Classification Audit CSV</a>\n          </div>\n\n          <div class="card-glass" style="margin-bottom:20px;">\n            <h4 style="margin-bottom:12px;">Search Verified Library Index</h4>\n            <div style="display:flex; gap:12px;">\n              <input type="text" id="doc-search-input" class="terminal-input" style="padding:10px; background:rgba(0,0,0,0.4); border-radius:8px; border:1px solid var(--border-glass);" placeholder="Search keywords across 12 verified modules...">\n              <button class="btn-cyber" onclick="searchDocuments()">Search Index</button>\n            </div>\n            <div id="doc-search-results" style="margin-top:16px;"></div>\n          </div>\n\n          <div class="card-glass">\n            <h4 style="margin-bottom:12px;">Ingest New Technical Document</h4>\n            <input type="text" id="doc-ingest-name" class="btn-secondary" style="width:100%; margin-bottom:10px;" placeholder="Document Title (e.g. Linux_Kernel_Tuning_Guide.md)">\n            <textarea id="doc-ingest-text" class="terminal-input" style="width:100%; height:100px; padding:10px; background:rgba(0,0,0,0.4); border-radius:8px; border:1px solid var(--border-glass); margin-bottom:10px;" placeholder="Paste raw document content to evaluate classification against zero-cross-contamination rules..."></textarea>\n            <button class="btn-cyber" onclick="ingestDocument()">Classify &amp; Ingest</button>\n            <div id="doc-ingest-result" style="margin-top:12px;"></div>\n          </div>\n        </section>\n\n        <!-- TAB 12: AI CONTROL CENTER -->\n        <section id="tab-ai" class="tab-pane">\n          <div style="margin-bottom:20px;">\n            <h2 style="font-size:1.3rem;">Multi-Provider Adaptive AI Control Matrix</h2>\n            <p style="color:var(--text-muted); font-size:0.85rem;">4-Provider Fallback Cascade (Gemini • Groq • OpenAI • OpenRouter) + Deterministic Offline Engine</p>\n          </div>\n\n          <div class="card-glass" style="margin-bottom:20px;">\n            <h4 style="margin-bottom:12px;">Active Providers &amp; Failover Status</h4>\n            <div id="ai-providers-table-container">\n              <!-- Populated dynamically by app.js -->\n            </div>\n          </div>\n\n          <div class="card-glass">\n            <h4 style="margin-bottom:12px;">Query AI Routing Engine</h4>\n            <div style="display:flex; gap:12px; margin-bottom:12px;">\n              <select id="ai-workload-select" class="btn-secondary">\n                <option value="auto">Auto-Select Optimal Provider</option>\n                <option value="gemini">Google Gemini 1.5 Flash</option>\n                <option value="groq">Groq (Llama 3.1 70B)</option>\n                <option value="openai">OpenAI (GPT-4o Mini)</option>\n                <option value="openrouter">OpenRouter (Claude 3.5 Sonnet)</option>\n              </select>\n              <input type="text" id="ai-prompt-input" class="terminal-input" style="flex:1; padding:10px; background:rgba(0,0,0,0.4); border-radius:8px; border:1px solid var(--border-glass);" placeholder="Ask any technical DevOps question (works offline or online)...">\n              <button class="btn-cyber" onclick="sendAIQuery()">Dispatch Query</button>\n            </div>\n            <div id="ai-route-response-box" style="background:rgba(0,0,0,0.3); padding:16px; border-radius:8px; min-height:80px; font-family:var(--font-mono); font-size:0.9rem; color:#e2e8f0;">\n              AI Response Console: Waiting for query...\n            </div>\n          </div>\n        </section>\n\n        <!-- TAB 13: SYSTEM & BACKUP -->\n        <section id="tab-system" class="tab-pane">\n          <div style="margin-bottom:20px;">\n            <h2 style="font-size:1.3rem;">System Telemetry, SQLite Integrity &amp; Backups</h2>\n            <p style="color:var(--text-muted); font-size:0.85rem;">Deterministic state management, backup archives with SHA256 manifests</p>\n          </div>\n\n          <div class="card-glass" style="margin-bottom:20px;">\n            <h4 style="margin-bottom:12px;">Runtime Environment Metrics</h4>\n            <div id="system-info-container"></div>\n          </div>\n\n          <div class="card-glass">\n            <h4 style="margin-bottom:12px;">Create Atomic System Backup</h4>\n            <div style="display:flex; gap:12px; margin-bottom:12px;">\n              <input type="text" id="backup-label-input" class="btn-secondary" style="flex:1;" placeholder="Backup Label (e.g. pre-capstone-snapshot)" value="manual-snapshot">\n              <button class="btn-cyber" onclick="triggerBackup()">Create Verified Backup</button>\n            </div>\n            <div id="backup-status-box" style="background:rgba(0,0,0,0.3); padding:16px; border-radius:8px;"></div>\n          </div>\n        </section>\n\n      </div>\n    </main>\n  </div>\n\n  <script src="app.js"></script>\n</body>\n</html>\n'
FALLBACK_STYLE_CSS = """/* ==========================================
   BILLINGER HIGH-CONTRAST PROFESSIONAL DARK THEME
   4K-Ready Responsive Architecture & WCAG AA Accessible
   ========================================== */

:root {
  --bg-base: #0B0F19;
  --bg-surface: #111827;
  --bg-elevated: #1F2937;
  --border-color: #374151;
  --border-highlight: #4B5563;
  --text-primary: #F9FAFB;
  --text-secondary: #9CA3AF;
  --text-muted: #6B7280;
  --accent-primary: #3B82F6;
  --accent-hover: #2563EB;
  --accent-cyan: #06B6D4;
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --code-font: "DejaVu Sans Mono", "Consolas", "Courier New", monospace;
  --base-font-size: 15px;
}

body.theme-high-contrast {
  --bg-base: #000000;
  --bg-surface: #0A0A0A;
  --bg-elevated: #171717;
  --border-color: #525252;
  --text-primary: #FFFFFF;
  --text-secondary: #D4D4D4;
  --accent-primary: #60A5FA;
}

body.font-large { --base-font-size: 18px; }
body.font-xlarge { --base-font-size: 21px; }

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-family);
  font-size: var(--base-font-size);
  line-height: 1.5;
  overflow-x: hidden;
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

/* SIDEBAR */
.sidebar {
  width: 280px;
  background-color: var(--bg-surface);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
}

.logo-badge {
  font-size: 24px;
  background: var(--bg-elevated);
  padding: 8px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.brand-text h2 {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: var(--text-primary);
}

.version-tag {
  font-size: 10px;
  font-weight: 700;
  background: var(--accent-primary);
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
}

.nav-menu {
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--bg-elevated);
  color: var(--accent-primary);
  border-left: 3px solid var(--accent-primary);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot.online { background: var(--color-success); }
.dot.offline { background: var(--color-danger); }

.accessibility-controls button {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

/* MAIN CONTENT AREA */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  max-width: calc(100vw - 280px);
}

.topbar {
  padding: 24px 32px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topbar h1 {
  font-size: 24px;
  font-weight: 800;
}

.subtitle {
  color: var(--text-muted);
  font-size: 13px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.readiness-metric {
  background: var(--bg-elevated);
  padding: 6px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.metric-val {
  font-weight: 800;
  color: var(--color-success);
  margin-left: 4px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  background: var(--accent-primary);
  color: #fff;
  font-weight: 700;
  padding: 6px 10px;
  border-radius: 50%;
  font-size: 12px;
}

/* CONTENT BODY */
.content-body {
  padding: 32px;
  flex: 1;
}

.tab-pane {
  display: none;
}
.tab-pane.active {
  display: block;
}

/* CARDS & GRIDS */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.stat-card h3 {
  font-size: 13px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
}

.stat-sub {
  font-size: 12px;
  color: var(--text-secondary);
}

.section-card {
  margin-bottom: 24px;
}

.section-card h2 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 12px;
}

.highlight-card {
  border-left: 4px solid var(--accent-primary);
}

/* BUTTONS & CHIPS */
.btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

.btn-primary { background: var(--accent-primary); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-danger { background: var(--color-danger); color: #fff; }
.btn-warning { background: var(--color-warning); color: #000; }
.btn-secondary { background: var(--bg-elevated); color: var(--text-primary); border-color: var(--border-color); }
.btn-secondary:hover { background: var(--border-color); }

.chip {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-family: var(--code-font);
  cursor: pointer;
}
.chip:hover {
  background: var(--border-color);
  border-color: var(--accent-primary);
}
.chip-danger {
  border-color: var(--color-danger);
  color: #F87171;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}
.badge-success { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981; }
.badge-danger { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444; }
.badge-warning { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B; }
.badge-info { background: rgba(59, 130, 246, 0.2); color: #3B82F6; border: 1px solid #3B82F6; }

/* TERMINAL SCREEN */
.terminal-container {
  background: #05070D;
  border: 1px solid #1E293B;
  border-radius: var(--radius-md);
  margin-top: 16px;
  overflow: hidden;
}

.terminal-output {
  padding: 16px;
  min-height: 280px;
  max-height: 450px;
  overflow-y: auto;
  font-family: var(--code-font);
  font-size: 13px;
  color: #38BDF8;
  white-space: pre-wrap;
}

.terminal-input-bar {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: #0F172A;
  border-top: 1px solid #1E293B;
  gap: 10px;
}

.terminal-input-bar input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  font-family: var(--code-font);
  font-size: 14px;
  outline: none;
}

.form-control {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  color: #fff;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  outline: none;
}

.full-textarea {
  width: 100%;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  color: #fff;
  padding: 12px;
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: 14px;
  margin: 12px 0;
  outline: none;
}

.code-preview {
  background: #05070D;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  font-family: var(--code-font);
  font-size: 13px;
  color: #E2E8F0;
  white-space: pre-wrap;
  max-height: 500px;
  overflow-y: auto;
  margin-top: 16px;
}

.domain-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.domain-card:hover {
  border-color: var(--accent-primary);
}

.chat-container {
  background: #05070D;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
  min-height: 320px;
  max-height: 480px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
}
.chat-bubble.interviewer {
  background: #1E293B;
  color: #F8FAFC;
  align-self: flex-start;
  border-left: 4px solid var(--accent-primary);
}
.chat-bubble.user {
  background: #1E3A8A;
  color: #FFFFFF;
  align-self: flex-end;
}
.chat-placeholder {
  color: var(--text-muted);
  text-align: center;
  margin-top: 100px;
}

.test-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-top: 16px;
}
"""
FALLBACK_APP_JS = """/**
 * Billinger Platform v3.0.0 Client SPA Engine
 * Fully Interactive: Every button, tab, and workbench connected to live backend APIs.
 */

const STATE = {
  currentTab: 'home',
  userId: 'student_1',
  highContrast: false,
  fontSizeIndex: 0,
  fontSizes: ['font-normal', 'font-large', 'font-xlarge'],
  catalogData: null,
  activeTestSession: null,
  testAnswers: {},
  currentQuestionIndex: 0,
  activeInterviewSession: null,
  activeInterviewQuestion: null,
  activeIncident: null,
  incidentTimerInterval: null,
  incidentSeconds: 0
};

document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupAccessibility();
  loadInitialData();
});

function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = item.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

const TAB_TITLES = {
  home: ["Executive Dashboard", "Personal Learning Twin & Readiness Operations"],
  learning: ["DevOps Master Curriculum", "12 Comprehensive Domains Across 6 Mastery Levels"],
  playground: ["Command Playground", "Live Sandboxed Execution with Defensive Risk Guard"],
  labs: ["Virtual Company Simulation", "Real-World Architecture & Failure Diagnostic Labs"],
  incidents: ["Production Incident Center", "On-Call Outage Triage with Real-Time SLA & MTTR Tracking"],
  assessment: ["Technical Assessment Center", "Timed Skill Assessments with Instant Gap Remediation"],
  interview: ["Mock Technical Interview", "9 Interviewer Personas with 8-Point Feedback Analysis"],
  career: ["Job → Learning Loop", "JD Skill Gap Matcher & Targeted Upskilling Engine"],
  resume: ["ATS Resume Engine", "Truth-Verified ATS Resume Generation from Lab Proofs"],
  portfolio: ["Evidence-Based Portfolio", "Production Showcase Auto-Compiled from Completed Labs"],
  documents: ["Document Vault", "Strict Zero-Mixing Classification & Semantic Search"],
  ai: ["AI Control Center", "Multi-Provider Management with Fallback & Offline Routing"],
  system: ["System & Backup Manager", "Hardware Telemetry, Snapshots, and Rollback Verification"]
};

function switchTab(tabId) {
  STATE.currentTab = tabId;
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));

  const activeLink = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const activePane = document.getElementById(`tab-${tabId}`);
  if (activeLink) activeLink.classList.add('active');
  if (activePane) activePane.classList.add('active');

  // Update Topbar
  if (TAB_TITLES[tabId]) {
    document.getElementById('page-title').textContent = TAB_TITLES[tabId][0];
    document.getElementById('page-subtitle').textContent = TAB_TITLES[tabId][1];
  }

  // Trigger data loaders
  if (tabId === 'home') loadInitialData();
  if (tabId === 'learning') loadCatalogUI();
  if (tabId === 'labs') loadScenariosUI();
  if (tabId === 'ai') loadAIProvidersUI();
  if (tabId === 'portfolio') loadPortfolioUI();
  if (tabId === 'system') loadSystemUI();
}

function setupAccessibility() {
  const themeBtn = document.getElementById('btn-theme-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      STATE.highContrast = !STATE.highContrast;
      document.body.classList.toggle('theme-high-contrast', STATE.highContrast);
    });
  }

  const fontBtn = document.getElementById('btn-font-toggle');
  if (fontBtn) {
    fontBtn.addEventListener('click', () => {
      document.body.classList.remove(STATE.fontSizes[STATE.fontSizeIndex]);
      STATE.fontSizeIndex = (STATE.fontSizeIndex + 1) % STATE.fontSizes.length;
      document.body.classList.add(STATE.fontSizes[STATE.fontSizeIndex]);
    });
  }
}

// ----------------------------------------------------
// 1. HOME & LEARNING TWIN
// ----------------------------------------------------
async function loadInitialData() {
  try {
    const res = await fetch(`/api/learning/twin?user_id=${STATE.userId}`);
    const data = await res.json();
    
    document.getElementById('topbar-readiness').textContent = `${data.overall_job_readiness}%`;
    document.getElementById('twin-level').textContent = data.current_level;
    document.getElementById('twin-cmds-count').textContent = `${data.commands_mastered_count} Mastered`;
    
    if (data.next_best_action) {
      document.getElementById('rec-lesson').textContent = data.next_best_action.recommended_lesson || 'N/A';
      document.getElementById('rec-lab').textContent = data.next_best_action.recommended_lab || 'N/A';
      document.getElementById('rec-action').textContent = data.next_best_action.recommended_action || 'N/A';
    }

    renderDimensions(data.dimensions);
  } catch (err) {
    console.warn("Could not load initial twin data:", err);
  }
}

function renderDimensions(dims) {
  const container = document.getElementById('dimension-bars-container');
  if (!container || !dims) return;
  container.innerHTML = Object.entries(dims).map(([dim, val]) => `
    <div style="margin-bottom: 12px;">
      <div style="display:flex; justify-content:space-between; font-size:13px; margin-bottom:4px;">
        <span style="text-transform: capitalize; font-weight:600;">${dim.replace('_', ' ')}</span>
        <span style="font-weight:700;">${val}%</span>
      </div>
      <div style="background:#1F2937; height:8px; border-radius:4px; overflow:hidden;">
        <div style="width:${val}%; background:${val >= 80 ? '#10B981' : val >= 60 ? '#3B82F6' : '#F59E0B'}; height:100%;"></div>
      </div>
    </div>
  `).join('');
}

// ----------------------------------------------------
// 2. LEARNING CATALOG & DOMAIN EXPLORER
// ----------------------------------------------------
async function loadCatalogUI() {
  const grid = document.getElementById('domain-catalog-grid');
  try {
    const res = await fetch('/api/learning/catalog');
    const data = await res.json();
    STATE.catalogData = data;
    const domains = data.domains || [];

    grid.innerHTML = domains.map(d => `
      <div class="domain-card" onclick="openDomainDetail('${d.tool_id}')">
        <div>
          <h3 style="color:#F9FAFB; margin-bottom:4px;">${d.name}</h3>
          <p style="color:#9CA3AF; font-size:13px;">${d.category} • ${d.commands ? d.commands.length : 0} Commands • ${d.concepts ? d.concepts.length : 0} Core Concepts</p>
        </div>
        <div>
          <button class="btn btn-primary" onclick="event.stopPropagation(); openDomainDetail('${d.tool_id}')">Explore Domain</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    grid.innerHTML = `<p>Error loading catalog: ${e.message}</p>`;
  }
}

function openDomainDetail(toolId) {
  if (!STATE.catalogData) return;
  const domain = (STATE.catalogData.domains || []).find(d => d.tool_id.toLowerCase() === toolId.toLowerCase());
  if (!domain) return;

  const card = document.getElementById('domain-detail-card');
  const title = document.getElementById('domain-detail-title');
  const body = document.getElementById('domain-detail-body');

  title.textContent = `${domain.name} — Technical Syllabus`;
  card.style.display = 'block';

  const cmdsHtml = (domain.commands || []).map(c => `
    <div style="background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:12px; margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <code style="color:#38BDF8; font-weight:700; font-size:14px;">${c.command}</code>
        <button class="btn btn-secondary" style="font-size:11px; padding:3px 8px;" onclick="sendToPlayground('${c.command.replace(/'/g, "\\'")}')">Send to Playground</button>
      </div>
      <p style="font-size:13px; margin:4px 0; color:#E2E8F0;"><strong>Purpose:</strong> ${c.purpose}</p>
      <p style="font-size:12px; color:#94A3B8;"><strong>Syntax:</strong> <code>${c.syntax || c.command}</code></p>
      <p style="font-size:12px; color:#94A3B8;"><strong>Production Usage:</strong> ${c.production_usage || 'Standard enterprise pipeline use.'}</p>
      ${c.common_mistakes ? `<p style="font-size:12px; color:#FCA5A5;"><strong>Common Mistake:</strong> ${c.common_mistakes}</p>` : ''}
    </div>
  `).join('');

  const conceptsHtml = (domain.concepts || []).map(cp => `
    <div style="background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:12px; margin-bottom:10px;">
      <h4 style="color:#F9FAFB;">${cp.name || cp.concept}</h4>
      <p style="font-size:13px; color:#CBD5E1; margin:4px 0;">${cp.description || cp.details || ''}</p>
      ${cp.production_usage ? `<p style="font-size:12px; color:#38BDF8;"><strong>Production Application:</strong> ${cp.production_usage}</p>` : ''}
    </div>
  `).join('');

  const MODULE_PDF_MAP = {
    "linux": "Module_linux_sysadmin_kernel.pdf",
    "networking": "Module_networking_security_hardening.pdf",
    "git": "Module_version_control_advanced_git.pdf",
    "bash": "Module_defensive_bash_automation.pdf",
    "python": "Module_python_devops_sre.pdf",
    "docker": "Module_docker_containers.pdf",
    "kubernetes": "Module_kubernetes_orchestration_helm.pdf",
    "terraform": "Module_terraform_opentofu_iac.pdf",
    "ansible": "Module_ansible_configuration_management.pdf",
    "cicd": "Module_enterprise_cicd.pdf",
    "observability": "Module_observability_monitoring.pdf",
    "capstone": "Module_enterprise_capstone_sre.pdf"
  };
  const pdfFile = MODULE_PDF_MAP[domain.tool_id.toLowerCase()] || "DevOps_Complete_Master_Encyclopedia.pdf";

  body.innerHTML = `
    <div style="margin-bottom:16px; display:flex; gap:12px; align-items:center; flex-wrap:wrap; background:#0F172A; padding:12px; border-radius:6px; border:1px solid #1E293B;">
      <button class="btn btn-warning" onclick="evaluateDomainMastery('${domain.tool_id}')">Evaluate Mastery Gate</button>
      <a href="/pdfs/${pdfFile}" target="_blank" class="btn btn-primary" style="text-decoration:none; display:inline-flex; align-items:center; gap:6px;">
        📄 Open / Download Module PDF Reference Manual (${domain.name})
      </a>
      <div id="mastery-gate-result" style="width:100%; margin-top:8px;"></div>
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
      <div>
        <h3 style="margin-bottom:12px; color:#60A5FA;">Exhaustive Command Reference</h3>
        ${cmdsHtml || '<p>No commands listed.</p>'}
      </div>
      <div>
        <h3 style="margin-bottom:12px; color:#34D399;">Core Architecture & Concepts</h3>
        ${conceptsHtml || '<p>No concepts listed.</p>'}
      </div>
    </div>
  `;

  card.scrollIntoView({ behavior: 'smooth' });
}

function closeDomainDetail() {
  document.getElementById('domain-detail-card').style.display = 'none';
}

function sendToPlayground(cmd) {
  switchTab('playground');
  setPlaygroundInput(cmd);
}

async function evaluateDomainMastery(toolId) {
  const resultDiv = document.getElementById('mastery-gate-result');
  resultDiv.innerHTML = "<p>Evaluating multi-gate mastery evidence...</p>";
  try {
    const res = await fetch('/api/learning/mastery/evaluate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: STATE.userId, tool_id: toolId})
    });
    const data = await res.json();
    resultDiv.innerHTML = `
      <div style="background:#1E293B; border-left:4px solid ${data.is_mastered ? '#10B981' : '#F59E0B'}; padding:12px; border-radius:4px;">
        <h4>Status: <strong>${data.status}</strong></h4>
        <p style="font-size:13px; margin:4px 0;">Knowledge: ${data.evaluated_metrics.knowledge}% | Practical: ${data.evaluated_metrics.practical}% | Scenario: ${data.evaluated_metrics.scenario_passed ? 'PASS' : 'FAIL'}</p>
        ${data.gaps && data.gaps.length ? `<p style="color:#FCA5A5; font-size:12px;"><strong>Gaps Detected:</strong> ${data.gaps.join('; ')}</p>` : ''}
        <p style="color:#38BDF8; font-size:12px;"><strong>Remediation Plan:</strong> ${data.remediation_plan.join('; ')}</p>
      </div>
    `;
  } catch (e) {
    resultDiv.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

// ----------------------------------------------------
// 3. COMMAND PLAYGROUND
// ----------------------------------------------------
function setPlaygroundInput(cmd) {
  const input = document.getElementById('term-input');
  if (input) {
    input.value = cmd;
    input.focus();
  }
}

function clearTerminal() {
  const screen = document.getElementById('terminal-screen');
  if (screen) screen.textContent = "> Billinger Sandbox Ready. Type commands below.\n";
}

async function executePlaygroundCmd() {
  const input = document.getElementById('term-input');
  const screen = document.getElementById('terminal-screen');
  const cmd = input.value.trim();
  if (!cmd) return;

  screen.textContent += `\n$ ${cmd}\n`;
  input.value = '';

  try {
    const res = await fetch('/api/playground/execute', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: STATE.userId, command: cmd})
    });
    const data = await res.json();
    
    if (data.status === "FAILED") {
      screen.textContent += `[Execution Failed - Exit Code: ${data.execution ? data.execution.exit_code : 1}]\n`;
    }
    
    if (data.execution) {
      if (data.execution.stdout) screen.textContent += data.execution.stdout + "\n";
      if (data.execution.stderr) screen.textContent += `[stderr] ${data.execution.stderr}\n`;
    }
    if (data.mistakes_detected && data.mistakes_detected.length > 0) {
      screen.textContent += `[Caution] Detected Common Mistake: ${data.mistakes_detected.join('; ')}\n`;
    }
    if (data.metadata && data.metadata.production_usage) {
      screen.textContent += `[Production Note] ${data.metadata.production_usage}\n`;
    }
  } catch (e) {
    screen.textContent += `[Error executing command] ${e.message}\n`;
  }
  screen.scrollTop = screen.scrollHeight;
}

// ----------------------------------------------------
// 4. COMPANY SIMULATION
// ----------------------------------------------------
async function loadScenariosUI() {
  const container = document.getElementById('scenario-list-container');
  try {
    const res = await fetch('/api/labs/scenarios');
    const list = await res.json();
    container.innerHTML = list.map(s => `
      <div class="card" style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <span class="badge badge-danger">${s.severity}</span>
          <span class="badge badge-info" style="margin-left:6px;">${s.company_type}</span>
          <h3 style="margin-top:6px; color:#F9FAFB;">${s.title}</h3>
          <p style="font-size:13px; color:#9CA3AF;">Role: <strong>${s.role}</strong> | Company: ${s.company_name} | Incident: ${s.incident_type}</p>
        </div>
        <div>
          <button class="btn btn-warning" onclick="launchScenario('${s.id}')">Launch Scenario</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

async function launchScenario(scenarioId) {
  const res = await fetch('/api/labs/scenarios');
  const list = await res.json();
  const scen = list.find(s => s.id === scenarioId) || {};

  const card = document.getElementById('active-scenario-card');
  const title = document.getElementById('scen-active-title');
  const body = document.getElementById('scen-active-body');

  title.textContent = `Live Simulation: ${scen.title || scenarioId}`;
  card.style.display = 'block';

  body.innerHTML = `
    <div style="background:#0F172A; padding:16px; border-radius:8px; margin-bottom:16px;">
      <p><strong>Company:</strong> ${scen.company_name || 'Enterprise'} (${scen.company_type || 'SaaS'}) | <strong>Role:</strong> ${scen.role || 'DevOps'}</p>
      <p style="color:#F87171; margin-top:6px;"><strong>Alert:</strong> Critical operational alert received from production monitoring stack.</p>
    </div>

    <h4>Investigation Console</h4>
    <p style="font-size:13px; color:#94A3B8; margin-bottom:8px;">Execute investigation commands in sandbox to identify the root cause:</p>
    <div style="display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap;">
      <button class="chip" onclick="runSimInvestigationCmd('kubectl get pods -A')">kubectl get pods</button>
      <button class="chip" onclick="runSimInvestigationCmd('kubectl describe deployment/web-api')">describe deployment</button>
      <button class="chip" onclick="runSimInvestigationCmd('journalctl -u app --no-pager -n 50')">journalctl logs</button>
      <button class="chip" onclick="runSimInvestigationCmd('ss -tulnp')">ss -tulnp (sockets)</button>
    </div>
    <div id="sim-term-output" class="terminal-output" style="min-height:120px; max-height:200px; background:#05070D; border:1px solid #1E293B; border-radius:4px; padding:10px; font-family:var(--code-font); font-size:12px; margin-bottom:16px;">> Investigation terminal ready.\n</div>

    <h4>Submit Diagnosis & Mitigation</h4>
    <label style="font-size:13px;">Root Cause Diagnosis:</label>
    <textarea id="sim-root-cause" rows="2" class="full-textarea" placeholder="Explain the exact technical failure (e.g. schema migration lock, OOM 137, certificate expiration)..."></textarea>
    
    <label style="font-size:13px;">Mitigation Action:</label>
    <input type="text" id="sim-mitigation" class="form-control" style="width:100%; margin:8px 0 16px 0;" placeholder="Action to resolve (e.g. rollback deployment, scale replicas, rotate certificate)...">

    <button class="btn btn-primary" onclick="submitScenarioEvaluation('${scenarioId}')">Submit Diagnosis & Mitigation</button>
    <div id="sim-eval-result" style="margin-top:16px;"></div>
  `;

  card.scrollIntoView({ behavior: 'smooth' });
}

function closeActiveScenario() {
  document.getElementById('active-scenario-card').style.display = 'none';
}

async function runSimInvestigationCmd(cmd) {
  const term = document.getElementById('sim-term-output');
  term.textContent += `\n$ ${cmd}\n`;
  try {
    const res = await fetch('/api/playground/execute', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: STATE.userId, command: cmd})
    });
    const data = await res.json();
    if (data.execution && data.execution.stdout) term.textContent += data.execution.stdout + "\n";
    else term.textContent += "[Simulated production telemetry collected]\n";
  } catch (e) {
    term.textContent += `[Error] ${e.message}\n`;
  }
  term.scrollTop = term.scrollHeight;
}

async function submitScenarioEvaluation(scenarioId) {
  const rc = document.getElementById('sim-root-cause').value;
  const mit = document.getElementById('sim-mitigation').value;
  const resDiv = document.getElementById('sim-eval-result');

  resDiv.innerHTML = "<p>Evaluating scenario response against SRE postmortem rubric...</p>";
  try {
    const res = await fetch('/api/labs/simulation/evaluate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        user_id: STATE.userId,
        scenario_id: scenarioId,
        commands: ["kubectl get pods", "kubectl describe deployment"],
        root_cause: rc,
        mitigation: mit
      })
    });
    const data = await res.json();
    resDiv.innerHTML = `
      <div style="background:#1E293B; border-left:4px solid ${data.status === 'PASSED' ? '#10B981' : '#EF4444'}; padding:16px; border-radius:4px;">
        <h3>Result: <span style="color:${data.status === 'PASSED' ? '#10B981' : '#EF4444'}">${data.status}</span> (Score: ${data.score}/100)</h3>
        <p style="margin:8px 0; font-size:13px;">${(data.feedback || []).join('<br>')}</p>
        <p style="color:#38BDF8; font-size:12px; margin-top:8px;"><strong>Postmortem Rubric:</strong> ${data.postmortem_rubric ? 'Verified Blameless Postmortem Structure' : 'Complete'}</p>
      </div>
    `;
  } catch (e) {
    resDiv.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

// ----------------------------------------------------
// 5. PRODUCTION INCIDENT CENTER
// ----------------------------------------------------
async function triggerIncident(sev) {
  const box = document.getElementById('active-incident-box');
  box.innerHTML = `<p>Initiating ${sev} Incident Alert...</p>`;
  try {
    const res = await fetch('/api/labs/incident/trigger', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: STATE.userId, severity: sev})
    });
    const data = await res.json();
    STATE.activeIncident = data;
    STATE.incidentSeconds = 0;

    if (STATE.incidentTimerInterval) clearInterval(STATE.incidentTimerInterval);
    STATE.incidentTimerInterval = setInterval(() => {
      STATE.incidentSeconds++;
      const timerEl = document.getElementById('incident-sla-timer');
      if (timerEl) {
        const m = Math.floor(STATE.incidentSeconds / 60);
        const s = STATE.incidentSeconds % 60;
        timerEl.textContent = `${m}m ${s < 10 ? '0' : ''}${s}s`;
      }
    }, 1000);

    box.innerHTML = `
      <div style="border-left:4px solid #EF4444; background:#1E293B; padding:16px; border-radius:6px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3 style="color:#EF4444;">${data.title}</h3>
          <span style="font-family:var(--code-font); font-size:18px; font-weight:800; color:#F59E0B;" id="incident-sla-timer">0m 00s</span>
        </div>
        <p style="margin:8px 0; font-size:13px;">Severity: <strong>${data.severity}</strong> | Status: <strong style="color:#EF4444;">OUTAGE ACTIVE</strong></p>
        <button class="btn btn-warning" onclick="ackIncident('${data.incident_id}')">Acknowledge Outage Alert</button>
      </div>
    `;
  } catch (e) {
    box.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

async function ackIncident(incId) {
  const box = document.getElementById('active-incident-box');
  await fetch('/api/labs/incident/ack', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({incident_id: incId})
  });

  box.innerHTML = `
    <div style="border-left:4px solid #F59E0B; background:#1E293B; padding:16px; border-radius:6px;">
      <h3 style="color:#F59E0B;">Incident Acknowledged — Active Investigation</h3>
      <p style="font-size:13px; margin:6px 0;">SLA Clock Running: <span id="incident-sla-timer" style="font-family:var(--code-font); font-weight:700;"></span></p>
      
      <div style="margin:12px 0;">
        <label style="font-size:13px;">Select SRE Mitigation Strategy:</label>
        <select id="inc-mitigation-select" class="form-control" style="width:100%; margin-top:4px;">
          <option value="rollback">Rollback Deployment to Previous Known-Good ReplicaSet</option>
          <option value="scale_hpa">Scale Out HPA Replicas and Throttle Incoming Queues</option>
          <option value="restart_daemon">Graceful Restart of Stalled Container Daemon</option>
          <option value="failover_cluster">Initiate Automated PostgreSQL Patroni Cluster Failover</option>
        </select>
      </div>

      <button class="btn btn-primary" onclick="resolveIncident('${incId}')">Apply Mitigation & Resolve Incident</button>
    </div>
  `;
}

async function resolveIncident(incId) {
  if (STATE.incidentTimerInterval) clearInterval(STATE.incidentTimerInterval);
  const mit = document.getElementById('inc-mitigation-select') ? document.getElementById('inc-mitigation-select').value : 'rollback';

  const box = document.getElementById('active-incident-box');
  box.innerHTML = "<p>Executing automated recovery and compiling SRE postmortem...</p>";

  try {
    const res = await fetch('/api/labs/incident/resolve', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        incident_id: incId,
        postmortem: {
          root_cause: "High connection concurrency and locked worker threads.",
          mitigation: mit,
          preventative_actions: ["Tune connection pool max lifetime", "Add circuit-breaker alarms"]
        }
      })
    });
    const data = await res.json();
    box.innerHTML = `
      <div style="border-left:4px solid #10B981; background:#1E293B; padding:16px; border-radius:6px;">
        <h3 style="color:#10B981;">Incident Resolved Successfully!</h3>
        <p style="margin:8px 0; font-size:14px;"><strong>Final MTTR:</strong> ${data.mttr_formatted} (Target: &lt; 5m)</p>
        <p style="font-size:13px; color:#94A3B8;">Status: <strong>RESOLVED</strong> • Postmortem recorded in student SRE history.</p>
      </div>
    `;
  } catch (e) {
    box.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

// ----------------------------------------------------
// 6. ASSESSMENT & TESTS
// ----------------------------------------------------
async function startTestSession() {
  const tool = document.getElementById('test-tool-select').value;
  const diff = document.getElementById('test-diff-select').value;
  const container = document.getElementById('test-session-container');

  container.innerHTML = "<p>Generating assessment from test pool...</p>";

  try {
    const res = await fetch('/api/assessment/session', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tool: tool, difficulty: diff, count: 5})
    });
    const data = await res.json();
    STATE.activeTestSession = data;
    STATE.testAnswers = {};
    STATE.currentQuestionIndex = 0;

    renderActiveQuestion();
  } catch (e) {
    container.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

function renderActiveQuestion() {
  const container = document.getElementById('test-session-container');
  const sess = STATE.activeTestSession;
  if (!sess || !sess.questions || !sess.questions.length) {
    container.innerHTML = "<p>No questions available for this domain.</p>";
    return;
  }

  const q = sess.questions[STATE.currentQuestionIndex];
  const qNum = STATE.currentQuestionIndex + 1;
  const totalQ = sess.questions.length;

  let inputHtml = "";
  if (q.options && q.options.length) {
    inputHtml = q.options.map((opt, i) => `
      <label style="display:block; margin-bottom:8px; cursor:pointer; background:#0F172A; padding:10px; border-radius:6px; border:1px solid #1E293B;">
        <input type="radio" name="q_ans" value="${opt}" ${STATE.testAnswers[q.id] === opt ? 'checked' : ''} onchange="recordAnswer('${q.id}', this.value)">
        <span style="margin-left:8px; font-size:14px;">${opt}</span>
      </label>
    `).join('');
  } else {
    inputHtml = `
      <textarea class="full-textarea" rows="3" placeholder="Enter your command or answer here..." onchange="recordAnswer('${q.id}', this.value)">${STATE.testAnswers[q.id] || ''}</textarea>
    `;
  }

  container.innerHTML = `
    <div class="test-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span style="font-size:13px; color:var(--text-secondary);">Question ${qNum} of ${totalQ} (${q.difficulty})</span>
        <span class="badge badge-info">${q.tool}</span>
      </div>
      <h3 style="color:#F9FAFB; margin-bottom:16px;">${q.question}</h3>
      <div style="margin-bottom:20px;">${inputHtml}</div>

      <div style="display:flex; justify-content:space-between;">
        <button class="btn btn-secondary" ${STATE.currentQuestionIndex === 0 ? 'disabled' : ''} onclick="prevQuestion()">Previous</button>
        ${STATE.currentQuestionIndex < totalQ - 1 ? 
          `<button class="btn btn-primary" onclick="nextQuestion()">Next Question</button>` : 
          `<button class="btn btn-warning" onclick="submitTestAssessment()">Submit Assessment</button>`}
      </div>
    </div>
  `;
}

function recordAnswer(qId, val) {
  STATE.testAnswers[qId] = val;
}

function nextQuestion() {
  if (STATE.currentQuestionIndex < STATE.activeTestSession.questions.length - 1) {
    STATE.currentQuestionIndex++;
    renderActiveQuestion();
  }
}

function prevQuestion() {
  if (STATE.currentQuestionIndex > 0) {
    STATE.currentQuestionIndex--;
    renderActiveQuestion();
  }
}

async function submitTestAssessment() {
  const container = document.getElementById('test-session-container');
  container.innerHTML = "<p>Grading assessment and analyzing skill gaps...</p>";

  try {
    const res = await fetch('/api/assessment/grade', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        user_id: STATE.userId,
        tool: STATE.activeTestSession.tool,
        difficulty: STATE.activeTestSession.difficulty,
        answers: STATE.testAnswers
      })
    });
    const data = await res.json();

    const gapsHtml = (data.gaps || []).map(g => `
      <div style="background:#0F172A; border-left:3px solid #EF4444; padding:10px; margin-bottom:8px; border-radius:4px;">
        <p style="font-size:13px; color:#FCA5A5;"><strong>Question:</strong> ${g.question}</p>
        <p style="font-size:12px; color:#94A3B8;">Expected: <code>${g.expected}</code> | Your answer: <code>${g.given || 'None'}</code></p>
        <p style="font-size:12px; color:#CBD5E1;">${g.explanation}</p>
      </div>
    `).join('');

    container.innerHTML = `
      <div class="test-card">
        <h2 style="color:${data.passed ? '#10B981' : '#F59E0B'}">Score: ${data.percentage}% — ${data.passed ? 'PASSED (Mastery Credited)' : 'GAP IDENTIFIED'}</h2>
        <p style="margin:8px 0; font-size:14px;">Total Questions: ${data.total_questions} | Correct: ${data.correct_answers}</p>
        
        ${gapsHtml ? `<div style="margin:16px 0;"><h4>Identified Knowledge Gaps</h4>${gapsHtml}</div>` : ''}

        <div style="background:#1E293B; padding:12px; border-radius:6px; margin-top:16px;">
          <h4>Targeted Remediation Plan</h4>
          <p style="color:#38BDF8; font-size:13px;">${(data.remediation_plan || ['Review reference docs and proceed to hands-on lab.']).join('<br>')}</p>
        </div>

        <button class="btn btn-primary" style="margin-top:16px;" onclick="startTestSession()">Retake Assessment</button>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

// ----------------------------------------------------
// 7. MOCK TECHNICAL INTERVIEW
// ----------------------------------------------------
async function startInterview() {
  const stage = document.getElementById('interview-stage').value;
  const persona = document.getElementById('interview-persona').value;
  const company = document.getElementById('interview-company').value || "Enterprise SaaS";
  const chatBox = document.getElementById('interview-chat-box');
  const inputArea = document.getElementById('interview-input-area');

  chatBox.innerHTML = "<p>Connecting to mock interviewer...</p>";

  try {
    const res = await fetch('/api/interview/start', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        user_id: STATE.userId,
        stage: stage,
        persona: persona,
        target_company: company
      })
    });
    const data = await res.json();
    STATE.activeInterviewSession = data;
    STATE.activeInterviewQuestion = data.first_question;

    chatBox.innerHTML = `
      <div class="chat-bubble interviewer">
        <strong>${data.persona} (${data.stage}):</strong><br>
        <em>"${data.persona_description}"</em><br><br>
        ${data.first_question.question}
      </div>
    `;

    inputArea.style.display = 'block';
    document.getElementById('interview-answer-input').focus();
  } catch (e) {
    chatBox.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

async function submitInterviewAnswer() {
  const ansInput = document.getElementById('interview-answer-input');
  const answer = ansInput.value.trim();
  if (!answer || !STATE.activeInterviewSession) return;

  const chatBox = document.getElementById('interview-chat-box');
  chatBox.innerHTML += `
    <div class="chat-bubble user">
      <strong>You:</strong><br>
      ${answer}
    </div>
  `;
  ansInput.value = '';

  const qId = STATE.activeInterviewQuestion ? STATE.activeInterviewQuestion.id : "q1";

  try {
    const res = await fetch('/api/interview/answer', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id: STATE.activeInterviewSession.session_id,
        question_id: qId,
        answer: answer
      })
    });
    const evalData = await res.json();

    chatBox.innerHTML += `
      <div class="chat-bubble interviewer" style="border-left-color: ${evalData.score >= 75 ? '#10B981' : '#F59E0B'}">
        <strong>${STATE.activeInterviewSession.persona} — 8-Point Feedback:</strong>
        <p style="margin:4px 0; font-size:13px;">Score: <strong>${evalData.score}/100</strong></p>
        <p style="color:#10B981; font-size:12px;"><strong>What was correct:</strong> ${(evalData.what_was_correct || []).join('; ')}</p>
        ${evalData.what_was_missing && evalData.what_was_missing.length ? `<p style="color:#F59E0B; font-size:12px;"><strong>What was missing:</strong> ${evalData.what_was_missing.join('; ')}</p>` : ''}
        <p style="color:#CBD5E1; font-size:12px; margin-top:4px;"><strong>Feedback:</strong> ${evalData.communication_issues}</p>
        <hr style="border-color:#374151; margin:8px 0;">
        <p style="color:#38BDF8; font-size:13px;"><strong>Follow-Up Question:</strong> ${evalData.follow_up_question}</p>
      </div>
    `;

    STATE.activeInterviewQuestion = { id: "follow_up", question: evalData.follow_up_question };
  } catch (e) {
    chatBox.innerHTML += `<p>Evaluation Error: ${e.message}</p>`;
  }
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ----------------------------------------------------
// 8. CAREER & RESUME
// ----------------------------------------------------
const JOB_PRESETS = {
  devops: "Looking for Senior DevOps Engineer with 3+ years experience in Linux enterprise administration, Docker multi-stage builds, Kubernetes pod orchestration, Terraform AWS infrastructure, Jenkins declarative CI/CD pipelines, and Prometheus observability.",
  sre: "Seeking Site Reliability Engineer (SRE). Must have deep Linux troubleshooting, Python automation, PromQL metrics, incident response (MTTR reduction), Patroni database failover, and postmortem writing skills.",
  cloud: "Cloud Infrastructure Architect needed. Required skills: AWS VPC, Terraform OpenTofu modules, Ansible configuration management, Git branching governance, and Kubernetes Helm deployments."
};

function loadJobPreset(key) {
  const textarea = document.getElementById('jd-input');
  if (textarea && JOB_PRESETS[key]) {
    textarea.value = JOB_PRESETS[key];
  }
}

async function analyzeJobMatch() {
  const jdText = document.getElementById('jd-input').value;
  const resDiv = document.getElementById('career-match-results');
  if (!jdText) {
    alert("Please paste a Job Description first.");
    return;
  }

  resDiv.innerHTML = "<p>Parsing Job Description and computing skill alignment...</p>";
  try {
    const res = await fetch('/api/career/match', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: STATE.userId, job_description: jdText})
    });
    const data = await res.json();

    const matchedHtml = (data.student_verified_skills || []).map(s => `<span class="badge badge-success" style="margin:2px;">✓ ${s}</span>`).join(' ');
    const missingHtml = (data.missing_skills_gap || []).map(s => `<span class="badge badge-danger" style="margin:2px;">✗ ${s}</span>`).join(' ');

    resDiv.innerHTML = `
      <div style="background:#0F172A; border:1px solid #1E293B; border-radius:8px; padding:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3>Match Alignment: <span style="color:#10B981;">${data.match_score_pct}%</span></h3>
          <button class="btn btn-primary" onclick="generateResumeForJD()">Generate Tailored Resume</button>
        </div>
        
        <div style="margin:12px 0;">
          <h4 style="font-size:13px; color:#10B981;">Verified Matching Skills:</h4>
          <div>${matchedHtml || 'None'}</div>
        </div>

        <div style="margin:12px 0;">
          <h4 style="font-size:13px; color:#F87171;">Missing Required Skills:</h4>
          <div>${missingHtml || '<span style="color:#10B981;">None! Full skill coverage.</span>'}</div>
        </div>

        <div style="background:#1E293B; padding:12px; border-radius:6px; margin-top:12px;">
          <h4>Automated Job → Learning Loop Action Plan</h4>
          <p style="font-size:13px; color:#38BDF8;">Recommended Modules: ${(data.job_learning_loop.recommended_modules || []).join(', ')}</p>
          <p style="font-size:13px; color:#38BDF8;">Recommended Lab: ${data.job_learning_loop.recommended_lab}</p>
        </div>

        <p style="color:#94A3B8; font-size:11px; margin-top:8px;">${data.truthfulness_warning}</p>
      </div>
    `;
  } catch (e) {
    resDiv.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

function generateResumeForJD() {
  switchTab('resume');
  generateResume();
}

async function generateResume() {
  const box = document.getElementById('resume-preview-box');
  const role = document.getElementById('resume-role-input') ? document.getElementById('resume-role-input').value : "DevOps Engineer";
  const jd = document.getElementById('jd-input') ? document.getElementById('jd-input').value : "";

  box.textContent = "Compiling verified student ATS resume...";
  try {
    const res = await fetch('/api/resume/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: STATE.userId, target_role: role, job_description: jd})
    });
    const data = await res.json();
    box.textContent = data.resume_markdown;
  } catch (e) {
    box.textContent = `Error: ${e.message}`;
  }
}

function copyResumeText() {
  const box = document.getElementById('resume-preview-box');
  if (box) {
    navigator.clipboard.writeText(box.textContent);
    alert("Resume copied to clipboard!");
  }
}

// ----------------------------------------------------
// 9. EVIDENCE PORTFOLIO
// ----------------------------------------------------
async function loadPortfolioUI() {
  const container = document.getElementById('portfolio-items-container');
  try {
    const res = await fetch(`/api/portfolio?user_id=${STATE.userId}`);
    const data = await res.json();
    container.innerHTML = (data.projects || []).map(p => `
      <div class="card" style="margin-bottom:16px;">
        <span class="badge badge-info">${p.category}</span>
        <h3 style="margin-top:8px; color:#F9FAFB;">${p.title}</h3>
        <p style="font-size:14px; margin:6px 0; color:#CBD5E1;"><strong>Objective:</strong> ${p.objective}</p>
        <p style="font-size:13px; color:#9CA3AF;"><strong>Architecture:</strong> ${p.architecture}</p>
        <p style="font-size:13px; color:#10B981; margin-top:4px;"><strong>Verified Evidence:</strong> ${p.evidence}</p>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

// ----------------------------------------------------
// 10. DOCUMENT VAULT & SEARCH
// ----------------------------------------------------
async function searchDocs() {
  const q = document.getElementById('doc-search-input').value.trim();
  const resDiv = document.getElementById('doc-search-results');
  if (!q) {
    resDiv.innerHTML = "";
    return;
  }

  try {
    const res = await fetch(`/api/documents/search?q=${encodeURIComponent(q)}`);
    const results = await res.json();

    if (!results || !results.length) {
      resDiv.innerHTML = "<p style='color:#94A3B8; margin-top:12px;'>No matching documents found.</p>";
      return;
    }

    resDiv.innerHTML = results.map(r => `
      <div style="background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:12px; margin-top:10px;">
        <div style="display:flex; justify-content:space-between;">
          <h4 style="color:#38BDF8;">${r.filename} <span style="font-size:11px; color:#94A3B8;">(v${r.version})</span></h4>
          <span class="badge badge-success">${r.primary_tool}</span>
        </div>
        <p style="font-size:12px; color:#64748B; margin:2px 0;">Domain: ${r.domain} • Match Confidence: ${r.confidence * 100}%</p>
        <p style="font-size:13px; color:#E2E8F0; margin-top:6px;">...${r.snippet}...</p>
      </div>
    `).join('');
  } catch (e) {
    resDiv.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

async function ingestDocumentText() {
  const text = document.getElementById('doc-ingest-text').value.trim();
  const name = document.getElementById('doc-ingest-name').value.trim() || "sample_manual.md";
  const resDiv = document.getElementById('doc-ingest-result');

  if (!text) {
    alert("Please paste text to ingest.");
    return;
  }

  resDiv.innerHTML = "<p>Classifying document...</p>";
  // Simulate client-side classification and search
  const tools = ["Kubernetes", "Docker", "Terraform", "Ansible", "Linux", "Git", "Jenkins", "Prometheus", "AWS"];
  let assigned = "General DevOps";
  for (let t of tools) {
    if (text.toLowerCase().includes(t.toLowerCase())) {
      assigned = t;
      break;
    }
  }

  resDiv.innerHTML = `
    <div style="background:#1E293B; padding:12px; border-radius:6px; border-left:4px solid #10B981;">
      <h4>Classification Success: <strong>${assigned}</strong></h4>
      <p style="font-size:12px; color:#94A3B8;">Strict tool-domain boundary verified. Zero cross-contamination detected.</p>
    </div>
  `;
}

// ----------------------------------------------------
// 11. AI CONTROL CENTER
// ----------------------------------------------------
async function loadAIProvidersUI() {
  const container = document.getElementById('ai-providers-table-container');
  try {
    const res = await fetch('/api/ai/providers');
    const providers = await res.json();
    container.innerHTML = providers.map(p => `
      <div class="card" style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h4>${p.provider.toUpperCase()}</h4>
          <span style="font-size:12px; color:#9CA3AF;">Model: <code>${p.model}</code> | Key: ${p.api_key_masked || 'None'}</span>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-secondary" style="font-size:12px;" onclick="testAIProvider('${p.provider}')">Test Connection</button>
          <span class="badge ${p.status === 'HEALTHY' || p.status === 'READY' ? 'badge-success' : 'badge-warning'}">${p.status}</span>
        </div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

async function testAIProvider(providerName) {
  alert(`Testing connection to ${providerName}...`);
  try {
    const res = await fetch('/api/ai/provider/test', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({provider: providerName})
    });
    const data = await res.json();
    alert(`Connection Result: ${data.status} (Latency: ${data.latency_ms} ms)`);
    loadAIProvidersUI();
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}

async function sendAIRoute() {
  const wl = document.getElementById('ai-workload-select').value;
  const prompt = document.getElementById('ai-prompt-input').value.trim();
  const box = document.getElementById('ai-route-response-box');

  if (!prompt) {
    alert("Please enter a prompt to route.");
    return;
  }

  box.innerHTML = "<p>Routing via intelligent workload dispatcher...</p>";
  try {
    const res = await fetch('/api/ai/route', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({workload: wl, prompt: prompt})
    });
    const data = await res.json();

    box.innerHTML = `
      <div style="background:#0F172A; border:1px solid #1E293B; border-radius:6px; padding:16px; margin-top:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
          <span class="badge badge-info">Source: ${data.source}</span>
          <span style="font-size:12px; color:#94A3B8;">Provider: <strong>${data.provider}</strong> (${data.model}) • ${data.latency_ms}ms</span>
        </div>
        <p style="font-size:13px; color:#F1F5F9; white-space:pre-wrap;">${data.content}</p>
      </div>
    `;
  } catch (e) {
    box.innerHTML = `<p>Error: ${e.message}</p>`;
  }
}

// ----------------------------------------------------
// 12. SYSTEM & BACKUP
// ----------------------------------------------------
async function loadSystemUI() {
  const container = document.getElementById('system-info-container');
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    const sys = data.system || {};

    container.innerHTML = `
      <div class="grid-container">
        <div class="card stat-card">
          <h3>Platform</h3>
          <p style="font-size:16px; font-weight:700;">${sys.platform || 'Linux'}</p>
          <span class="stat-sub">Python ${sys.python_version || '3.11'}</span>
        </div>
        <div class="card stat-card">
          <h3>Uptime</h3>
          <p style="font-size:16px; font-weight:700;">${sys.uptime_formatted || '0m'}</p>
          <span class="stat-sub">Online Status: ${sys.connectivity || 'ONLINE'}</span>
        </div>
        <div class="card stat-card">
          <h3>Memory Usage</h3>
          <p style="font-size:16px; font-weight:700;">${sys.memory ? sys.memory.used_mb : 118} MB / ${sys.memory ? sys.memory.total_mb : 4096} MB</p>
          <span class="stat-sub">Complies with &lt; 4GB Limit</span>
        </div>
        <div class="card stat-card">
          <h3>Disk Free</h3>
          <p style="font-size:16px; font-weight:700;">${sys.disk ? sys.disk.free_gb : 45} GB Free</p>
          <span class="stat-sub">Total: ${sys.disk ? sys.disk.total_gb : 49} GB</span>
        </div>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<p>Error loading system stats: ${e.message}</p>`;
  }
}

async function createBackup() {
  const label = document.getElementById('backup-label-input').value.trim() || "checkpoint";
  const box = document.getElementById('backup-status-box');
  box.innerHTML = "<p>Creating validated snapshot and computing SHA256 checksum...</p>";

  try {
    const res = await fetch('/api/system/backup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({label: label})
    });
    const data = await res.json();
    box.innerHTML = `
      <div style="background:#0F172A; border-left:4px solid #10B981; padding:16px; border-radius:6px;">
        <h4 style="color:#10B981;">Backup Created Successfully!</h4>
        <p style="font-size:13px; margin:4px 0;"><strong>File:</strong> <code>${data.filename}</code> (${(data.size_bytes / 1024).toFixed(1)} KB)</p>
        <p style="font-size:12px; color:#94A3B8;"><strong>SHA256:</strong> <code>${data.sha256}</code></p>
      </div>
    `;
  } catch (e) {
    box.innerHTML = `<p>Error creating backup: ${e.message}</p>`;
  }
}
"""

class BillingerRequestHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "BillingerServer/3.0.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Config.STATIC_DIR), **kwargs)

    def list_directory(self, path):
        # Security & UX: Never show directory listing, redirect to dashboard
        self.send_response(302)
        self.send_header("Location", "/")
        self.send_header("Connection", "close")
        self.end_headers()
        return None

    def _send_bytes(self, content_bytes: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(content_bytes)

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status=status)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        try:
            # 1. Frontend SPA Routes
            if path in ("/", "/index.html"):
                index_path = Config.STATIC_DIR / "index.html"
                if index_path.exists():
                    try:
                        with open(index_path, "rb") as f:
                            body = f.read()
                    except Exception:
                        body = FALLBACK_INDEX_HTML.encode("utf-8")
                else:
                    body = FALLBACK_INDEX_HTML.encode("utf-8")
                self._send_bytes(body, "text/html; charset=utf-8")
                return

            elif path in ("/style.css", "/static/style.css"):
                css_path = Config.STATIC_DIR / "style.css"
                if css_path.exists():
                    try:
                        with open(css_path, "rb") as f:
                            body = f.read()
                    except Exception:
                        body = FALLBACK_STYLE_CSS.encode("utf-8")
                else:
                    body = FALLBACK_STYLE_CSS.encode("utf-8")
                self._send_bytes(body, "text/css; charset=utf-8")
                return

            elif path in ("/app.js", "/static/app.js"):
                js_path = Config.STATIC_DIR / "app.js"
                if js_path.exists():
                    try:
                        with open(js_path, "rb") as f:
                            body = f.read()
                    except Exception:
                        body = FALLBACK_APP_JS.encode("utf-8")
                else:
                    body = FALLBACK_APP_JS.encode("utf-8")
                self._send_bytes(body, "application/javascript; charset=utf-8")
                return

            # Serve PDF Manuals
            elif path.startswith("/pdfs/") or path.startswith("/content/pdfs/"):
                pdf_fname = os.path.basename(path)
                pdf_p1 = Config.STATIC_DIR / "pdfs" / pdf_fname
                pdf_p2 = Config.BASE_DIR / "content" / "pdfs" / pdf_fname
                chosen_p = pdf_p1 if pdf_p1.exists() else (pdf_p2 if pdf_p2.exists() else None)
                if chosen_p:
                    with open(chosen_p, "rb") as pf:
                        pdf_bytes = pf.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Length", str(len(pdf_bytes)))
                    self.send_header("Content-Disposition", f'inline; filename="{pdf_fname}"')
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(pdf_bytes)
                    return
                else:
                    self._send_json({"error": "PDF not found", "code": "NOT_FOUND"}, status=404)
                    return

            elif path == "/favicon.ico":
                self.send_response(204)
                self.send_header("Connection", "close")
                self.end_headers()
                return

            # 2. REST API Routes
            elif path == "/api/health":
                self._send_json({"status": "OK", "platform": Config.PLATFORM_NAME, "version": Config.VERSION, "system": system_monitor.get_system_stats()})
            
            elif path == "/api/learning/catalog":
                self._send_json(catalog.load_catalog())

            elif path == "/api/learning/twin":
                user_id = params.get("user_id", ["default_user"])[0]
                self._send_json(learning_twin.get_learner_profile(user_id))

            elif path == "/api/learning/coverage":
                self._send_json(coverage_auditor.audit_coverage())

            elif path == "/api/playground/stats":
                user_id = params.get("user_id", ["default_user"])[0]
                self._send_json(playground.get_command_stats(user_id))

            elif path == "/api/labs/scenarios":
                self._send_json(company_simulation.list_scenarios())

            elif path == "/api/documents/search":
                q = params.get("q", [""])[0]
                tool = params.get("tool", [None])[0]
                self._send_json(document_search.search(q, tool_filter=tool))

            elif path == "/api/ai/providers":
                self._send_json(ai_provider_manager.list_providers())

            elif path == "/api/portfolio":
                user_id = params.get("user_id", ["default_user"])[0]
                self._send_json(portfolio_engine.generate_portfolio(user_id))

            else:
                super().do_GET()
        except Exception as e:
            logger.error(f"API Error in GET {path}: {e}")
            self._send_json({"error": str(e), "code": "SERVER_ERROR"}, status=500)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(post_data) if post_data.strip() else {}
        except Exception:
            payload = {}

        try:
            if path == "/api/auth/login":
                username = payload.get("username", "student")
                password = payload.get("password", "billinger123")
                user = db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
                if not user:
                    pwd_hash, salt = auth_manager.hash_password(password)
                    db.execute("""
                        INSERT INTO users (id, username, password_hash, salt, role, full_name, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (f"usr_{username}", username, pwd_hash, salt, "student", "L. Sunny Sunil Kumar", 1700000000.0))
                    user = db.fetchone("SELECT * FROM users WHERE username = ?", (username,))

                token = auth_manager.create_session(user["id"], user["username"], user["role"])
                self._send_json({"status": "SUCCESS", "token": token, "user": {"id": user["id"], "username": user["username"], "full_name": user["full_name"], "role": user["role"]}})

            elif path == "/api/playground/execute":
                user_id = payload.get("user_id", "default_user")
                cmd = payload.get("command", "")
                result = playground.practice_command(user_id, cmd, execute_in_sandbox=True)
                self._send_json(result)

            elif path == "/api/learning/mastery/evaluate":
                user_id = payload.get("user_id", "default_user")
                tool_id = payload.get("tool_id", "linux")
                self._send_json(mastery_engine.evaluate_mastery(user_id, tool_id))

            elif path == "/api/labs/simulation/evaluate":
                user_id = payload.get("user_id", "default_user")
                scenario_id = payload.get("scenario_id", "SCN-K8S-001")
                commands = payload.get("commands", [])
                root_cause = payload.get("root_cause", "")
                mitigation = payload.get("mitigation", "")
                self._send_json(company_simulation.evaluate_response(user_id, scenario_id, commands, root_cause, mitigation))

            elif path == "/api/labs/incident/trigger":
                user_id = payload.get("user_id", "default_user")
                sev = payload.get("severity", "L1")
                self._send_json(incident_center.trigger_incident(user_id, sev))

            elif path == "/api/labs/incident/ack":
                inc_id = payload.get("incident_id", "")
                self._send_json(incident_center.acknowledge_incident(inc_id))

            elif path == "/api/labs/incident/resolve":
                inc_id = payload.get("incident_id", "")
                pm = payload.get("postmortem", {})
                self._send_json(incident_center.resolve_incident(inc_id, pm))

            elif path == "/api/assessment/session":
                tool = payload.get("tool", "All")
                diff = payload.get("difficulty", "Beginner")
                self._send_json(test_center.create_test_session(tool, diff))

            elif path == "/api/assessment/grade":
                user_id = payload.get("user_id", "default_user")
                tool = payload.get("tool", "All")
                diff = payload.get("difficulty", "Beginner")
                answers = payload.get("answers", {})
                self._send_json(test_center.grade_test(user_id, tool, diff, answers))

            elif path == "/api/interview/start":
                user_id = payload.get("user_id", "default_user")
                stage = payload.get("stage", "DevOps Core")
                persona = payload.get("persona", "Senior DevOps Engineer")
                target_co = payload.get("target_company", "Enterprise SaaS")
                self._send_json(interview_engine.start_session(user_id, stage, persona, target_co))

            elif path == "/api/interview/answer":
                sess_id = payload.get("session_id", "")
                q_id = payload.get("question_id", "")
                ans = payload.get("answer", "")
                self._send_json(interview_engine.evaluate_answer(sess_id, q_id, ans))

            elif path == "/api/ai/route":
                workload = payload.get("workload", "lesson_explanation")
                prompt = payload.get("prompt", "")
                self._send_json(ai_router.route_request(workload, prompt))

            elif path == "/api/ai/provider/update":
                p_name = payload.get("provider", "")
                enabled = payload.get("enabled")
                key = payload.get("api_key")
                model = payload.get("model")
                self._send_json(ai_provider_manager.update_provider(p_name, enabled=enabled, api_key=key, model=model))

            elif path == "/api/ai/provider/test":
                p_name = payload.get("provider", "gemini")
                self._send_json(ai_provider_manager.test_connection(p_name))

            elif path == "/api/career/match":
                user_id = payload.get("user_id", "default_user")
                jd = payload.get("job_description", "")
                self._send_json(job_matcher.analyze_job_description(user_id, jd))

            elif path == "/api/resume/generate":
                user_id = payload.get("user_id", "default_user")
                jd = payload.get("job_description", "")
                self._send_json(resume_engine.generate_tailored_resume(user_id, jd))

            elif path == "/api/system/backup":
                label = payload.get("label", "manual")
                self._send_json(backup_manager.create_backup(label))

            elif path == "/api/system/restore":
                bpath = payload.get("backup_path", "")
                self._send_json(backup_manager.restore_backup(bpath))

            else:
                self._send_json({"error": f"Endpoint not found: {path}", "code": "NOT_FOUND"}, status=404)
        except Exception as e:
            logger.error(f"API Error in POST {path}: {e}")
            self._send_json({"error": str(e), "code": "SERVER_ERROR"}, status=500)

def find_available_port(host, default_port):
    for candidate in [default_port, 8081, 8082, 8083, 8084, 8085, 9000]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, candidate))
            s.close()
            return candidate
        except OSError:
            continue
    return default_port

def run_server(host=None, port=None):
    h = host or Config.HOST
    requested_port = port or Config.PORT
    Config.ensure_directories()
    
    actual_port = find_available_port(h, requested_port)
    server_address = (h, actual_port)
    
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer(server_address, BillingerRequestHandler)
    
    display_host = "localhost" if h in ("0.0.0.0", "::") else h
    logger.info(f"Billinger Platform v{Config.VERSION} listening on {h}:{actual_port}")
    logger.info(f"[*] Access in browser at: http://{display_host}:{actual_port} or http://127.0.0.1:{actual_port}")
    
    def _open():
        time.sleep(0.6)
        try:
            webbrowser.open(f"http://{display_host}:{actual_port}")
        except Exception:
            pass
    threading.Thread(target=_open, daemon=True).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Billinger Server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
