# Build a rent-analysis agent

Code for the TiRE post [Build a rent-analysis agent](https://techinrealestate.com/blog/rent-analysis-agent).

Ask it a rent question in plain English ("Where are Florida rents falling, and is there a pattern?") and it
pulls Zillow's free county rent data, runs the comparisons and explains what it found. The model never
calculates anything: three small pandas tools do the math, and the model reads their results.

## Run it

```bash
pip install -r requirements.txt
pytest -q                     # offline: fixture data and a scripted fake model, no API key
export ANTHROPIC_API_KEY=...
python rent_agent.py "Where are Florida rents falling, and is there a pattern?"
```

To use another provider, change the model string in `rent_agent.py` (e.g. `"openai:..."`) and install
that provider's LangChain package.

## Files

- `rent_agent.py`: the data loader, the three tools (`state_overview`, `rank_counties`, `county_detail`) and `build_agent(model)`.
- `test_rent_agent.py`: checks the pandas math by hand and runs the agent end to end with a fake model.
- `requirements.txt`: pinned versions the tests pass on.

Data: [Zillow Observed Rent Index](https://www.zillow.com/research/data/), county level. MIT licensed, like the rest of this repo.
