# Ground-truth labels

`label.json` contains one independently assessed record for every brand/creator
pair in `data/brands.json` × `data/creators.json`. Labels are based on the
brief and profile fields only; ChromaDB and retrieval rank are not inputs.

## Rubric

- **Good:** A realistic campaign candidate. The creator has a direct required
  niche/content fit, reaches a relevant audience and geography, can deliver on
  the needed channel/format, and has no disqualifying hard-constraint conflict.
  One minor soft mismatch does not disqualify an otherwise strong candidate.
- **Maybe:** There is a credible product or content connection, but a concrete
  shortfall makes the creator a secondary candidate. Examples include a
  partial niche fit, weak audience overlap, a soft geography mismatch, no
  preferred platform, a materially imperfect size, or a budget that cannot be
  confirmed from the provided data.
- **Poor:** The campaign has little natural connection to the creator, or a
  material hard requirement is unmet. Multiple major gaps also qualify even
  when one aspect is relevant.

## Applying the criteria consistently

- **Hard constraints:** Treat a niche named in `required_creator_niches` as
  required, while reading `mandatory_requirements` to clarify its meaning
  (including explicit `or`/`and` wording). Mandatory geography, platform,
  language, audience-gender, content-format, and campaign-experience statements
  are hard constraints when the profile has enough information to assess them.
  A clear failure of a hard requirement normally means poor. Do not infer
  failure from a missing profile field; record that dimension as unknown and
  weigh the remaining evidence.
- **Soft constraints:** `preferred_creator_niches`, `preferred_traits`, target
  geography where it is not mandatory, preferred platform overlap, audience
  details not stated as mandatory, and creator-size preference are soft. A
  single soft mismatch normally lowers a strong fit to maybe at most; it does
  not by itself make a creator poor.
- **Niche:** Compare primary and secondary niches, bio, content types, interests,
  and past brand categories with the required/preferred niches and the actual
  product use. A direct required-niche match is strong; an adjacent creator
  with a credible product connection is partial; unrelated content is poor.
- **Audience:** Compare age ranges by overlap, gender distribution against the
  requested audience, and listed audience locations. Strong age and demographic
  overlap is strong. Partial overlap or a mixed demographic is partial. A
  clearly opposing required demographic is poor. Do not assume creator gender
  from a name. Creator gender is not a field in these profiles, so a mandatory
  creator-gender condition remains unknown and cannot qualify as a good match.
  Use explicit profile content and stated campaign fit only.
- **Geography:** Compare the creator's base location to explicit mandatory
  regions first. Then compare the listed audience locations to target markets.
  A mandatory location failure is poor; a target-market audience without local
  creator base can still be good or maybe depending on the rest of the brief.
  If geography is not mandatory, treat it as a soft factor.
- **Platform and format:** Compare profile platforms to the brief's platforms.
  An explicit mandatory platform or video requirement is hard. For a list of
  brief platforms without mandatory wording, overlap is positive evidence but
  absence is a soft gap. Do not equate a blog with video content.
- **Budget:** Compare a rate card to a ceiling only when both use the same
  currency and the profile gives a usable rate range. If the highest listed
  price exceeds the ceiling, record a budget mismatch; a cheaper option may
  exist, but the profile does not tie prices to deliverables. A range within
  the ceiling fits. All supplied creator rate cards are in INR, but
  most brand budgets use another currency and the data has no exchange-rate
  convention or rate-card unit. For those pairs budget fit is `unknown`; do not
  convert or infer a mismatch from the raw numbers. Budget alone should not
  decide a label unless a same-currency hard ceiling is explicit.
- **Creator size:** Compare follower count with the brand's minimum/maximum and
  stated tier. Within range fits. A modest miss is a soft shortfall; an extreme
  miss may make a candidate poor if the campaign also has other gaps.
- **Campaign fit:** Assess whether the creator's described content and past
  partnerships make a credible way to show the specific product and campaign
  goal. This is a synthesis of profile evidence, not retrieval similarity.

The `reasoning` values describe each dimension (`strong`, `partial`, `weak`,
`unknown`; budget uses `fit`, `mismatch`, `uncertain`, or `unknown`; size uses
`fit`, `near`, `outside`, or `unknown`). Each `reason` states the main evidence
and any material shortfall. These labels are a curated benchmark for the
provided synthetic profiles, not a claim about real-world creator performance.

## Validation

Run from the repository root:

```bash
python evals/validate_labels.py
```

The validator checks IDs, pair uniqueness and complete Cartesian coverage,
allowed labels, required reasoning fields, and total count.
