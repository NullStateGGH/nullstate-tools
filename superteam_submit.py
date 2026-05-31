import os
import requests, json, os, re, time
from datetime import datetime

ST_API_KEY = os.environ.get("SUPERTEAM_API_KEY", "")
AGENT_ID = "352cbaf7-db38-4a5f-8a85-9cbb7e11e5d7"
SUBMISSION_DIR = "submissions"


def direct_submit(slug, content):
    """Try direct POST to the listing endpoint."""
    r = requests.post(
        f"https://superteam.fun/earn/listing/{slug}/",
        json={"text": content, "listingId": ""},
        headers={
            "Authorization": f"Bearer {ST_API_KEY}",
            "X-Agent-ID": AGENT_ID,
            "Content-Type": "application/json",
        },
        timeout=15
    )
    return r.status_code, r.text[:500]


def rsc_submit(slug, content):
    """Try Next.js RSC POST."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/x-component",
        "Authorization": f"Bearer {ST_API_KEY}",
    })
    
    # First GET to establish cookies
    session.get(f"https://superteam.fun/earn/listing/{slug}/", timeout=15)
    
    # RSC action call
    r = session.post(
        f"https://superteam.fun/earn/listing/{slug}/",
        data=json.dumps([{
            "action": "submitBounty",
            "data": {"text": content, "listingId": ""}
        }]),
        timeout=15
    )
    return r.status_code, r.text[:500]


def next_action_submit(slug, content):
    """Try NextAction header pattern."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Authorization": f"Bearer {ST_API_KEY}",
    })
    
    # Get the page and extract Next-Action ID from the form
    r = session.get(f"https://superteam.fun/earn/listing/{slug}/", timeout=15)
    
    # Find all __NEXT_DATA__ or server action IDs
    actions = re.findall(r'action="([^"]+)"', r.text)
    action_ids = re.findall(r'[a-f0-9]{32,}', r.text)
    
    for action_id in action_ids[:5]:
        r2 = session.post(
            f"https://superteam.fun/earn/listing/{slug}/",
            headers={
                "Accept": "text/x-component",
                "Next-Action": action_id,
                "Content-Type": "text/plain;charset=UTF-8",
            },
            data=json.dumps([{"text": content}]),
            timeout=15
        )
        if r2.status_code == 200 and "error" not in r2.text[:200].lower():
            return r2.status_code, f"Action {action_id}: {r2.text[:300]}"
    
    return 0, "No valid action found"


def apiv2_submit(slug, content):
    """Try api/v2 endpoint."""
    r = requests.post(
        f"https://earn.superteam.fun/api/listings/{slug}/submit",
        json={"text": content},
        headers={
            "Authorization": f"Bearer {ST_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=15
    )
    return r.status_code, r.text[:500]


def graphql_submit(slug, content):
    """Try GraphQL mutation."""
    query = {
        "query": """
        mutation SubmitBounty($slug: String!, $text: String!) {
            submitBounty(slug: $slug, text: $text) {
                id
                submittedAt
            }
        }
        """,
        "variables": {"slug": slug, "text": content}
    }
    r = requests.post(
        "https://earn.superteam.fun/api/graphql",
        json=query,
        headers={
            "Authorization": f"Bearer {ST_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=15
    )
    return r.status_code, r.text[:500]


def supabase_submit(slug, content):
    """Try direct Supabase REST insertion."""
    # Check if there's a supabase URL in the env
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", ST_API_KEY)
    
    if supabase_url:
        r = requests.post(
            f"{supabase_url}/rest/v1/submissions",
            json={"listing_slug": slug, "content": content},
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
            },
            timeout=15
        )
        return r.status_code, r.text[:500]
    return 0, "No Supabase URL configured"


def try_all_methods(slug, content):
    methods = [
        ("direct", direct_submit),
        ("rsc", rsc_submit),
        ("next-action", next_action_submit),
        ("api-v2", apiv2_submit),
        ("graphql", graphql_submit),
    ]
    
    results = {}
    for name, func in methods:
        try:
            status, resp = func(slug, content)
            results[name] = {"status": status, "response": resp[:200]}
            print(f"  [{name}] HTTP {status}")
            if status == 200 and "error" not in resp[:100].lower():
                print(f"  -> Possible success!")
        except Exception as e:
            results[name] = {"error": str(e)}
            print(f"  [{name}] ERROR: {e}")
        time.sleep(1)
    
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 superteam_submit.py <slug> [content_file_or_text]")
        sys.exit(1)
    
    slug = sys.argv[1]
    if len(sys.argv) > 2:
        arg = sys.argv[2]
        if os.path.exists(arg):
            with open(arg) as f:
                content = f.read()
        else:
            content = arg
    else:
        # Try to find existing submission file
        pattern = f"{SUBMISSION_DIR}/{slug}*.md"
        import glob
        files = glob.glob(pattern)
        if files:
            with open(files[0]) as f:
                content = f.read()
        else:
            print("No content provided and no saved submission found")
            sys.exit(1)
    
    print(f"Submitting to: {slug}")
    print(f"Content length: {len(content)} chars")
    print()
    
    results = try_all_methods(slug, content)
    print()
    
    # Log the attempt
    log = {"slug": slug, "timestamp": datetime.now().isoformat(), "results": results}
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/submit_{slug}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json", "w") as f:
        json.dump(log, f, indent=2)
    print("Logged to logs/")
