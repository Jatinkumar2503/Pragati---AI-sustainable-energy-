# PRAGATI AI — Production Payment Integration & Architecture Guide
**Confidential & Technical Specification**  
**Team Polaris | CodeWord 2.0 Hackathon**

---

## 1. Executive Summary & Current Operational Status

The current PRAGATI AI billing engine (`backend/api_billing.py`) operates in a **strictly isolated, deterministic test sandbox** using the test key `rzp_test_PRAGATI2026`. 

In compliance with hackathon safety rules and PCI-DSS / RBI compliance guidelines, **live production payments are intentionally deactivated**. Real financial transactions must never be executed without formal business entity incorporation, verified merchant KYC, and dedicated security infrastructure.

This document details the exact requirements, technical specifications, and security protocols required to transition PRAGATI AI's SaaS subscription engine to live Razorpay production processing.

---

## 2. Prerequisites for Production Readiness

### 2.1 Legal and Regulatory Onboarding
- **Registered Corporate Entity:** Private Limited Company or LLP registered with the Ministry of Corporate Affairs (MCA), India.
- **GSTIN & PAN Verification:** Verified 15-digit GSTIN linked with current commercial bank accounts for automatic CGST/SGST (9% + 9%) or IGST (18%) remittances.
- **Razorpay Merchant KYC:** Submission of Certificate of Incorporation, MOA/AOA, authorized signatory KYC, and registered industrial office proof.
- **Current Account Settlement Escrow:** Linking of RBI-compliant merchant nodal/escrow account for T+2 settlements.

### 2.2 Infrastructure & Credential Management
- **Zero Secrets in Source Control:** Neither `RAZORPAY_KEY_ID` nor `RAZORPAY_KEY_SECRET` should ever be hardcoded or checked into Git.
- **Secrets Vault:** Credentials must be provisioned via environment variables or secret vaults:
  - `RAZORPAY_KEY_ID`: Public key exposed to the frontend checkout modal.
  - `RAZORPAY_KEY_SECRET`: Private server-side key stored in AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.
  - `RAZORPAY_WEBHOOK_SECRET`: HMAC-SHA256 secret key for cryptographically validating incoming webhook events.

---

## 3. End-to-End Architectural Flow

```
[ Industrial Client / Browser ]
           │
           │ 1. POST /api/v1/billing/subscribe {plan_tier, gstin}
           ▼
[ PRAGATI AI FastAPI Server ] ──(Calls Razorpay Orders API)──► [ Razorpay Server ]
           │                                                           │
           │ 2. Returns order_id, amount_in_paise, key_id              │
           ▼                                                           │
[ Client Opens Razorpay Checkout ]                                     │
           │                                                           │
           │ 3. User pays via UPI / Corporate NetBanking / Card       │
           ▼                                                           │
[ Razorpay Checkout Callback ]                                         │
           │                                                           │
           │ 4. Submits payment_id, order_id, signature                │
           ▼                                                           │
[ PRAGATI AI Backend: POST /verify ]                                   │
           │ ── Validates HMAC-SHA256 signature                        │
           ▼                                                           │
[ Database Transaction ]                                               │
           │ ── Idempotently marks subscription ACTIVE                 │
           ▼                                                           │
[ Webhook Ingestion: POST /webhook ] ◄─────────────────────────────────┘
             ── Reconciles async payment captures and refunds
```

---

## 4. Server-Side Signature Verification & Idempotency

### 4.1 Payment Verification Algorithm
Every payment completed on the frontend delivers three tokens:
1. `razorpay_order_id`
2. `razorpay_payment_id`
3. `razorpay_signature`

The backend must cryptographically compute the HMAC-SHA256 digest of `order_id + "|" + payment_id` using `RAZORPAY_KEY_SECRET`:

```python
import hmac
import hashlib

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str, secret: str) -> bool:
    message = f"{order_id}|{payment_id}".encode("utf-8")
    generated_signature = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_signature, signature)
```

### 4.2 Webhook Signature Validation
Razorpay webhooks dispatch events asynchronously (e.g., `payment.captured`, `subscription.charged`, `payment.failed`).
The raw request payload bytes must be verified against the header `X-Razorpay-Signature`:

```python
def verify_webhook_signature(raw_body: bytes, webhook_signature: str, webhook_secret: str) -> bool:
    generated_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_sig, webhook_signature)
```

### 4.3 Idempotency Enforcement
Network retries and duplicate webhooks must not create duplicate billing records or double-charge subscribers:
1. **Unique Index on Database:** `razorpay_payment_id` must have a `UNIQUE` constraint in the payments table.
2. **State Machine Transitions:**
   - `CREATED` ➔ `AUTHORIZED` ➔ `CAPTURED` ➔ `ACTIVE`
   - Disallow re-processing if state is already `ACTIVE` or `CAPTURED`.

---

## 5. Tax Invoicing & GST Compliance

In compliance with Rule 46 of the CGST Rules, 2017:
- **SAC Code for Industrial Energy AI Software:** `998314` (Information Technology design and development services) or `998315` (Hosting and IT infrastructure provisioning).
- **Tax Breakdown:**
  - **Intra-State Supply (e.g. Haryana Supplier ➔ Haryana Facility):** CGST 9% + SGST 9%
  - **Inter-State Supply (e.g. Haryana Supplier ➔ Maharashtra Facility):** IGST 18%
- **Mandatory Invoice Fields:**
  - Sequential Invoice Number (e.g. `INV-2026-0042`)
  - Date of Invoice
  - Supplier Legal Name, Registered Address, and GSTIN
  - Recipient Facility Name, Address, and 15-digit GSTIN
  - HSN/SAC Code
  - Taxable value, applicable GST rate, and breakdown amounts
  - Cryptographically signed IRN (Invoice Reference Number) via GST e-Invoicing Portal for enterprises exceeding statutory turnover thresholds.

---

## 6. Failure Modes and Recovery

| Failure Scenario | Immediate Action | Recovery Strategy |
| :--- | :--- | :--- |
| **Network Timeout during Checkout** | UI notifies user; does not debit twice | Webhook `payment.failed` logged; checkout can be re-attempted with same order ID |
| **Signature Mismatch** | HTTP 400 Bad Request returned; event logged | Security alert flagged; no database modification |
| **Webhook Delivery Delay** | Polling job queries Razorpay Payments API | Fallback cron job `/api/v1/billing/reconcile` checks unverified orders older than 15 min |
| **Subscription Renewal Failure** | 3-day grace period granted | Automated email notification dispatched; system downgrades to Free tier after 7 days |

---

## 7. Migration Checklist from Sandbox to Production

1. [ ] Complete legal incorporation and corporate bank account activation.
2. [ ] Submit merchant documents and achieve Razorpay Account Activation.
3. [ ] Generate live API Keys (`rzp_live_...`) in Razorpay Dashboard.
4. [ ] Store live keys in secure environment variables:
   - `export RAZORPAY_KEY_ID="rzp_live_..."`
   - `export RAZORPAY_KEY_SECRET="<vault_secret>"`
   - `export RAZORPAY_WEBHOOK_SECRET="<vault_webhook_secret>"`
5. [ ] Register production webhook URL `https://api.pragati-ai.com/api/v1/billing/razorpay/webhook`.
6. [ ] Subscribe to events: `order.paid`, `payment.captured`, `subscription.charged`, `payment.failed`.
7. [ ] Execute end-to-end INR 1.00 live transaction and test refund cycle.
8. [ ] Validate automated PDF invoice generation with correct GST calculation.
