def check_figures(narrative: str) -> bool:
    normalized = narrative.replace(",", "")
    checks = {
        "cleaned total 97358.30":  "97358.30" in normalized or "97358.3" in normalized,
        "COD return 44.4":         "44.4" in normalized,
        "COD+T2 segment 54.5":     "54.5" in normalized,
        "duplicate delta 2501.90": "2501.90" in normalized or "2501.9" in normalized,
        "March 20318.90":          ("March" in narrative or "2026-03" in narrative)
                                    and ("20318.90" in normalized or "20318.9" in normalized),
    }

    all_pass = True
    for label, ok in checks.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        all_pass = all_pass and ok

    return all_pass


if __name__ == "__main__":
    with open("narrator/sample_output.txt", encoding="utf-8") as f:
        narrative = f.read()

    print("Checking narrator/sample_output.txt...\n")
    result = check_figures(narrative)
    print()
    print("OVERALL:", "PASS" if result else "FAIL")