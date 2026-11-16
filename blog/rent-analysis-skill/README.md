# Teach Claude to read county rent data

Code for the TiRE post [Teach Claude to read county rent data](https://techinrealestate.com/blog/rent-analysis-skill).

A Claude skill: `SKILL.md` tells Claude how to read county rents (what Zillow's index measures, how to compare
counties, what the data can't tell you), and `rent_report.py` computes every number from Zillow's free county
rent file. Claude loads the skill when a rent question comes up and runs the script itself.

## Run it

```bash
pip install -r requirements.txt
pytest -q                                  # offline: fixture CSV, no network
mkdir -p ~/.claude/skills/rent-analysis
cp SKILL.md rent_report.py ~/.claude/skills/rent-analysis/
```

Start a new Claude Code session and ask, for example, "How are rents moving in Lee and Palm Beach County?"
The Python that Claude runs needs pandas installed. To see exactly what Claude sees:
`python rent_report.py FL "Lee" "Palm Beach"`.

Data: [Zillow Observed Rent Index](https://www.zillow.com/research/data/), county level. MIT licensed, like the rest of this repo.
