"""Typed Laya decision questions for creator-brand matching."""
from __future__ import annotations

QUESTIONS: dict[str, dict] = {
    "niche_fit": {
        "type": "choice",
        "instructions": "How well does this creator's content niche fit the brand's required and preferred creator niches?",
        "criteria": {
            "strong": "The creator directly matches one or more required niches and is clearly relevant to the campaign.",
            "partial": "The creator has meaningful adjacent relevance but does not strongly satisfy the required niche.",
            "none": "The creator's niche is unrelated to the brand or campaign.",
        },
    },
    "audience_fit": {
        "type": "choice",
        "instructions": "How well does the creator's audience match the brand's target audience?",
        "criteria": {
            "strong": "Audience demographics, interests, and/or locations strongly match the target audience.",
            "partial": "There is meaningful overlap but also important uncertainty or mismatch.",
            "none": "The creator's audience is clearly different from the target audience.",
        },
    },
    "geography_fit": {
        "type": "choice",
        "instructions": "How well does the creator satisfy the brand's geographic requirements?",
        "criteria": {
            "strong": "Creator location and/or audience location clearly satisfies the target geography.",
            "partial": "There is some geographic relevance but the requirement is not fully satisfied.",
            "none": "The creator is clearly outside the required geography and has no meaningful audience match there.",
        },
    },
    "platform_fit": {
        "type": "choice",
        "instructions": "How well does the creator satisfy the brand's required platforms and content formats?",
        "criteria": {
            "strong": "The creator actively uses the required platform(s) and can produce the requested content.",
            "partial": "There is some platform/content compatibility but not a complete match.",
            "none": "The creator does not use the required platform(s) or cannot reasonably produce the requested format.",
        },
    },
    "budget_fit": {
        "type": "choice",
        "instructions": "How well does the creator's rate card fit the campaign budget?",
        "criteria": {
            "strong": "The creator's pricing clearly fits within the campaign budget.",
            "partial": "Pricing is uncertain, partially compatible, or cannot be directly compared because currencies/requirements are unclear.",
            "none": "The creator's pricing clearly exceeds the campaign budget.",
        },
    },
    "creator_size_fit": {
        "type": "choice",
        "instructions": "How well does the creator's follower size and reach fit the campaign's creator-size requirements?",
        "criteria": {
            "strong": "Creator size clearly falls within the preferred or required range.",
            "partial": "Creator size is somewhat outside the preferred range but may still be usable.",
            "none": "Creator size clearly violates a mandatory creator-size requirement.",
        },
    },
    "campaign_fit": {
        "type": "choice",
        "instructions": "Considering the campaign goal, product, content style, creator interests, and previous brand categories, how suitable is this creator for the campaign?",
        "criteria": {
            "strong": "The creator is clearly suitable for the campaign and can naturally promote the product.",
            "partial": "The creator has meaningful potential but there are uncertainties or weaker alignment.",
            "none": "The creator is clearly unsuitable for the campaign.",
        },
    },
    "final_decision": {
        "type": "choice",
        "instructions": "Should this creator remain in the brand's candidate feed? Consider hard constraints separately from soft preferences.",
        "criteria": {
            "KEEP": "The creator is a strong realistic candidate. The creator satisfies important campaign requirements and has no clear hard-constraint failure.",
            "UNCERTAIN": "The creator has meaningful relevance but one or more important factors are uncertain, partially matched, or require deeper reasoning.",
            "DROP": "The creator has a clear mismatch or hard-constraint failure that makes them unsuitable for this campaign.",
        },
    },
}

__all__ = ["QUESTIONS"]
