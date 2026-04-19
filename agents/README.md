# Agents

Python agents and pipelines for real estate research, pricing, and market analysis. Each subfolder is a runnable agent — clone, `pip install -r requirements.txt`, add API keys, run.

## Shape

```
/agents/
  /{agent-name}/
    README.md        # what it does, inputs/outputs, how to run
    requirements.txt # pinned Python deps
    .env.example     # required API keys (never commit real ones)
    {entry}.py       # the agent script
    # plus whatever the agent needs
```

## Stack

TiRE agents are Python 3.11+, Anthropic SDK direct (not OpenRouter), LangChain / LangGraph where it earns its keep. We fetch from FRED, Census, Redfin, Realtor.com, Zillow, HUD, HMDA, BLS, and FEMA — all free, documented at [techinrealestate.com/data](https://techinrealestate.com/data).

## What's here

Nothing yet — TiRE's own research / readings / publish pipelines are the first candidates to land here as public reference implementations. [The site's `/agents` hub](https://techinrealestate.com/agents) will list them as they ship.

## Contributing

Not accepting external PRs right now — the TiRE pipeline is the first consumer. Open an issue if you hit a bug or want to request a specific agent.
