import openai, requests, json, os, time, re
import os
from datetime import datetime

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
SUPERTEAM_KEY = os.environ.get("SUPERTEAM_API_KEY", "")

client = openai.OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")


def get_listings(min_subs=0, max_subs=999, agent_only=True):
    r = requests.get("https://earn.superteam.fun/api/listings",
        headers={"Authorization": f"Bearer {SUPERTEAM_KEY}"}, timeout=15)
    data = r.json()
    results = []
    for l in data:
        subs = l.get("_count", {}).get("Submission", 999)
        aa = l.get("agentAccess", "HUMAN_ONLY")
        reward = l.get("rewardAmount", "?")
        token = l.get("token", "USDC")
        if agent_only and aa != "AGENT_ALLOWED":
            continue
        if subs < min_subs or subs > max_subs:
            continue
        results.append({
            "slug": l["slug"],
            "title": l.get("title", ""),
            "reward": reward,
            "token": token,
            "submissions": subs,
            "deadline": l.get("deadline", "")[:10],
            "agent_access": aa,
            "url": f"https://earn.superteam.fun/listings/{l['slug']}"
        })
    return sorted(results, key=lambda x: x["submissions"])


def get_bounty_detail(slug):
    r = requests.get(f"https://earn.superteam.fun/api/listings/{slug}",
        headers={"Authorization": f"Bearer {SUPERTEAM_KEY}"}, timeout=15)
    if r.status_code == 200:
        return r.json()
    return None


def generate_submission(prompt, bounty_context, model="google/gemma-4-31b-it:free", max_tokens=1500):
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional content creator. Generate high-quality bounty submissions."},
                {"role": "user", "content": f"Bounty context:\n{bounty_context}\n\nGenerate: {prompt}"}
            ],
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"


def try_submit(slug, content, method="direct"):
    headers = {"Authorization": f"Bearer {SUPERTEAM_KEY}"}
    if method == "direct":
        r = requests.post(
            f"https://superteam.fun/earn/listing/{slug}/",
            json={"text": content},
            headers=headers | {"Content-Type": "application/json"},
            timeout=15
        )
        return f"HTTP {r.status_code}", r.text[:200]
    elif method == "rsc":
        r = requests.post(
            f"https://superteam.fun/earn/listing/{slug}/",
            headers=headers | {"Accept": "text/x-component", "Next-Action": ""},
            data=json.dumps(["submissionText", content]),
            timeout=15
        )
        return f"RSC HTTP {r.status_code}", r.text[:200]
    return "Unknown method", ""


def track_bounty(slug, status="pending", submission_file=None):
    log_file = "bounty_tracker.json"
    try:
        with open(log_file) as f:
            tracker = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        tracker = {}
    tracker[slug] = {
        "status": status,
        "submission_file": submission_file,
        "updated": datetime.now().isoformat()
    }
    with open(log_file, "w") as f:
        json.dump(tracker, f, indent=2)


def scan_and_generate(model="google/gemma-4-31b-it:free", max_bounties=3):
    print("[bounty_hunter] Scanning for AGENT_ALLOWED bounties...")
    listings = get_listings(agent_only=True)
    print(f"[bounty_hunter] Found {len(listings)} AGENT_ALLOWED bounties")
    
    if not listings:
        print("[bounty_hunter] No AGENT_ALLOWED bounties with few submissions")
        return
    
    for bounty in listings[:max_bounties]:
        print(f"\n[bounty_hunter] Targeting: ${bounty['reward']} {bounty['token']} - {bounty['slug']}")
        print(f"[bounty_hunter] Submissions: {bounty['submissions']}, Deadline: {bounty['deadline']}")
        
        track_bounty(bounty['slug'], "in_progress")
        
        detail = get_bounty_detail(bounty['slug'])
        context = json.dumps(detail or bounty, indent=2)
        
        prompt = "Create a complete, high-quality submission for this bounty. Make it detailed and professional."
        content = generate_submission(prompt, context, model=model)
        
        if content.startswith("ERROR"):
            print(f"[bounty_hunter] Generation failed: {content}")
            track_bounty(bounty['slug'], "generation_failed")
            continue
        
        filename = f"submissions/{bounty['slug']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        os.makedirs("submissions", exist_ok=True)
        with open(filename, "w") as f:
            f.write(content)
        
        print(f"[bounty_hunter] Saved to {filename}")
        track_bounty(bounty['slug'], "submitted", filename)
        
        # attempt direct and RSC
        for method in ["direct", "rsc"]:
            status, resp = try_submit(bounty['slug'], content, method)
            print(f"[bounty_hunter] {method} submit: {status}")
            if "submitted" in resp.lower() or "success" in resp.lower():
                track_bounty(bounty['slug'], "submitted_online")
                break
        
        time.sleep(2)


if __name__ == "__main__":
    scan_and_generate()
