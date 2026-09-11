import re, yaml
md = open("docs/research/bottlenecks.md").read()
BUCKET = {  # which diffusion stock the section's barriers act on
    "Stage 1: Methods → products (the model-to-product gap)": "products",
    "Stage 2: Product → individual adoption": "early_adoption",
    "Stage 3: Organizational and structural adaptation": "adaptation",
    "Regulatory, legal, and institutional limits": "adaptation",
    "External-world and physical speed limits": "adaptation",
    "Safety speed limits (deliberate brakes)": "adaptation",
    "Market and economic limits": "adaptation",
    "Science-specific bottlenecks": "adaptation",
    "Upstream: why AI cannot simply accelerate its own diffusion": "return_arrow",
}
LINKS = {  # bottleneck number -> indicators the tracker uses to watch it (titles checked against the list)
    1: ["enterprise_pilot_to_production"], 2: ["enterprise_pilot_to_production", "dev_rct_uplift"],
    3: ["horizon_ratio_80_50", "metr_horizon_80"], 4: ["rsi_intervention_rate_4_8h", "horizon_ratio_80_50"],
    7: ["enterprise_pilot_to_production"], 9: ["model_price_per_horizon_hour"],
    16: ["dev_rct_uplift", "horizon_ratio_80_50"], 17: ["dev_rct_uplift"],
    18: ["bbd_work_hours_assisted", "btos_firm_use"], 19: ["bbd_work_hours_assisted", "aei_augmentation_share"],
    20: ["bbd_work_hours_assisted"], 21: ["btos_firm_use", "ramp_paid_ai_adoption"], 23: ["rsi_intervention_rate_4_8h"],
    28: ["btos_firm_use", "bbd_work_hours_assisted"], 29: ["enterprise_pilot_to_production", "dev_rct_uplift"],
    35: ["rsi_intervention_rate_4_8h", "dev_rct_uplift"], 37: ["bls_tfp_private_nonfarm"], 38: ["btos_firm_use"],
    41: ["canaries_entry_level_gap", "new_grad_unemployment"], 42: ["bls_labor_productivity_yoy"],
    61: ["circular_financing_scale", "cloud_rpo_backlog"], 65: ["rsi_intervention_rate_4_8h", "horizon_ratio_80_50"],
    70: ["model_price_per_horizon_hour", "consumer_surplus_wta"], 71: ["model_price_per_horizon_hour", "lab_hhi", "margin_stack_semis_share"],
    74: ["bls_tfp_private_nonfarm", "bls_labor_productivity_yoy"], 75: ["lab_recoupment_ratio", "saas_multiples", "enterprise_spend_by_layer"],
    86: ["rsi_agent_workdays_per_human", "rsi_intervention_rate_4_8h"],
}
items, section, sections = [], None, []
for line in md.splitlines():
    if line.startswith("## "):
        section = line[3:].strip()
        if section in BUCKET:
            sections.append({"name": section, "bucket_id": BUCKET[section]})
        continue
    m = re.match(r"^(\d+)\. \*\*(.+?)\*\* (.+?) \[([A-Za-z0-9, ]+)\]\s*$", line)
    if m and section in BUCKET:
        n = int(m.group(1))
        items.append({"id": n, "title": m.group(2).rstrip("."), "text": m.group(3).strip(), "section": section,
                      "bucket_id": BUCKET[section], "source_codes": [c.strip() for c in m.group(4).split(",")],
                      "related_indicators": LINKS.get(n, [])})
essays = []
for row in re.findall(r"^\| (\w+) \| \[(.+?)\]\((.+?)\) \| (\d{4}-\d{2}-\d{2}) \|$", md, re.M):
    essays.append({"code": row[0], "title": row[1], "url": row[2], "date": row[3]})
# Domain (the grid's second axis): the raw extraction tags each of its 224 rows with a domain but has no mechanism field.
# An item takes the domain of the raw row that best matches its words; with no close match, the most common domain
# among the raw rows of the essays it cites. The basis is kept so the fallbacks can be reviewed.
import collections, difflib, json
raw = json.load(open("docs/research/bottlenecks_raw.json"))
words = lambda t: set(re.findall(r"[a-z]{4,}", t.lower()))  # noqa: E731
slug = {e["code"]: e["url"].rstrip("/").split("/")[-1] for e in essays}
for it in items:
    mine = words(it["title"] + " " + it["text"])
    def score(r):  # (title similarity, word overlap)
        other = words(r["name"] + " " + r["description"])
        return difflib.SequenceMatcher(None, it["title"].lower(), r["name"].lower()).ratio(), len(mine & other) / max(1, len(mine | other))
    best = max(raw, key=lambda r: max(score(r)[0], 2 * score(r)[1]))
    if score(best)[0] >= 0.5 or score(best)[1] >= 1 / 3:  # a close title or a third of the words shared
        it["domain"], it["domain_basis"] = best["domain"], f"matched extraction row: {best['name']}"
    else:
        doms = collections.Counter(r["domain"] for r in raw if r["slug"] in {slug.get(c) for c in it["source_codes"]})
        it["domain"], it["domain_basis"] = (doms.most_common(1)[0][0] if doms else "general"), "most common domain of its essays"
assert [i["id"] for i in items] == list(range(1, 90)), [i["id"] for i in items][:5]
codes = {e["code"] for e in essays}
bad = {c for i in items for c in i["source_codes"] if c not in codes}
assert not bad, bad
out = {"_generated_from": "docs/research/bottlenecks.md (Narayanan & Kapoor's 89 named bottlenecks, verified extraction); regenerate with the script in the commit that added this file. related_indicators are the tracker's hand-mapped links.",
       "sections": sections, "essays": essays, "bottlenecks": items}
open("seed/bottlenecks.yaml", "w").write(yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=1000))
print(len(items), "bottlenecks;", len(essays), "essays;", len(sections), "sections;", sum(1 for i in items if i["related_indicators"]), "linked")
