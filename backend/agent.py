import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from backend.db import (
    get_policies,
    add_audit_log,
    add_agent_task
)


load_dotenv()


# ============================================================
# GROQ CLIENT
# ============================================================

def get_llm_client():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )


# ============================================================
# DOCUMENT AGENT
# ============================================================

def document_agent(application):

    issues = []

    verified = 0
    pending = 0
    mismatched = 0

    for document in application["documents"]:

        status = document["status"]

        if status == "VERIFIED":
            verified += 1

        elif status == "PENDING":
            pending += 1

            issues.append({
                "type": "DOCUMENT_PENDING",
                "document": document["document_type"],
                "severity": "MEDIUM",
                "message": (
                    f'{document["document_type"]} '
                    'has not been verified.'
                )
            })

        elif status == "MISMATCH":
            mismatched += 1

            issues.append({
                "type": "DOCUMENT_MISMATCH",
                "document": document["document_type"],
                "severity": "HIGH",
                "message": (
                    f'{document["document_type"]} '
                    'contains inconsistent information.'
                )
            })

    result = {
        "agent": "Document Intelligence Agent",
        "documents_checked": len(application["documents"]),
        "verified": verified,
        "pending": pending,
        "mismatched": mismatched,
        "issues": issues
    }

    add_agent_task(
        application["id"],
        "Document Intelligence Agent",
        "Verify application documents",
        "COMPLETED",
        json.dumps(result)
    )

    return result


# ============================================================
# FINANCIAL ANALYSIS AGENT
# ============================================================

def financial_agent(application):

    income = float(application["income"])
    requested_amount = float(application["requested_amount"])
    credit_score = int(application["credit_score"])

    loan_income_ratio = requested_amount / income

    risk_points = 0
    issues = []

    if credit_score < 650:

        risk_points += 40

        issues.append({
            "type": "LOW_CREDIT_SCORE",
            "severity": "HIGH",
            "message": (
                f"Credit score {credit_score} "
                "is below the minimum threshold."
            )
        })

    elif credit_score < 700:

        risk_points += 20

        issues.append({
            "type": "MODERATE_CREDIT_SCORE",
            "severity": "MEDIUM",
            "message": (
                f"Credit score {credit_score} "
                "falls within the moderate-risk range."
            )
        })

    if loan_income_ratio > 2:

        risk_points += 30

        issues.append({
            "type": "HIGH_LOAN_INCOME_RATIO",
            "severity": "HIGH",
            "message": (
                f"Requested amount is "
                f"{loan_income_ratio:.2f}x annual income."
            )
        })

    elif loan_income_ratio > 1:

        risk_points += 10

        issues.append({
            "type": "ELEVATED_LOAN_INCOME_RATIO",
            "severity": "MEDIUM",
            "message": (
                f"Requested amount is "
                f"{loan_income_ratio:.2f}x annual income."
            )
        })

    result = {
        "agent": "Financial Analysis Agent",
        "annual_income": income,
        "requested_amount": requested_amount,
        "loan_income_ratio": round(loan_income_ratio, 2),
        "credit_score": credit_score,
        "risk_points": risk_points,
        "issues": issues
    }

    add_agent_task(
        application["id"],
        "Financial Analysis Agent",
        "Evaluate financial risk",
        "COMPLETED",
        json.dumps(result)
    )

    return result


# ============================================================
# POLICY AGENT
# ============================================================

def policy_agent(application, document_result, financial_result):

    policies = get_policies()

    violations = []

    for issue in document_result["issues"]:
        violations.append(issue)

    for issue in financial_result["issues"]:
        violations.append(issue)

    risk_score = financial_result["risk_points"]

    for issue in document_result["issues"]:

        if issue["severity"] == "HIGH":
            risk_score += 30

        elif issue["severity"] == "MEDIUM":
            risk_score += 15

    # Cap score
    risk_score = min(risk_score, 100)

    if risk_score >= 60:
        decision = "ESCALATE"

    elif risk_score >= 30:
        decision = "REVIEW"

    else:
        decision = "LOW_RISK"

    result = {
        "agent": "Policy & Decision Agent",
        "policies_evaluated": len(policies),
        "risk_score": risk_score,
        "decision": decision,
        "violations": violations
    }

    add_agent_task(
        application["id"],
        "Policy & Decision Agent",
        "Evaluate credit policy",
        "COMPLETED",
        json.dumps(result)
    )

    return result


# ============================================================
# LLM REASONING AGENT
# ============================================================

def llm_reasoning_agent(
    application,
    document_result,
    financial_result,
    policy_result
):

    client = get_llm_client()

    # --------------------------------------------------------
    # No API key?
    # --------------------------------------------------------

    if client is None:

        return {
            "agent": "LLM Reasoning Agent",
            "status": "SKIPPED",
            "reasoning": (
                "Groq API key is not configured. "
                "Deterministic policy analysis was completed."
            )
        }

    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile"
    )

    context = {
        "application": application,
        "document_analysis": document_result,
        "financial_analysis": financial_result,
        "policy_analysis": policy_result
    }

    system_prompt = """
You are the reasoning layer of CortexOps, an autonomous
credit-operations system.

Your job is NOT to invent financial facts.

Use only the supplied application evidence.

Explain:
1. Main risk signals
2. Evidence supporting them
3. Why the policy engine produced its decision
4. What a human reviewer should check
5. Recommended next workflow action

Be concise, professional and explainable.

Never claim a loan is approved merely because risk is low.
CortexOps supports human-governed credit operations.
"""

    user_prompt = f"""
Analyze this credit application:

{json.dumps(context, indent=2)}

Return JSON with exactly these fields:

{{
    "summary": "...",
    "risk_explanation": "...",
    "evidence": ["...", "..."],
    "human_review": ["...", "..."],
    "next_action": "..."
}}
"""

    try:

        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        content = response.choices[0].message.content

        result = {
            "agent": "LLM Reasoning Agent",
            "status": "COMPLETED",
            "reasoning": content
        }

        add_agent_task(
            application["id"],
            "LLM Reasoning Agent",
            "Generate evidence-backed reasoning",
            "COMPLETED",
            content
        )

        return result

    except Exception as error:

        result = {
            "agent": "LLM Reasoning Agent",
            "status": "ERROR",
            "reasoning": (
                "LLM reasoning failed. "
                "Deterministic analysis remains available."
            ),
            "error": str(error)
        }

        add_agent_task(
            application["id"],
            "LLM Reasoning Agent",
            "Generate evidence-backed reasoning",
            "FAILED",
            str(error)
        )

        return result


# ============================================================
# VERIFICATION AGENT
# ============================================================

def verification_agent(
    application,
    document_result,
    financial_result,
    policy_result
):

    contradictions = []

    if policy_result["decision"] == "LOW_RISK":

        if document_result["mismatched"] > 0:
            contradictions.append(
                "Policy result indicates low risk despite "
                "document mismatches."
            )

        if financial_result["credit_score"] < 650:
            contradictions.append(
                "Policy result indicates low risk despite "
                "credit score below minimum threshold."
            )

    if contradictions:

        final_decision = "ESCALATE"

    else:

        final_decision = policy_result["decision"]

    result = {
        "agent": "Verification Agent",
        "verified": len(contradictions) == 0,
        "contradictions": contradictions,
        "final_decision": final_decision
    }

    add_agent_task(
        application["id"],
        "Verification Agent",
        "Challenge decision and detect contradictions",
        "COMPLETED",
        json.dumps(result)
    )

    return result


# ============================================================
# MASTER ORCHESTRATOR
# ============================================================

def analyze_application(application):

    application_id = application["id"]

    add_audit_log(
        application_id,
        "WORKFLOW_STARTED",
        "CortexOps autonomous credit workflow initiated."
    )

    # --------------------------------------------------------
    # STEP 1 — DOCUMENT INTELLIGENCE
    # --------------------------------------------------------

    document_result = document_agent(application)

    add_audit_log(
        application_id,
        "DOCUMENT_ANALYSIS_COMPLETED",
        json.dumps(document_result)
    )

    # --------------------------------------------------------
    # STEP 2 — FINANCIAL ANALYSIS
    # --------------------------------------------------------

    financial_result = financial_agent(application)

    add_audit_log(
        application_id,
        "FINANCIAL_ANALYSIS_COMPLETED",
        json.dumps(financial_result)
    )

    # --------------------------------------------------------
    # STEP 3 — POLICY DECISION
    # --------------------------------------------------------

    policy_result = policy_agent(
        application,
        document_result,
        financial_result
    )

    add_audit_log(
        application_id,
        "POLICY_ANALYSIS_COMPLETED",
        json.dumps(policy_result)
    )

    # --------------------------------------------------------
    # STEP 4 — LLM REASONING
    # --------------------------------------------------------

    llm_result = llm_reasoning_agent(
        application,
        document_result,
        financial_result,
        policy_result
    )

    add_audit_log(
        application_id,
        "LLM_REASONING_COMPLETED",
        json.dumps(llm_result)
    )

    # --------------------------------------------------------
    # STEP 5 — VERIFICATION
    # --------------------------------------------------------

    verification_result = verification_agent(
        application,
        document_result,
        financial_result,
        policy_result
    )

    add_audit_log(
        application_id,
        "DECISION_VERIFIED",
        json.dumps(verification_result)
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    final_result = {
        "application": application,

        "workflow": {
            "status": "COMPLETED",
            "steps": [
                "Document Intelligence",
                "Financial Analysis",
                "Policy Evaluation",
                "LLM Reasoning",
                "Verification"
            ]
        },

        "document_analysis": document_result,

        "financial_analysis": financial_result,

        "policy_analysis": policy_result,

        "llm_reasoning": llm_result,

        "verification": verification_result,

        "final_decision": verification_result["final_decision"]
    }

    add_audit_log(
        application_id,
        "WORKFLOW_COMPLETED",
        json.dumps({
            "decision": verification_result["final_decision"]
        })
    )

    return final_result