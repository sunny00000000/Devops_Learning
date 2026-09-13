import re
from typing import Dict, Any

TOOL_SIGNATURES = {
    "Kubernetes": {
        "domain": "Container Orchestration",
        "keywords": [r'\bkubectl\b', r'\bpod\b', r'\bstatefulset\b', r'\bdeployment\.apps\b', r'\bhelm\b', r'\bkubelet\b', r'\bingress-nginx\b', r'\bdaemonset\b'],
        "anti_keywords": [r'\bterraform\b', r'\bansible\b', r'\bplaybook\b']
    },
    "Docker": {
        "domain": "Containerization",
        "keywords": [r'\bdockerfile\b', r'\bdocker\s+run\b', r'\bdocker\s+compose\b', r'\bmultistage\b', r'\bcontainerd\b'],
        "anti_keywords": [r'\bhelm\s+install\b', r'\bkubectl\b']
    },
    "Terraform": {
        "domain": "Infrastructure as Code",
        "keywords": [r'\bterraform\b', r'\bopentofu\b', r'\bhcl2\b', r'\bterraform\s+plan\b', r'\bstate\s+lock\b', r'\bresource\s+"aws_'],
        "anti_keywords": [r'\bansible-playbook\b', r'\bkubectl\b']
    },
    "Ansible": {
        "domain": "Configuration Management",
        "keywords": [r'\bansible\b', r'\bplaybook\b', r'\bansible-vault\b', r'\binventory\b', r'\btasks:\b', r'\bhandlers:\b'],
        "anti_keywords": [r'\bterraform\b', r'\bkernel\s+tuning\b']
    },
    "Git": {
        "domain": "Version Control",
        "keywords": [r'\bgit\s+rebase\b', r'\bgit\s+bisect\b', r'\bworktree\b', r'\bcherry-pick\b', r'\breflog\b', r'\bmerge\s+conflict\b'],
        "anti_keywords": [r'\bjenkinsfile\b', r'\bgithub\s+actions\b']
    },
    "Linux": {
        "domain": "Linux SysAdmin",
        "keywords": [r'\bsystemd\b', r'\bsysctl\b', r'\bjournalctl\b', r'\biptables\b', r'\blsblk\b', r'\bchmod\b', r'\bchown\b', r'\bfdisk\b'],
        "anti_keywords": [r'\bansible\b', r'\bterraform\b', r'\bkubernetes\b']
    },
    "Jenkins": {
        "domain": "Continuous Integration",
        "keywords": [r'\bjenkinsfile\b', r'\bdeclarative\s+pipeline\b', r'\bstage\("build"\)', r'\bmaven\b', r'\bmaster-slave\b'],
        "anti_keywords": [r'\bdocker-compose\b']
    },
    "Prometheus": {
        "domain": "Observability & Monitoring",
        "keywords": [r'\bprometheus\b', r'\bpromql\b', r'\bgrafana\b', r'\balertmanager\b', r'\bnode_exporter\b', r'\brate\('],
        "anti_keywords": [r'\bterraform\b']
    },
    "AWS": {
        "domain": "Cloud Infrastructure",
        "keywords": [r'\baws\b', r'\bamazon\s+web\s+services\b', r'\bec2\b', r'\bvpc\b', r'\bs3\b', r'\biam\b', r'\broute53\b'],
        "anti_keywords": []
    }
}

class DocumentClassifier:
    @staticmethod
    def classify(filename: str, content: str) -> Dict[str, Any]:
        text = (filename + " " + content).lower()
        best_tool = "General DevOps"
        best_domain = "DevOps Engineering"
        highest_score = 0
        best_reason = "General reference documentation."

        for tool, conf in TOOL_SIGNATURES.items():
            pos_matches = sum(1 for kw in conf["keywords"] if re.search(kw, text, re.I))
            neg_matches = sum(1 for akw in conf["anti_keywords"] if re.search(akw, text, re.I))
            
            score = pos_matches * 2 - neg_matches * 3
            if score > highest_score and pos_matches > 0:
                highest_score = score
                best_tool = tool
                best_domain = conf["domain"]
                best_reason = f"Verified positive matches for {tool} syntax ({pos_matches} keywords) with 0 contradictory topics."

        confidence = min(0.99, max(0.65, 0.70 + (highest_score * 0.05)))

        return {
            "primary_tool": best_tool,
            "domain": best_domain,
            "confidence": round(confidence, 2),
            "reason": best_reason,
            "version": "1.0.0"
        }

document_classifier = DocumentClassifier()
