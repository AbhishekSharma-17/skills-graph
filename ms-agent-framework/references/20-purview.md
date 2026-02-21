# Purview Integration — Data Governance & Compliance

## Overview

Microsoft Purview integration with the Agent Framework enables enterprise-grade data governance, compliance, and responsible AI controls directly within agent runtime. Key capabilities include:

- **Content Safety**: Detect and block harmful content automatically
- **Data Classification**: Classify and track sensitive data through agent operations
- **PII Protection**: Identify and handle personally identifiable information
- **Audit Trails**: Maintain compliance with regulatory requirements (GDPR, HIPAA, SOC 2)
- **Responsible AI**: Jailbreak detection, prompt injection protection, transparency logging

---

## Azure AI Content Safety Integration

Content Safety analyzes text and images for harmful categories and blocks execution when thresholds are exceeded.

### Basic Setup

```python
from agent_framework.safety import ContentSafetyMiddleware
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential

# Initialize Content Safety client
endpoint = "https://<resource-name>.cognitiveservices.azure.com/"
key = "<your-api-key>"

safety_client = ContentSafetyClient(endpoint, AzureKeyCredential(key))

# Create middleware with default settings
safety_middleware = ContentSafetyMiddleware(
    client=safety_client,
    block_categories=["hate", "sexual", "violence", "self_harm"],
    severity_threshold=2  # 0=safe, 7=most harmful; block if >= threshold
)

# Attach to agent
from agent_framework import ChatAgent

agent = ChatAgent(
    name="SafetyAwareAgent",
    chat_client=client,
    middleware=[safety_middleware]
)
```

### Advanced Configuration

```python
from agent_framework.safety import ContentSafetyMiddleware, SafetyConfig

safety_config = SafetyConfig(
    # Categories to monitor and block
    block_categories={
        "hate": {"enabled": True, "threshold": 2},
        "sexual": {"enabled": True, "threshold": 2},
        "violence": {"enabled": True, "threshold": 3},
        "self_harm": {"enabled": True, "threshold": 2},
    },
    # Analyze user input, agent output, or both
    analyze_input=True,
    analyze_output=True,

    # Action on violation
    action_on_violation="block",  # "block", "log", "alert", or "custom"
    violation_callback=lambda cat, score: print(f"Content safety: {cat}={score}"),

    # Filtering options
    filter_profanity=True,
    filter_jailbreak_attempts=True,

    # Logging
    log_all_checks=False,  # Set True for audit trail
)

safety_middleware = ContentSafetyMiddleware(
    client=safety_client,
    config=safety_config
)
```

### Content Safety Categories

Each category has severity scores from 0 (safe) to 7 (most harmful).

#### Hate

- **Definition**: Content that promotes discrimination or violence against individuals based on protected characteristics
- **Examples**: Slurs, derogatory statements, promotion of discrimination
- **Severity Levels**:
  - 0: Safe
  - 2-4: Low-medium concern
  - 6-7: High severity, recommend blocking

```python
# Example detection
safety_result = safety_client.analyze_text(
    text="[potentially offensive content]"
)

print(f"Hate severity: {safety_result.categories_analysis[0].severity}")
```

#### Sexual

- **Definition**: Content involving sexual acts, exploitation, or abuse
- **Examples**: Explicit descriptions, non-consensual content, child safety concerns
- **Severity Levels**: 0-7 scale

#### Violence

- **Definition**: Content depicting violence, harm, or threats
- **Examples**: Instructions for violence, graphic violence, threats
- **Severity Levels**: 0-7 scale

#### Self-Harm

- **Definition**: Content promoting self-injury or suicide
- **Examples**: Suicide methods, self-harm instructions, eating disorders content
- **Severity Levels**: 0-7 scale

### Handling Safety Violations

```python
from agent_framework import Middleware

class SafetyViolationHandler(Middleware):
    """Custom handler for safety violations."""

    async def on_invoke(self, agent_state):
        """Check user input for violations."""
        try:
            result = await safety_client.analyze_text(agent_state.message)

            for analysis in result.categories_analysis:
                if analysis.severity >= SEVERITY_THRESHOLD:
                    # Log violation
                    logger.warning(
                        f"Safety violation: {analysis.category} (severity={analysis.severity})"
                    )

                    # Optionally block execution
                    if should_block(analysis.category, analysis.severity):
                        raise ValueError(f"Message blocked: {analysis.category}")

        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            # Fail open or closed based on policy
            if FAIL_CLOSED:
                raise

agent = ChatAgent(
    name="CompliantAgent",
    chat_client=client,
    middleware=[SafetyViolationHandler()]
)
```

---

## Data Governance

Integrate with Purview's data classification and governance capabilities.

### Data Classification Middleware

```python
from agent_framework import Middleware
from azure.purview.catalog import PurviewCatalogClient

class DataClassificationMiddleware(Middleware):
    """Classify and track data flowing through agent."""

    def __init__(self, purview_endpoint, auth_credential):
        self.purview_client = PurviewCatalogClient(
            endpoint=purview_endpoint,
            credential=auth_credential
        )

    async def on_invoke(self, agent_state):
        """Classify user input data."""
        # Extract entities and classify
        entities = self._extract_entities(agent_state.message)

        for entity in entities:
            classification = await self._classify_entity(entity)
            agent_state.metadata["data_classification"] = classification

            # Log for audit trail
            logger.info(
                f"Data classified: {entity['type']}={classification}",
                extra={"session_id": agent_state.session_id}
            )

    async def _classify_entity(self, entity):
        """Use Purview to classify an entity."""
        # Example classification logic
        if entity["type"] == "email":
            return "PII"
        elif entity["type"] == "credit_card":
            return "HIGHLY_SENSITIVE"
        else:
            return "GENERAL"

    def _extract_entities(self, text):
        """Extract entities from text (simplified)."""
        import re
        entities = []

        # Email pattern
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({"type": "email", "value": email})

        # Credit card pattern (simplified)
        cards = re.findall(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', text)
        for card in cards:
            entities.append({"type": "credit_card", "value": card})

        return entities
```

### Sensitive Data Handling

```python
from agent_framework.safety import SensitiveDataHandler, SensitivityLevel

# Configure sensitive data patterns
sensitive_patterns = {
    "credit_card": {
        "pattern": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "sensitivity": SensitivityLevel.CRITICAL,
        "action": "redact"  # or "block", "log"
    },
    "ssn": {
        "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
        "sensitivity": SensitivityLevel.HIGH,
        "action": "redact"
    },
    "email": {
        "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "sensitivity": SensitivityLevel.MEDIUM,
        "action": "log"
    }
}

# Create handler
handler = SensitiveDataHandler(patterns=sensitive_patterns)

# Redact data in responses
response = agent.invoke("Process this: john.doe@example.com")
redacted_response = handler.redact(response)  # john.***@example.com
```

### Tracking Data Lineage

```python
from agent_framework import Middleware
from opentelemetry import trace

class DataLineageMiddleware(Middleware):
    """Track data lineage through agent pipeline."""

    async def on_invoke(self, agent_state):
        """Record input data source."""
        span = trace.get_current_span()
        span.set_attribute("data.source", agent_state.context.get("source"))
        span.set_attribute("data.classification", agent_state.metadata.get("classification"))

    async def on_chat(self, agent_state):
        """Record model processing."""
        span = trace.get_current_span()
        span.set_attribute("processing.model", agent_state.chat_client.model)

    async def on_tool_execute(self, agent_state, tool_result):
        """Record tool access to data."""
        span = trace.get_current_span()
        span.set_attribute("tool.name", tool_result.tool_name)
        span.set_attribute("data.accessed_by", tool_result.tool_name)
```

---

## Compliance & Audit

Maintain compliance with regulatory requirements through comprehensive audit trails.

### Audit Logging Middleware

```python
from agent_framework import Middleware
from datetime import datetime
import json

class AuditLoggingMiddleware(Middleware):
    """Log all agent operations for compliance audits."""

    def __init__(self, audit_log_path):
        self.audit_log = open(audit_log_path, 'a')

    async def on_invoke(self, agent_state):
        """Log agent invocation."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "agent_invoke",
            "agent_name": agent_state.agent.name,
            "session_id": agent_state.session_id,
            "user_id": agent_state.context.get("user_id"),
            "input_length": len(agent_state.message),
            "input_hash": self._hash(agent_state.message),  # Don't log raw PII
        }
        self._log_audit(audit_entry)

    async def on_chat(self, agent_state):
        """Log chat operation."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "chat_completion",
            "model": agent_state.chat_client.model,
            "tokens_input": agent_state.usage.input_tokens,
            "tokens_output": agent_state.usage.output_tokens,
            "finish_reason": agent_state.finish_reason,
        }
        self._log_audit(audit_entry)

    async def on_tool_execute(self, agent_state, tool_result):
        """Log tool execution."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "tool_execute",
            "tool_name": tool_result.tool_name,
            "tool_input_hash": self._hash(str(tool_result.tool_input)),
            "success": tool_result.success,
        }
        self._log_audit(audit_entry)

    def _log_audit(self, entry):
        """Write audit entry to log."""
        self.audit_log.write(json.dumps(entry) + "\n")
        self.audit_log.flush()

    def _hash(self, data):
        """Hash data to avoid logging sensitive information."""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()
```

### GDPR Compliance

```python
from agent_framework import Middleware
from datetime import datetime, timedelta

class GDPRComplianceMiddleware(Middleware):
    """Implement GDPR requirements: consent, right to erasure, data retention."""

    def __init__(self, data_retention_days=30):
        self.data_retention_days = data_retention_days

    async def on_invoke(self, agent_state):
        """Check user consent."""
        user_id = agent_state.context.get("user_id")

        # Verify user has given consent
        has_consent = await self._check_consent(user_id)
        if not has_consent:
            raise ValueError("User has not provided consent for data processing")

    async def _check_consent(self, user_id):
        """Check if user has active consent."""
        # Query consent database
        from datetime import datetime
        consent_record = consent_db.get(user_id)

        if not consent_record:
            return False

        if consent_record["expires_at"] < datetime.utcnow():
            return False

        return consent_record["given"]

    def right_to_erasure(self, user_id):
        """Implement right to be forgotten."""
        # Delete all data associated with user
        conversations = db.query(
            "SELECT * FROM conversations WHERE user_id = ?", user_id
        )

        for conversation in conversations:
            # Erase conversation
            db.delete(conversation)

            # Erase associated audit logs
            db.delete_where(
                "audit_logs",
                "session_id", conversation.session_id
            )

        logger.info(f"User {user_id}: right to erasure executed")

    def get_user_data(self, user_id):
        """Implement right to data portability."""
        data = {
            "conversations": db.query("SELECT * FROM conversations WHERE user_id = ?", user_id),
            "audit_logs": db.query("SELECT * FROM audit_logs WHERE user_id = ?", user_id),
            "preferences": db.query("SELECT * FROM preferences WHERE user_id = ?", user_id),
        }
        return data
```

### HIPAA Compliance

```python
from agent_framework.safety import HealthcareMiddleware, PHICategory

# Configure HIPAA middleware
healthcare_middleware = HealthcareMiddleware(
    protected_categories={
        PHICategory.MEDICAL_RECORD_NUMBER: {"enabled": True, "action": "redact"},
        PHICategory.PATIENT_NAME: {"enabled": True, "action": "redact"},
        PHICategory.DIAGNOSIS: {"enabled": True, "action": "log"},
        PHICategory.PRESCRIPTION: {"enabled": True, "action": "log"},
    },
    # Require encryption for data at rest
    encryption_required=True,
    # Require audit logging of all PHI access
    audit_all_phi_access=True,
    # Track data access for breach notification
    track_access_history=True,
)

# Create HIPAA-compliant agent
healthcare_agent = ChatAgent(
    name="HealthcareAdvisor",
    chat_client=client,
    middleware=[healthcare_middleware]
)
```

### SOC 2 Compliance

```python
from agent_framework.compliance import SOC2ComplianceMiddleware

soc2_middleware = SOC2ComplianceMiddleware(
    # Security: Monitor unauthorized access attempts
    monitor_unauthorized_access=True,

    # Availability: Track uptime and performance
    monitor_availability=True,
    slo_latency_ms=1000,
    slo_availability_percent=99.9,

    # Processing Integrity: Validate all inputs
    validate_input_integrity=True,

    # Confidentiality: Encrypt sensitive data
    encrypt_pii=True,
    encryption_algorithm="AES-256",

    # Privacy: Implement data minimization
    minimize_data_collection=True,

    # Generate compliance reports
    generate_monthly_reports=True,
)

agent = ChatAgent(
    name="ComplianceAwareAgent",
    chat_client=client,
    middleware=[soc2_middleware]
)
```

---

## Responsible AI

Implement responsible AI controls to ensure ethical and transparent agent behavior.

### Jailbreak Detection

```python
from agent_framework.safety import JailbreakDetectionMiddleware

jailbreak_detector = JailbreakDetectionMiddleware(
    # Detect common jailbreak patterns
    detect_role_play_attacks=True,
    detect_prompt_injection=True,
    detect_token_smuggling=True,
    detect_encoding_attacks=True,

    # Block or alert on detection
    action_on_jailbreak="block",  # or "alert", "log"

    # Custom jailbreak patterns
    custom_patterns=[
        r"ignore previous instructions",
        r"pretend you are",
        r"system override",
    ]
)

agent = ChatAgent(
    name="RobustAgent",
    chat_client=client,
    middleware=[jailbreak_detector]
)
```

### Prompt Injection Protection

```python
from agent_framework.safety import PromptInjectionMiddleware

injection_detector = PromptInjectionMiddleware(
    # Detect injection attempts
    detect_system_prompt_leaks=True,
    detect_context_poisoning=True,
    detect_malicious_tool_calls=True,

    # Sanitization options
    sanitize_input=True,
    sanitize_output=True,

    # Validation
    validate_tool_parameters=True,
    validate_json_responses=True,
)

agent = ChatAgent(
    name="SecurityHardenedAgent",
    chat_client=client,
    middleware=[injection_detector]
)
```

### Transparency & Explainability

```python
from agent_framework import Middleware

class TransparencyMiddleware(Middleware):
    """Log all decisions for explainability."""

    async def on_invoke(self, agent_state):
        """Record the original user request."""
        agent_state.metadata["original_request"] = agent_state.message

    async def on_tool_execute(self, agent_state, tool_result):
        """Log why a tool was selected and executed."""
        logger.info(
            f"Tool selected: {tool_result.tool_name}",
            extra={
                "reasoning": tool_result.reasoning,
                "parameters": str(tool_result.tool_input),
                "session_id": agent_state.session_id,
            }
        )

    async def on_error(self, agent_state, error):
        """Log errors for transparency."""
        logger.error(
            f"Agent error: {error}",
            extra={
                "session_id": agent_state.session_id,
                "error_type": type(error).__name__,
            }
        )

# Generate explainability report
def generate_explainability_report(session_id):
    """Create a human-readable explanation of agent decisions."""
    logs = logger.get_logs(session_id)

    report = {
        "session_id": session_id,
        "original_request": logs[0]["original_request"],
        "decision_path": [],
        "errors": [],
        "tools_used": [],
    }

    for log in logs:
        if log["event"] == "tool_execute":
            report["tools_used"].append({
                "name": log["tool_name"],
                "reasoning": log.get("reasoning"),
                "success": log.get("success"),
            })
        elif log["event"] == "error":
            report["errors"].append(log["message"])

    return report
```

### Human Oversight Integration

```python
from agent_framework import Middleware

class HumanOversightMiddleware(Middleware):
    """Require human approval for sensitive operations."""

    async def on_invoke(self, agent_state):
        """Check if operation requires human approval."""
        sensitivity_level = await self._assess_sensitivity(agent_state.message)

        if sensitivity_level == "HIGH":
            # Require human approval
            approval = await self._request_human_approval(
                user_message=agent_state.message,
                sensitivity_level=sensitivity_level,
                timeout_seconds=300
            )

            if not approval:
                raise ValueError("Human approval required but not obtained")

    async def _assess_sensitivity(self, message):
        """Assess if operation is sensitive."""
        keywords = ["delete", "modify", "financial", "personal"]

        for keyword in keywords:
            if keyword.lower() in message.lower():
                return "HIGH"

        return "LOW"

    async def _request_human_approval(self, user_message, sensitivity_level, timeout_seconds):
        """Request human approval via some notification system."""
        # Example: Send to approval queue
        approval_request = {
            "id": uuid.uuid4(),
            "message": user_message,
            "sensitivity": sensitivity_level,
            "timestamp": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=timeout_seconds),
        }

        approval_queue.put(approval_request)

        # Wait for response
        while True:
            response = approval_responses.get(approval_request.id, None)
            if response:
                return response.approved

            if datetime.utcnow() > approval_request.expires_at:
                return False

            await asyncio.sleep(1)
```

---

## When to Use Purview Integration

| Scenario | Use Purview | Notes |
|----------|-------------|-------|
| Enterprise deployments | YES | Essential for large organizations |
| Regulated industries | YES | Mandatory for HIPAA, PCI-DSS, etc. |
| PII in conversations | YES | Protect customer/employee data |
| Financial applications | YES | Content safety + compliance |
| Healthcare applications | YES | HIPAA + sensitive data handling |
| Public-facing agents | YES | Jailbreak + prompt injection protection |
| Internal tools | OPTIONAL | Lower risk, but recommended |
| Research/prototyping | NO | Add later when productionizing |

---

## Complete Example: Compliant Healthcare Agent

```python
from agent_framework import ChatAgent
from agent_framework.safety import (
    ContentSafetyMiddleware,
    HealthcareMiddleware,
    PromptInjectionMiddleware,
)
from agent_framework.compliance import AuditLoggingMiddleware, GDPRComplianceMiddleware

# Initialize clients
chat_client = AzureOpenAIClient(...)
content_safety_client = ContentSafetyClient(...)

# Configure middleware stack
middleware = [
    # Security: Block harmful content
    ContentSafetyMiddleware(
        client=content_safety_client,
        block_categories=["hate", "sexual", "violence", "self_harm"],
        severity_threshold=2
    ),

    # Healthcare: Protect PHI
    HealthcareMiddleware(
        encrypt_pii=True,
        audit_all_access=True,
    ),

    # Security: Prevent injection attacks
    PromptInjectionMiddleware(
        detect_system_prompt_leaks=True,
        validate_tool_parameters=True,
    ),

    # Compliance: GDPR
    GDPRComplianceMiddleware(data_retention_days=90),

    # Audit: Log everything
    AuditLoggingMiddleware(audit_log_path="/var/log/agent-audit.jsonl"),
]

# Create compliant agent
healthcare_agent = ChatAgent(
    name="HealthcareAssistant",
    chat_client=chat_client,
    middleware=middleware,
    system_prompt="""You are a healthcare assistant. You:
    - Never diagnose medical conditions
    - Always recommend consulting healthcare professionals
    - Protect patient privacy at all times
    - Refuse any requests that could harm users
    """
)

# Use the agent
result = await healthcare_agent.invoke(
    "I have symptoms of the flu. What should I do?",
    context={"user_id": "patient_123"}
)
```

---

## Summary

Purview integration provides:

1. **Content Safety**: Block harmful content at runtime
2. **Data Governance**: Classify and track sensitive data
3. **Compliance**: Meet regulatory requirements (GDPR, HIPAA, SOC 2)
4. **Responsible AI**: Jailbreak detection, transparency, human oversight
5. **Audit Trails**: Complete logging for security investigations

For enterprise agents handling sensitive data or operating in regulated industries, Purview integration is essential.
