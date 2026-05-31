# NullState Tools

Autonomous revenue-generation toolkit for AI agents.

## Tools

| Tool | Description |
|------|-------------|
| `bounty_hunter.py` | Scans Superteam Earn for AGENT_ALLOWED bounties, generates submissions, tracks progress |
| `securebanana_fixer.py` | Auto-fixes SecureBananaLabs bug bounties — creates branches, commits, and PRs |
| `owlrun_manager.py` | Manages Owlrun idle compute node — earnings dashboard, Lightning wallet, job monitoring |
| `superteam_submit.py` | Multi-method Superteam submission engine — tries direct, RSC, GraphQL, and Supabase endpoints |

## Quick Start

```bash
# Find bounties
python3 bounty_hunter.py

# Fix SecureBananaLabs issues
python3 securebanana_fixer.py auto

# Monitor Owlrun earnings
python3 owlrun_manager.py status
```

## Revenue Sources

- **SecureBananaLabs Bug Bounties**: $430-$780 per issue, AI-agent-friendly
- **Superteam Earn**: AGENT_ALLOWED bounties, USDC payments on Solana
- **Owlrun**: Passive Bitcoin sats for idle compute
- **dealwork.ai**: API-first AI agent marketplace
- **toku.agency**: High-volume AI agent job board

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Bounty Scanner  │────▶│  Content Gen     │────▶│  Submitter     │
│  (Superteam API) │     │  (OpenRouter AI) │     │  (Multi-method)│
└─────────────────┘     └──────────────────┘     └────────────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐              ▼
│  Bug Fixer       │────▶│  PR Creator      │     ┌────────────────┐
│  (SecureBanana)  │     │  (GitHub API)    │     │  Revenue Log    │
└─────────────────┘     └──────────────────┘     └────────────────┘
                                                          
┌─────────────────┐     ┌──────────────────┐
│  Owlrun Monitor  │────▶│  Lightning Wallet │
│  (Passive Sats)  │     │  (BTC Payout)    │
└─────────────────┘     └──────────────────┘
```
