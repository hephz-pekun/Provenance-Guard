# Provenance Guard

## Overview

Provenance Guard is a Flask-based content attribution system that estimates whether a submitted piece of text is likely human-written or AI-generated. The system combines multiple independent detection signals into a confidence score and presents results through transparent user-facing labels.

Rather than making definitive claims about authorship, the system emphasizes:

- Transparency
- Confidence reporting
- Appeals and contestability
- Auditability
- Responsible AI attribution

The goal is not perfect AI detection. Instead, the system provides an explainable attribution workflow that allows creators to understand and challenge system decisions.

---

## Repository Structure

```text
Provenance-Guard/
├── app.py
├── detector.py
├── audit_log.json
├── requirements.txt
├── planning.md
├── README.md
└── .env
```

---

# Architecture Overview

## Submission Flow

``text
POST /submit
      |
      v
Text Content
Metadata
      |
      v
LLM Classification
      |
      v
Stylometric Analysis
      |
      v
Repetition Analysis
      |
      v
Metadata Analysis
      |
      v
Confidence Score Calculation
      |
      v
Transparency Label
      |
      v
Audit Log
``

## Appeal Flow

```text
POST /appeal
      |
      v
Locate Content
      |
      v
Store Creator Reasoning
      |
      v
Update Status (under_review)
      |
      v
Audit Log Entry
      |
      v
JSON Response
```

A submission passes through two independent detection systems before a combined confidence score is calculated. The confidence score determines the attribution result and transparency label returned to the user.

Appeals bypass the detection pipeline and instead update the content record while preserving a reviewable audit trail.

---

# Detection Signals

## Signal 1: LLM-Based Classification

### What It Measures

The first signal uses GPT-OSS-20B through Groq to evaluate:

- Writing coherence
- Semantic consistency
- Predictability
- Typical AI writing patterns
- Generic phrasing

### Why It Was Chosen

Large language models can identify subtle semantic and stylistic patterns that are difficult to represent using manually defined rules.

### Limitations

- Highly polished human writing may appear AI-generated.
- Heavily edited AI content may appear human-written.
- Results are probabilistic rather than definitive proof.

---

## Signal 2: Stylometric Analysis

### What It Measures

The stylometric signal evaluates:

- Sentence-length variance
- Vocabulary diversity (type-token ratio)
- Overall structural consistency

### Why It Was Chosen

Stylometric analysis provides a measurable statistical signal that is independent of the language model.

### Limitations

- Poetry may appear AI-generated because of repetition.
- Academic writing may appear unusually structured.
- Very short submissions provide limited evidence.

---

# Confidence Scoring

Both signals generate scores between **0.0** and **1.0**.

The final confidence score is calculated using weighted averaging:

```text
confidence =
(0.4 * llm_score)
+
(0.25 * style_score)
+
(0.15 * repetition)
+
(0.20 * metadata_signal)
```

The language-model signal receives a larger weight because it evaluates broader semantic patterns, while stylometric analysis provides an independent structural cross-check.

---

## Classification Thresholds

| Confidence Score | Classification |
|------------------|----------------|
| 0.00-0.39 | Likely Human |
| 0.40-0.69 | Uncertain |
| 0.70-1.00 | Likely AI |

The intentionally large uncertainty range helps reduce false positives against human authors.

---

# Confidence Score Examples

## Example 1: Higher AI Confidence

### Text

> Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications.

### Result

```text
Attribution: Uncertain
Confidence: 0.56
LLM Score: 0.80
Stylometric Score: 0.20
```

Although the language-model signal strongly favored AI authorship, the stylometric signal disagreed, producing an uncertain classification.

---

## Example 2: Strong Human Classification

### Text

> ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after.

### Result

```text
Attribution: Likely Human
Confidence: 0.02
LLM Score: 0.00
Stylometric Score: 0.04
```

Both signals strongly suggested human authorship.

---

# Transparency Labels

## High-Confidence AI

```text
This content shows strong indicators of AI-generated writing.

Our system has high confidence in this assessment based on multiple detection signals.

This result is not proof of AI authorship. Creators may appeal this decision if they disagree.
```

## High-Confidence Human

```text
This content appears to be human-written.

Our system found strong indicators of human authorship across multiple detection signals.

This result is not proof of human authorship. Creators may appeal this decision if they disagree.
```

## Uncertain

```text
This content contains mixed signals.

Our system is not confident enough to classify the content as AI-generated or human-written.

Additional review may be necessary. Creators may appeal this result if they disagree.
```

---

# API Endpoints

## POST /submit

### Request

```json
{
  "text": "Sample content",
  "creator_id": "user123"
}
```

### Response

```json
{
  "content_id": "...",
  "attribution": "likely_human",
  "confidence": 0.21,
  "label": "...",
  "llm_score": 0.20,
  "stylometric_score": 0.50,
  "repetition_score": 0.00,
  "metadata_score": 0.00,
  "verified_creator": false,
  "certificate_id": null
}
```

---

## POST /appeal

### Request

```json
{
  "content_id": "uuid",
  "creator_reasoning": "I wrote this content myself."
}
```

### Response

```json
{
  "message": "Appeal received.",
  "status": "under_review"
}
```

---

## GET /log

### Response

```json
{
  "entries": [...]
}
```

Returns structured audit-log entries.

---

# Appeals Workflow

When an appeal is submitted, the system:

1. Locates the original content record.
2. Stores the creator's reasoning.
3. Updates the status to `under_review`.
4. Creates an audit-log entry.
5. Returns a confirmation response.

This workflow provides a mechanism for challenging potential false positives.

---

# Rate Limiting

## Limits

```text
10 requests per minute
100 requests per day
```

## Reasoning

A typical creator submits only a small number of drafts during a writing session. These limits help discourage abuse while allowing normal usage.

## Verification

Rate limiting was verified using Flask-Limiter.

For testing purposes, a temporary limit of **2 requests per minute** was applied.

### Test Output

```text
200
200
429
429
429
```

The first two requests succeeded and subsequent requests returned **HTTP 429 (Too Many Requests)**, confirming enforcement of request limits.

The application was then restored to:

```text
10 requests per minute
100 requests per day
```

---

# Audit Log Samples

## Classification Entry

```json
{
  "content_id": "7bdc2021-fb54-40a3-aad2-52fe1950df33",
  "attribution": "uncertain",
  "confidence": 0.56,
  "llm_score": 0.80,
  "stylometric_score": 0.20,
  "timestamp": "2026-10-05T03:05:30.915841",
  "status": "classified"
}
```

## Human Classification Entry

```json
{
  "content_id": "65504d18-03f0-44ec-894f-25d030d5466b",
  "attribution": "likely_human",
  "confidence": 0.02,
  "llm_score": 0.00,
  "stylometric_score": 0.04,
  "timestamp": "2026-10-05T03:06:17.908908",
  "status": "classified"
}
```

## Appeal Entry

```json
{
  "content_id": "4b7a2035-70fe-4b37-a4df-89d424acd59a",
  "status": "under_review",
  "appeal_reasoning": "I wrote this content myself from personal experience.",
  "timestamp": "2026-10-05T03:38:42.954411"
}
```

---

# Known Limitations

## Poetry

Poetry frequently contains repetition and unusual structure that may resemble AI-generated writing.

## Academic Writing

Academic writing often follows highly structured conventions that can elevate AI-likelihood scores.

## Heavily Edited AI Content

Substantially revised AI-generated text may not retain identifiable AI patterns.

## Short Submissions

Very short text samples provide insufficient evidence for reliable stylometric analysis.

## In-Memory Appeal Storage

Appeal records are stored in memory while the application is running. Restarting the application clears the in-memory content store. A production system would use persistent database storage.

---

# Spec Reflection

## How the Planning Phase Helped

Creating the planning document before implementation made it easier to connect requirements to concrete functionality. The architecture diagrams provided a roadmap for content submission, confidence scoring, label generation, appeal handling, and audit logging.

Defining confidence thresholds early also simplified implementation of transparency labels and attribution decisions.

## Where the Implementation Changed

The original plan referenced a Groq-hosted Llama model. During implementation, GPT-OSS-20B was used instead due to model availability. The overall architecture remained unchanged.

The planning document also described several candidate stylometric metrics. The final implementation focused on sentence-length variance and vocabulary diversity to keep the system concise while maintaining a genuinely independent second signal.

## What I Learned

This project demonstrated how difficult authorship attribution can be. Multiple imperfect signals combined with explicit uncertainty proved more realistic than relying on a single binary detector.

---

# AI Usage

## AI Usage

AI tools were used as implementation and documentation assistants throughout development. All generated content was reviewed, tested, and modified before being incorporated into the final project.

## Example 1: Flask Endpoint Generation

### Prompt and Goal

I used AI assistance to generate an initial Flask application skeleton for the project.

I provided the project requirements and asked the AI to create:

- A `POST /submit` endpoint
- A `POST /appeal` endpoint
- A `GET /log` endpoint
- JSON request and response formats
- Basic audit logging functionality

### Prompt
 
```text
Create a Flask application for a content attribution system.
 
Requirements:
- POST /submit endpoint
- POST /appeal endpoint
- GET /log endpoint
- JSON request and response formats
- Audit logging support
- UUID-based content identifiers
 
Return starter code for app.py.
```

### AI Output

The AI generated:

- Route definitions
- Input validation examples
- JSON response structures
- Helper functions for audit logging

### What I Changed

I modified the generated code by:

- Replacing placeholder attribution logic with a weighted confidence-scoring system
- Integrating GPT-OSS-20B through Groq
- Adding UUID-based content identifiers
- Updating audit-log fields to match the project specification
- Implementing transparency labels tied to confidence thresholds

### Validation

I tested each endpoint using PowerShell requests and verified:

- Successful content submission
- Proper JSON responses
- Audit-log creation
- Appeal processing
- Correct confidence-score reporting

---

## Example 2: Stylometric Analysis Design

### Prompt and Goal

I used AI assistance to explore possible stylometric signals that could serve as an independent detection method alongside the language-model classifier.

I asked for statistical characteristics that could help distinguish between different writing styles.

### Prompt
 
```text
Suggest simple stylometric features for estimating whether text is AI-generated.

Requirements:
- Easy to implement in Python
- Produce a score between 0 and 1
- Work as an independent signal alongside an LLM classifier

For each feature, explain what it measures and its limitations.
```

### AI Output

The AI suggested multiple approaches, including:

- Sentence-length variance
- Vocabulary diversity (type-token ratio)
- Punctuation-density analysis
- Structural consistency measures

### What I Changed

I chose to implement:

- Sentence-length variance
- Vocabulary diversity (type-token ratio)

I intentionally did not implement punctuation-density analysis because I wanted to keep the detector simple and easier to validate within the scope of the project.

I also modified the confidence-scoring approach by assigning:

```text
60% weight to the LLM signal
40% weight to the stylometric signal
```

---


# AI Tool Plan

## Milestone 3: Submission Endpoint and LLM Signal

### Planning Inputs Used

- Detection Signals
- Architecture Narrative
- API Surface

### AI-Assisted Tasks

- Generated the initial Flask application structure.
- Created the `/submit` endpoint.
- Integrated Groq API calls.
- Designed UUID-based content IDs.
- Generated the audit-log helper function.
- Created request and response schemas.

### Verification Performed

- Verified Flask startup.
- Tested `/submit`.
- Confirmed content ID generation.
- Confirmed Groq responses.
- Verified audit-log creation.
- Tested `/log`.

---

## Milestone 4: Stylometric Analysis and Confidence Scoring

### Planning Inputs Used

- Detection Signals
- Confidence Scoring
- Uncertainty Representation

### AI-Assisted Tasks

- Designed the stylometric scoring function.
- Implemented sentence-length variance analysis.
- Implemented type-token ratio analysis.
- Generated confidence-scoring logic.
- Implemented attribution thresholds.

### Verification Performed

Four categories of text were tested:

1. Clearly AI-style text
2. Clearly human-written text
3. Borderline academic writing
4. Borderline conversational writing

Observed Results:

```text
AI Sample:
Confidence = 0.56
Attribution = Uncertain
```

```text
Human Sample:
Confidence = 0.02
Attribution = Likely Human
```

These tests verified that scores varied across different writing styles.

---

## Milestone 5: Transparency, Appeals, and Rate Limiting

### Planning Inputs Used

- Transparency Labels
- Appeals Workflow
- Rate Limiting Plan
- Audit Log Design

### AI-Assisted Tasks

- Generated the transparency-label function.
- Implemented all three transparency labels.
- Created the `/appeal` endpoint.
- Implemented appeal status updates.
- Added appeal logging.
- Integrated Flask-Limiter.
- Configured submission limits.

### Verification Performed

- Verified appeal responses.
- Verified audit-log updates.
- Verified storage of creator reasoning.
- Tested rate limiting.

Observed Rate-Limit Output:

```text
200
200
429
429
429
```

which confirmed HTTP 429 enforcement.

---

# Stretch Feature: Analytics Dashboard

To provide greater transparency into system behavior, I implemented an analytics dashboard endpoint.

## Endpoint

```http
GET /stats
```

## Example Response

```json
{
  "total_submissions": 52,
  "likely_human": 46,
  "uncertain": 6,
  "likely_ai": 0,
  "appeals": 1,
  "appeal_rate": 1.92,
  "average_confidence": 0.30
}
```

## Metrics

The dashboard reports:

- Total submissions
- Number of likely-human classifications
- Number of uncertain classifications
- Number of likely-AI classifications
- Total appeals
- Appeal rate
- Average confidence score

## How It Works

The endpoint reads data from the audit log and calculates aggregate statistics.

This provides reviewers and administrators with a high-level view of:

- Classification patterns
- User appeal activity
- Confidence trends
- Overall system usage

The analytics dashboard extends the transparency goals of the project by exposing system-level behavior in addition to individual classification decisions.

# Stretch Feature: Ensemble Detection

The original implementation used two independent detection signals:

1. LLM-based classification
2. Stylometric analysis

To improve robustness, a third signal was added:

3. Repetition analysis

## Repetition Analysis

This signal measures repeated vocabulary within a submission.

AI-generated content often exhibits more repeated words and phrases than naturally occurring human writing.

Example:

```text
Human-written sample:
repetition_score = 0.00
```

```text
Repetitive sample:
repetition_score = 1.00
```

## Ensemble Weighting

The final confidence score is calculated using:

```text
confidence =
(0.5 × llm_score)
+
(0.3 × stylometric_score)
+
(0.2 × repetition_score)
```

This approach reduces reliance on any individual detector and creates a three-signal ensemble attribution system.

# Stretch Feature: Provenance Certificate

To extend provenance tracking beyond content attribution, I implemented a Verified Human Creator credential.

## Endpoint

```http
POST /verify
```

### Example Request

```json
{
  "creator_id": "test-user"
}
```

### Example Response

```json
{
  "creator_id": "test-user",
  "verified_human": true,
  "certificate_id": "VH-001"
}
```

---

## Verified Content Example

After verification, creator provenance information is attached to content submissions.

Example:

```json
{
  "content_id": "c3d6bd05-6764-4a53-b0dd-1a8f732d27a2",
  "verified_creator": true,
  "certificate_id": "VH-001",
  "attribution": "likely_human",
  "confidence": 0.30
}
```

---

## How It Works

The system stores verified creators and assigns a unique certificate identifier.

When a verified creator submits content:

- the attribution pipeline still runs normally
- confidence scoring still applies
- the creator's provenance credential is displayed alongside the result

The credential does not override attribution decisions. Instead, it provides additional provenance information about the creator.

---

## Validation

The feature was tested by:

1. Verifying a creator through `POST /verify`.
2. Submitting content under that creator ID.
3. Confirming that:
   - `verified_creator` returned `true`
   - a certificate ID was displayed
   - attribution scoring continued to operate normally

# Stretch Feature: Multi-Modal Support

The original system analyzed only text submissions.

To expand provenance analysis beyond text, I extended the system to support creator-provided metadata alongside textual content.

## Supported Modalities

1. Text content
2. Structured metadata

### Example Request

```json
{
  "text": "This article discusses the role of AI in modern education.",
  "creator_id": "test-user",
  "metadata": {
    "title": "AI in Education",
    "category": "Education",
    "tags": ["ai", "teaching", "technology"]
  }
}
```

---

## Metadata Analysis

The metadata signal evaluates:

- Title completeness
- Metadata availability
- Tag information

The metadata signal produces a score between:

```text
0.0 = More complete metadata
1.0 = Less complete metadata
```

### Example Outputs

#### Complete Metadata

```text
metadata_score = 0.0
```

#### Weak Metadata

```text
metadata_score = 0.4
```

#### No Metadata

```text
metadata_score = 0.5
```

---

## Confidence Scoring

The metadata signal is incorporated into the ensemble detector alongside:

1. LLM-based classification
2. Stylometric analysis
3. Repetition analysis

This allows the final confidence score to reflect information from multiple content modalities rather than relying only on text.

---

## Validation

The feature was validated using:

- Complete metadata submissions
- Incomplete metadata submissions
- Submissions without metadata

The resulting metadata scores varied as expected and were successfully recorded in the audit log.

# Demo Video

**Video Link:** https://www.youtube.com/watch?v=DItw1D5fpdo

