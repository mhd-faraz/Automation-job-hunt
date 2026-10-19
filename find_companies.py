"""Find companies on Greenhouse / Lever / Ashby that have entry-level-looking
engineering jobs in India, and (optionally) add them to companies.yaml.

Usage (from the PWP_jobhunt folder, with the venv active):
    python3 find_companies.py            # test candidates, show a table
    python3 find_companies.py --apply    # ...and append the good ones to companies.yaml
"""
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import yaml

CANDIDATES = """
postman razorpaysoftwareprivatelimited groww slice cred meesho zeta atlan spotdraft
unacademy cashfree juspay inmobi pubmatic moengage druva thoughtspot icertis zenoti
zluri rocketlane sarvam gohighlevel lenskart phonepe kreditbee moneyview dream11
games24x7 mpl exotel netcore webengage smallcase upstox angelone kuvera jupiter
bharatpe mobikwik pinelabs openfinancial setu yubi finbox zeotap hevodata
stripe figma dropbox coinbase reddit airbnb okta datadog samsara pagerduty anthropic
notion mercury linear ramp vanta mixpanel amplitude heap segment twilio sendgrid plaid
chime robinhood kraken ripple chainalysis alchemy consensys cloudflare elastic hashicorp
newrelic netskope sumologic chronosphere grafanalabs cockroachlabs yugabyte couchbase
pubnub talkdesk medallia gong rippling deel gusto brex navan airtable asana miro
grammarly duolingo discord roblox scaleai openai databricks cohere langchain pinecone
weaviate qdrant chroma perplexityai writer harvey sierra decagon anysphere replit
retool netlify render railway planetscale neon supabase posthog sentry vercel
circleci launchdarkly sourcegraph tailscale clickhouse dbtlabs fivetran hubspot
zendesk outreach zoominfo apolloio clay chargebee recurly mongodb rubrik gitlab
glean gleanwork turing jumpcloud gushwork valgenesis klearnow gigaml razorpay
nutanix thoughtworks freshworks sprinklr browserstack clevertap hasura whatfix
mindtickle leadsquared darwinbox innovaccer gupshup yellowai uniphore capillary
coindcx coinswitch jar fampay navi lendingkart perfios pocketfm sharechat swiggy nykaa
urbancompany cars24 spinny rapido porter shadowfax delhivery upgrad scaler krutrim
toplyne highlevel dukaan bluecopa ola olaelectric ather licious zepto
paytm airtel jio walmartglobaltech target lowes expedia booking
mckinsey bcg oracle sap salesforce adobe vmware servicenow workday
""".split()

INDIA = ("india", "bangalore", "bengaluru", "hyderabad", "pune", "noida", "gurgaon",
         "gurugram", "delhi", "mumbai", "chennai", "chandigarh", "mohali", "kolkata",
         "ahmedabad", "jaipur", "indore", "kochi", "coimbatore")
TITLE_OK = re.compile(r"\b(software|backend|back-end|full[\s-]?stack|developer|engineer|sde|"
                      r"member of technical staff|ai|genai|ml)\b", re.I)
TITLE_BAD = re.compile(r"\b(senior|sr\.?|staff|principal|lead|manager|director|head|architect|"
                       r"vp|intern|internship|sales|marketing|recruit|support|success|"
                       r"designer|data scientist|ii|iii|iv|sde[\s-]?[234])\b", re.I)
UA = {"User-Agent": "jobhunt/1.0 (personal job search agent)"}


def get(url):
    for attempt in range(2):
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except Exception:
            time.sleep(2)
    return None


def greenhouse(slug):
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    return None if not d else [(j.get("title", ""), (j.get("location") or {}).get("name", "")) for j in d.get("jobs", [])]


def lever(slug):
    d = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    return None if not d else [(j.get("text", ""), (j.get("categories") or {}).get("location") or "") for j in d]


def ashby(slug):
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    return None if not d else [(j.get("title", ""), j.get("location") or "") for j in d.get("jobs", [])]


def check(slug):
    for ats, fn in (("greenhouse", greenhouse), ("lever", lever), ("ashby", ashby)):
        jobs = fn(slug)
        if jobs:
            india = [(t, l) for t, l in jobs if any(k in (l or "").lower() for k in INDIA)]
            rel = [t for t, l in india if TITLE_OK.search(t) and not TITLE_BAD.search(t)]
            return dict(ats=ats, slug=slug, total=len(jobs), india=len(india), relevant=len(rel))
    return None


def main():
    apply = "--apply" in sys.argv
    existing = set()
    try:
        cur = yaml.safe_load(open("companies.yaml")) or {}
        existing = {c["slug"] for c in cur.get("companies", [])}
    except Exception:
        pass

    slugs = [s for s in dict.fromkeys(CANDIDATES)]
    print(f"Testing {len(slugs)} candidates (takes a few minutes)...")
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = [r for r in ex.map(check, slugs) if r]

    results.sort(key=lambda r: (r["relevant"], r["india"]), reverse=True)
    print(f"\n{'ats':11} {'slug':32} total india relevant  (already in list?)")
    for r in results:
        mark = "yes" if r["slug"] in existing else ""
        print(f"{r['ats']:11} {r['slug']:32} {r['total']:5} {r['india']:5} {r['relevant']:8}  {mark}")

    good = [r for r in results if r["relevant"] >= 1 and r["slug"] not in existing]
    lines = [f"  - {{ats: {r['ats']}, slug: {r['slug']}, name: {r['slug'].title()}}}" for r in good]
    print(f"\n{len(good)} NEW companies with at least 1 relevant India job:\n")
    print("\n".join(lines))

    if apply and lines:
        shutil.copy("companies.yaml", "companies.yaml.bak")
        with open("companies.yaml", "a") as f:
            f.write("\n  # added by find_companies.py\n" + "\n".join(lines) + "\n")
        print(f"\nAppended {len(lines)} companies to companies.yaml (backup: companies.yaml.bak)")
    elif lines:
        print("\nTo add them automatically run:  python3 find_companies.py --apply")


if __name__ == "__main__":
    main()