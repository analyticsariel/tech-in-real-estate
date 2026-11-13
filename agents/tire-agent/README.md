# tire-agent

The agent behind [techinrealestate.com/ask](https://techinrealestate.com/ask). Ask it about the data on the site (rates, rents, jobs, prices, 166 metrics from 9 public sources) and it answers in a few sentences. Every number is checked against the data it read, and every answer links to its source page.

This is a reference implementation, not a package. It reads a SQLite corpus built from TiRE's own catalogs, so to point it at your data, start with `build_db.py`.

## How it answers

1. **Search.** It finds the pages you mean with SQLite FTS5. If the place or topic isn't covered, it says so and stops.
2. **Query.** It reads numbers with read-only SQL. Changes, trends, streaks, and county-vs-state-vs-US comparisons over the same months are pre-computed in `summary.py`, so the model never does arithmetic.
3. **Check.** `grounding.py` compares every number and link in the draft against what the tools returned in that run. A miss gets one retry. A second miss returns the pages it read instead of an answer.
4. **Decline.** It won't give buy, sell, or wait advice, or forecasts of its own. It reports published forecasts (Zillow's) as forecasts, with their base month and horizon.

It's built on LangChain Deep Agents with Claude Haiku 5.5 on Amazon Bedrock and structured output. A typical answer takes about 5 seconds and costs under a tenth of a cent.

## What's in here

```
tire_agent/
  build_db.py      catalogs + metric history -> tire.db (fails loudly, writes nothing on error)
  summary.py       all the math: calendar-month windows, streaks, aligned benchmarks, forecast horizons
  tools.py         search (FTS5) and read-only query (SQLite authorizer, caps, timeout)
  agent.py         the Deep Agent, the model, call limits, the AWS account guard
  ask.py           one request end to end: deadline, guard, grounding, retry, honest fallback
  grounding.py     number and link validation
  guard.py         stop-reason, refusal, and cost checks
  prompts.py       system prompt
  server.py        FastAPI app for Lambda: streams progress events, then the answer
  gate.py          sign-in gate: one free question (Cloudflare Turnstile), then Clerk
  limits.py        per-IP limits and daily/monthly spend caps that fail closed
  history.py       saved questions for signed-in users (DynamoDB, 12-month TTL)
  evals/           golden set, code evaluators, LangSmith experiment + gate
  deploy/          Dockerfile, SAM template, GitHub OIDC bootstrap, account guard
requirements.txt   pinned runtime deps (Python 3.12)
.env.example       configuration
```

## Run it locally

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your AWS profile + account and a LangSmith key
python -m tire_agent.build_db          # needs TiRE's catalog + history layout; adapt for your data
python -m tire_agent ask "What's the 30-year mortgage rate right now?"
```

The agent refuses to call Bedrock unless the active AWS credentials belong to `TIRE_AWS_ACCOUNT_ID`. That's deliberate. It's cheap insurance against running on the wrong account.

## Evals

`evals/golden.yaml` holds the test questions. Expectations point at cells in `tire.db`, not literal values, so a weekly data refresh doesn't break them. Four code evaluators score each run:

- `correct_answer`: numbers, directions, and dates right, or correctly declined
- `citations`: only live pages
- `budget`: tool calls within the limit
- `plain_dates`: no ISO dates in prose

The deploy is gated on them: correct answers at 95% or better, and the other three at 100%. A failing example is re-run once before the gate decides.

```bash
python -m tire_agent.evals.sync     # mirror the golden set to a LangSmith dataset
python -m tire_agent.evals.run --model claude-haiku-5-5
```

## Deploy

AWS Lambda behind a function URL in response-streaming mode, via the Lambda Web Adapter. DynamoDB holds limits and history, CloudWatch alarms go to SNS email, and SSM Parameter Store holds secrets. `deploy/bootstrap.yaml` creates GitHub OIDC deploy roles with a permissions boundary, so CI never holds long-lived keys. `deploy/template.yaml` is the SAM stack. Fill in `deploy/samconfig.toml` with your account before deploying.

## License

MIT, like the rest of this repo.
