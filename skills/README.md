# Skills

Claude Code skills for real estate work. Each subfolder is a self-contained skill — drop it into your `~/.claude/skills/` (or a project-local `.claude/skills/`) and invoke it from Claude Code.

## Shape

```
/skills/
  /{skill-name}/
    SKILL.md         # Claude-facing frontmatter + instructions
    README.md        # human-facing: what it does, when to use, how to install
    # any supporting files the skill references
```

## Installing

```bash
cp -r skills/{skill-name} ~/.claude/skills/
```

Then in any Claude Code session, the skill is invokable by name. See [Anthropic's skills docs](https://docs.claude.com/en/docs/claude-code/skills) for the lifecycle.

## What's here

Nothing yet — the first skills ship shortly. Until then, [the site's `/skills` hub](https://techinrealestate.com/skills) is the catalog view of what's planned.

## Contributing

Not accepting external PRs at the moment — the TiRE pipeline writes most of these. If you have a skill you'd like to see, open an issue with the problem it solves (not the implementation).
