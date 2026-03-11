# Multimodal Image Passing Specification

## Purpose

This document specifies **how images must be processed and passed through the multimodal pipeline** in the WhatsApp Yearbook system.

The goal is to maximize:

* narrative quality
* reasoning clarity
* signal‑to‑noise ratio
* token efficiency

This document focuses **only on the image flow** and should be considered a **critical design specification** for the multimodal architecture.

---

# 1. Core Design Principle

Images should **not be passed directly in bulk to the reasoning model**.

Instead the pipeline must separate:

* visual perception
* narrative reasoning

Two different models handle these stages.

```text
Qwen2.5‑VL → visual perception
GPT‑OSS → narrative reasoning
```

---

# 2. Anti‑Pattern to Avoid

The most common multimodal mistake is:

```text
messages of the day
+ all images
+ all audio
↓
multimodal LLM
↓
summary
```

Problems created:

• excessive context usage
• noisy visual input
• irrelevant memes or screenshots
• duplicated images
• loss of connection between image and conversation moment
• degraded reasoning quality

Large reasoning models perform worse when raw visual data is mixed with narrative reasoning tasks.

---

# 3. Correct Multimodal Architecture

Images must go through **two separate stages**.

```text
raw images
↓
Qwen2.5‑VL (single‑image analysis)
↓
structured visual facts
↓
image ranking
↓
selected images
↓
GPT‑OSS reasoning
```

This architecture separates **perception** from **interpretation**.

---

# 4. Stage 1 — Single Image Analysis

Each image is analyzed **individually** by the vision model.

Reasons:

• avoids cross‑image contamination
• allows independent scoring
• improves caption accuracy
• improves OCR extraction

## Input

* image path
* basic metadata
* captioning prompt

## Output

Structured record.

Example:

```json
{
 "filename": "IMG-001.jpg",
 "caption": "photo of sushi dinner at a restaurant",
 "category": "food_restaurant",
 "contains_text": false,
 "narrative_relevance_score": 0.84
}
```

---

# 5. Information Extracted From Images

The vision prompt must extract at minimum:

• detailed caption
• short caption
• scene category
• presence of text
• screenshot detection
• meme detection
• estimated people count
• technical quality score
• narrative relevance score

This produces **structured visual facts**.

---

# 6. Stage 2 — Image Ranking

After analysis the system must reduce the images.

Goal:

Select **only the visually meaningful images of the day**.

### Recommended limits

| asset          | limit |
| -------------- | ----- |
| images per day | 4     |
| hero image     | 1     |

### Ranking formula example

```
score =
  narrative_relevance * 0.5
+ aesthetic_score * 0.2
+ event_proximity * 0.2
+ message_cluster_weight * 0.1
```

This reduces visual noise dramatically.

---

# 7. What the Reasoning Model Receives

The reasoning model (GPT‑OSS) **does not receive all images**.

Instead it receives distilled signals.

Example input:

```
TOP IMAGES

1. sushi dinner at restaurant
2. selfie together in the evening
3. screenshot of map planning meetup
```

The reasoning model works on **semantic visual signals**, not raw media.

---

# 8. When Raw Images May Be Passed

Raw images may be forwarded to GPT‑OSS only in special cases:

• the day contains very few images
• an image represents the central event
• complex screenshot requiring deeper interpretation

Even then the number should be limited.

Maximum recommended: **1‑2 images**.

---

# 9. Example Full Image Pipeline

```text
raw images
↓
Qwen2.5‑VL
↓
image captions + OCR + tags
↓
image ranking
↓
selected images
↓
GPT‑OSS reasoning
↓
daily narrative
↓
slide generation
```

---

# 10. Benefits of the Two‑Stage Design

| benefit                | explanation                               |
| ---------------------- | ----------------------------------------- |
| context reduction      | fewer tokens sent to reasoning model      |
| cleaner reasoning      | GPT‑OSS focuses on narrative signals      |
| better caption quality | vision model sees one image at a time     |
| better slide selection | ranking identifies most meaningful images |

---

# 11. Operational Rule

**Vision models should see the images.**

**Reasoning models should interpret the extracted facts.**

Keeping this separation is essential for reliable multimodal pipelines.

---

# 12. Impact on Slide Generation

The final selected images should be used for:

• slide collage
• hero image of the day
• narrative visual support

Images not selected should **not appear in the final deck**.

---

# 13. Final Architectural Rule

The system must enforce this invariant:

```text
visual perception ≠ narrative reasoning
```

This separation ensures scalable multimodal reasoning and consistent output quality.
