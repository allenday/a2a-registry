# A2A Agent Registry Implementation Spec

## Overview
This document outlines a pragmatic approach to building a registry for A2A agents, addressing gaps in the A2A protocol specification (e.g., public key discovery, signing authority, key distribution, and trust bootstrapping). The registry will serve as a curated, discoverable repository for AgentCards, emphasizing zero-trust principles, security best practices, and flexibility for future A2A updates. It draws from established standards like JOSE/JWS, JWKS, and HTTPS/TLS to ensure verifiable trust.

Key goals:
- Enable secure submission, validation, and discovery of AgentCards.
- Mitigate risks like spoofing, tampering, or unauthorized claims.
- Provide features for semantic search, filtering, and trust indicators.
- Start curated (manual/semi-automated approvals) for quality control, with potential for scaling.

## Key Principles
- **Zero-Trust Foundation**: Always verify identities, signatures, and claims cryptographically.
- **Curated Registry**: Centralized governance to maintain security and quality.
- **Standards Adoption**: Use JWKS for keys, HTTPS/TLS for bootstrapping, and JWS for signatures.
- **Risk Mitigation**: Focus on defenses against impersonation and tampering via workflows and monitoring.
- **Scalability and Flexibility**: Design for easy integration and adaptation to A2A evolutions.

## Registry Structure and Features
- **Storage**: Use a database (e.g., PostgreSQL with JSONB) to store validated AgentCards, including metadata like provider details, capabilities, trust status, and reputation scores.
- **Discovery Features**:
  - Semantic search on skills/capabilities.
  - Filtering by organization, security schemes, or trust level.
  - API endpoints (e.g., GET /agents?capability=translation).
- **Hosting**: Deploy at a domain like a2aregistry.example.com with an API for submissions and queries.

## Submission Process
- **Requirements**:
  - Providers must host their AgentCard at `/.well-known/agent.json` on their domain (e.g., https://provider.com/.well-known/agent.json).
  - Submit the card URL, claimed organization (from `AgentProvider.organization`), and optional test credentials (e.g., API keys).
- **Enforcement**:
  - Validate schema against A2A proto definitions (e.g., required fields like `signatures`).
  - For `AgentSkill` entries:
    - If pointing to HTTP URLs, fetch over HTTPS, validate TLS cert, and check conformance to expected formats (e.g., JSON/proto). Optionally attest via test calls.
    - For non-HTTP URIs (e.g., `data:`), accept if embedding verifiable data; reject complex/opaque URIs.

## Trust Bootstrapping and Verification Workflow
- **Domain Ownership Check**: Verify submitter controls the domain (e.g., DNS TXT records, meta tags, or email to admin@domain.com).
- **Signature Validation**:
  - Fetch AgentCard over HTTPS with TLS validation.
  - Require public keys at `/.well-known/jwks.json` on the provider's domain.
  - Use JWS header (e.g., `kid` or `jku`) to resolve keys from JWKS.
  - Verify `AgentCard.signatures` to ensure integrity and authenticity.
  - Ensure domain matches claimed `AgentProvider.organization` (e.g., reject non-google.com claiming "Google").
- **Approval Workflow**:
  - Manual/semi-automated review: Scan for vulnerabilities (e.g., prompt injection), test skills, and issue endorsements.
  - For high-trust organizations, require additional evidence (e.g., corporate email).
- **Reputation and Checks**:
  - Assign trust scores based on domain age, TLS cert issuer, or interaction history.
  - Monitor post-registration for anomalies.

## Key Management and Signing Authority
- **Public Key Discovery/Distribution**: Fetch from provider's `/.well-known/jwks.json`; cache with short TTL (e.g., 24 hours) and rotation handling.
- **Signing Authority**: Domain key is authoritative; flag/require multi-signatures for critical cards. Use registry's key for endorsements.
- **Security**: Store keys in HSMs or cloud KMS; enforce 90-day rotation; use mTLS for interactions.

## Publication and Maintenance
- **Querying**: Make cards available with metadata (e.g., "Verified Domain: Yes; Signature Valid: Yes").
- **Observability**: Log accesses, audit changes, use honeypots for threat detection.
- **Updates**: Allow card refreshes with re-verification triggers.

## AgentExtension Trust Model and URI Allowlist
AgentExtensions derive trust through provenance from verified AgentCards, creating a secure, scalable trust model:

**URI Allowlist Policy**:
- Registry maintains a strict allowlist of permitted extension URIs
- New extension URIs can only be introduced by verified/signed AgentCards
- Subsequent agents may reference existing URIs from the allowlist with full provenance tracking
- Unverified agents cannot introduce new extension URIs

**Trust Inheritance**:
- Extensions gain trust from the first verified AgentCard that declares them
- Third-party agents can reference the same extension URI, inheriting the original trust provenance
- Registry tracks: `extension_uri → original_declaring_agent → trust_level`
- Users see clear provenance: "Extension originally verified via Google Agent (Verified Badge)"

**Registration Flow**:
1. Agent submits signed AgentCard with `capabilities.extensions[].uri`
2. Registry validates card signatures and domain ownership
3. If verified: Add new extension URIs to allowlist with provenance metadata
4. Future agents can reference allowlisted URIs (but cannot introduce arbitrary new URIs)

**Security Benefits**:
- Prevents URI injection attacks from malicious agents
- Establishes clear provenance chain for every extension
- Stops unauthorized domain claims or extension squatting
- Enables trust assessment: "This agent uses 3 verified extensions from trusted sources"

## Proposed Verification Badge System
To enhance trust and usability, implement a "verified" badge for submitted AgentCards (and by extension, any referenced extensions):
- **Verified Badge**:
  - Awarded to cards passing full validation (domain ownership, signature check, schema conformance, and manual review).
  - Includes provenance linking back to the owner domain (e.g., a verifiable chain showing the card was fetched from `/.well-known/agent.json` and signed by the domain's key).
  - Displayed in registry listings and APIs (e.g., { "status": "verified", "provenance": "Signed by key from provider.com/.well-known/jwks.json" }).
  - Extensions referenced by verified cards inherit verification status with provenance attribution.
- **Unverified Status**:
  - Applied to submissions failing checks or pending review.
  - Subject to deletion after a grace period (e.g., 30 days) or upon detection of issues (e.g., spoofing attempts).
  - Users querying the registry should see warnings for unverified entries to encourage caution.

This system promotes transparency, reduces risks, and incentivizes providers to follow best practices while establishing a clear trust model for extensions.

## Testing and Iteration
- **MVP Approach**: Bootstrap with known providers; simulate attacks (e.g., forged signatures).
- **Monitoring**: Track A2A repo for updates; adapt modularly (e.g., pluggable key resolvers).
- **Open-Sourcing**: Consider sharing code for community input.

## Tools and Technologies
- **Verification**: JOSE libraries (e.g., `jose` in Node.js/Python); Let's Encrypt for TLS.
- **Backend**: PostgreSQL, FastAPI/Express.js for APIs.
- **Security**: OWASP ZAP for scans.
- **Enhancements**: Pinecone for semantic search.

## Risks and Mitigations
| Aspect          | Potential Risk                  | Mitigation                          |
|-----------------|---------------------------------|-------------------------------------|
| Spoofing       | Fake organization claims       | Domain verification + manual review |
| Key Compromise | Stolen keys tampering cards    | Rotation, HSMs, reputation monitoring |
| Scalability    | High submission volume         | Curated approvals; automate low-risk |
| Interop        | A2A changes breaking model     | Modular design; track GitHub issues |

This spec provides a solid foundation for implementation. Questions? Let's discuss in the next engineering sync.