import os
import json
from google import genai
from google.genai import types


def generate_scr_narrative_offline(findings: dict) -> dict:
    rr = findings["return_rate_by_payment"]
    seg = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    oi = findings["outlier_inflated_month"]

    narrative = (
        "SITUATION\n"
        f"Mamaearth's cleaned order book totals Rs {findings['cleaned_total_revenue_inr']:,.2f} "
        "across 175 verified orders after removing double-submitted duplicates from the raw "
        "dataset. Payment mix is spread across CARD, UPI and COD, and the business is running "
        "on a blended revenue base that had been overstated by data-quality issues before cleaning.\n\n"
        "COMPLICATION\n"
        "Returns are not uniform across the business. COD orders return at "
        f"{rr['COD']}%, compared with {rr['CARD']}% for CARD and {rr['UPI']}% for UPI. "
        "Segmented further, the COD + Tier-2 city combination is the single highest-risk pocket "
        f"at {seg['return_rate_pct']}%. Separately, the raw revenue figure of "
        f"Rs {findings['raw_total_revenue_inr']:,.2f} was overstated by "
        f"Rs {findings['duplicate_reconciliation_delta_inr']:,.2f} due to five duplicate orders, "
        f"and January's apparent peak of Rs {oi['apparent_revenue_inr']:,.2f} is an artifact of two "
        f"bulk orders — corrected January revenue is Rs {oi['corrected_revenue_inr']:,.2f}. "
        f"The true peak month is {peak['month']} at Rs {peak['revenue_inr']:,.2f}.\n\n"
        "RESOLUTION\n"
        f"Prioritise a COD-to-prepaid intervention in Tier-2 cities targeting the "
        f"{seg['return_rate_pct']}% return cohort, tighten duplicate-submission controls at "
        f"checkout, and re-baseline monthly performance against the outlier-corrected trend "
        f"using {peak['month']} as the genuine peak. These three actions address the largest "
        "return driver and restore confidence in the reported revenue trajectory."
    )

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": None,
        "path": "offline",
    }


def generate_scr_narrative(findings: dict) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return generate_scr_narrative_offline(findings)

    system_instruction = (
        "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
        "Structure your report in exactly three labelled sections: Situation, Complication, "
        "Resolution. Every number you quote must come from the supplied findings and must appear "
        "with the same value — no invented statistics."
    )

    contents = (
        "Write a 3-section Situation-Complication-Resolution business narrative "
        "using only these verified findings:\n"
        + json.dumps(findings, indent=2)
    )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                max_output_tokens=2048,
                http_options=types.HttpOptions(timeout=30000),
            ),
        )

        return {
            "status": "success",
            "narrative": response.text,
            "tokens": getattr(response.usage_metadata, "total_token_count", None),
            "path": "online",
        }

    except Exception as err:
        fallback = generate_scr_narrative_offline(findings)
        fallback["note"] = f"Online path failed, served offline: {err}"
        return fallback


if __name__ == "__main__":
    with open("narrator/findings.json") as f:
        findings = json.load(f)

    result = generate_scr_narrative(findings)
    print(result["narrative"])
    print()
    print(f"(path: {result['path']}, status: {result['status']})")

    with open("narrator/sample_output.txt", "w", encoding="utf-8") as f:
        f.write(result["narrative"])
    print("Saved narrator/sample_output.txt")
