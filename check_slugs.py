import requests

import requests

CANDIDATES = [
    # India product / SaaS / fintech (small-mid)
    "razorpaysoftwareprivatelimited", "razorpay", "postman", "cred", "meesho", "zeta",
    "groww", "browserstack", "clevertap", "chargebee", "hasura", "zeotap", "atlan",
    "mindtickle", "whatfix", "spotdraft", "leadsquared", "darwinbox", "innovaccer",
    "gupshup", "yellowai", "uniphore", "capillary", "coindcx", "coinswitch", "slice",
    "jar", "fampay", "navi", "lendingkart", "perfios", "pocketfm", "sharechat",
    "swiggy", "nykaa", "lenskart", "urbancompany", "cars24", "spinny", "rapido",
    "porter", "shadowfax", "delhivery", "upgrad", "scaler", "sarvam", "krutrim",
    # Global, remote-friendly, small-mid
    "mixpanel", "amplitude", "gleanwork", "supabase", "vercel", "posthog", "sentry",
    "airbyte", "temporal", "appsmith", "deel", "remote", "toptal", "turing", "andela",
    "gitlab", "automattic", "zapier", "doist", "hotjar", "jumpcloud", "retool",
    # Bade names (rakho, par sirf ek hissa)
    "databricks", "mongodb", "elastic", "cloudflare", "twilio", "rubrik", "okta",
]

def greenhouse(s):
    r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs", timeout=15)
    if r.status_code != 200: return None
    return [j.get("location", {}).get("name", "") for j in r.json().get("jobs", [])]

def lever(s):
    r = requests.get(f"https://api.lever.co/v0/postings/{s}?mode=json", timeout=15)
    if r.status_code != 200: return None
    return [(j.get("categories") or {}).get("location", "") or "" for j in r.json()]

def ashby(s):
    r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{s}", timeout=15)
    if r.status_code != 200: return None
    return [j.get("location", "") or "" for j in r.json().get("jobs", [])]

KEYS = ("india", "bangalore", "bengaluru", "hyderabad", "pune", "noida", "gurgaon", "gurugram", "delhi", "remote")

for s in CANDIDATES:
    for ats, fn in (("greenhouse", greenhouse), ("lever", lever), ("ashby", ashby)):
        try:
            locs = fn(s)
        except Exception:
            locs = None
        if locs:
            n = sum(any(k in l.lower() for k in KEYS) for l in locs)
            print(f"{ats:11} {s:35} total={len(locs):4} india_or_remote={n}")

def greenhouse(s):
    r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs", timeout=15)
    if r.status_code != 200: return None
    return [j.get("location", {}).get("name", "") for j in r.json().get("jobs", [])]

def lever(s):
    r = requests.get(f"https://api.lever.co/v0/postings/{s}?mode=json", timeout=15)
    if r.status_code != 200: return None
    return [(j.get("categories") or {}).get("location", "") or "" for j in r.json()]

def ashby(s):
    r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{s}", timeout=15)
    if r.status_code != 200: return None
    return [j.get("location", "") or "" for j in r.json().get("jobs", [])]

KEYS = ("india", "bangalore", "bengaluru", "hyderabad", "pune", "noida", "gurgaon", "gurugram", "delhi", "remote")

for s in CANDIDATES:
    for ats, fn in (("greenhouse", greenhouse), ("lever", lever), ("ashby", ashby)):
        try:
            locs = fn(s)
        except Exception:
            locs = None
        if locs:
            n = sum(any(k in l.lower() for k in KEYS) for l in locs)
            print(f"{ats:11} {s:35} total={len(locs):4} india_or_remote={n}")