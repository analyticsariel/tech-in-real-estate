# MCP Servers

[Model Context Protocol](https://modelcontextprotocol.io) servers that expose real estate data to agents. Each subfolder is an MCP server — clone, install, point your agent at it.

## Shape

```
/mcps/
  /{server-name}/
    README.md        # what it exposes, how to connect, auth setup
    package.json     # or pyproject.toml / Cargo.toml depending on lang
    src/             # the server code
    .env.example     # required upstream API keys
```

## Why MCPs

The TiRE thesis on MCPs: the interesting work isn't "build another data API wrapper" — it's exposing the data we already catalog in a shape agents can reason about. An MCP server over FRED + Census + Redfin + Zillow is a better interface for a real estate agent than nine raw upstream APIs.

## What's here

Nothing yet. First MCP lands when it's ready to be useful, not before. [The site's `/mcp` hub](https://techinrealestate.com/mcp) is the catalog view.

## Contributing

Not accepting external PRs yet. Issues welcome if you hit a bug or want to request a specific MCP.
