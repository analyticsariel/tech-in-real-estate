# Turn your rent agent into an MCP server

Code for the TiRE post [Turn your rent agent into an MCP server](https://techinrealestate.com/blog/rent-data-mcp-server).

The same three rent tools as [rent-analysis-agent](../rent-analysis-agent), served over MCP, so Claude Desktop,
Claude Code or Cursor can answer rent questions in the chat you already use. The tools compute from Zillow's
free county rent data; typed returns give the client's model an output schema.

## Run it

```bash
pip install -r requirements.txt
pytest -q                                        # offline: fixture data, real MCP client in-process
claude mcp add rents -- python /full/path/to/rent_mcp.py
```

In Claude Desktop: Settings, Developer, Edit Config, add the same command under `mcpServers`, restart.

Data: [Zillow Observed Rent Index](https://www.zillow.com/research/data/), county level. MIT licensed, like the rest of this repo.
