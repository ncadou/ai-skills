# ai-skills

Home for the AI skills I use for software development.

## Layout

```text
ai-skills/
├── .claude-plugin/
│   └── marketplace.json   # declares each bundle as a plugin
├── evals/                 # behavior evals: see evals/README.md
├── LICENSE
├── README.md
└── skills/
    ├── ndev/              # bundle: see skills/ndev/README.md
    │   ├── nstart/
    │   ├── nlearn/
    │   ├── ndesign/
    │   ├── nplan/
    │   ├── nbuild/
    │   └── nreview/
    └── nwork/             # skill: see skills/nwork/README.md
```

`nwork` is an alternative to `ndev`: one skill that works from a current-state view and a working agreement. `ndev` keeps its state under `.ndev/`, and `nwork` under `.nwork/`.

## Adding a skill

1. Create a new folder under `skills/<bundle>/<skill-name>/`.
2. Add the skill files. Format is decided per-skill for now (no repo-wide standard yet).
3. Document what the skill does, when to use it, and how to invoke it.
4. Add `./<skill-name>` to the bundle's `skills` list in `.claude-plugin/marketplace.json`. For a new bundle, add a new plugin entry with `"source": "./skills/<bundle>"`. For a skill outside a bundle, like `nwork`, use `skills/<skill-name>/` with `"source": "./skills/<skill-name>"` and `"skills": ["./"]`.

## Using skills

With [`npx skills`](https://github.com/vercel-labs/skills) (OpenCode, Claude Code, Codex, Cursor, and others):

```sh
# Pick skills interactively; they are grouped by bundle
npx skills@latest add ncadou/ai-skills

# Install the whole ndev bundle
npx skills@latest add ncadou/ai-skills/skills/ndev

# Install the nwork skill
npx skills@latest add ncadou/ai-skills/skills/nwork

# From the self-hosted remote (no subpath support: select skills by name)
npx skills@latest add ssh://git@git.gateway.cadou.ca:2222/nicolas/ai-skills.git --skill '*'
```

With the Claude Code plugin marketplace (skills are then named `/ndev:nstart`, `/nwork:nwork`, etc.):

```text
/plugin marketplace add ncadou/ai-skills
/plugin install ndev@ai-skills
/plugin install nwork@ai-skills
```

Or symlink / copy the relevant `skills/<bundle>/<skill-name>/` or `skills/<skill-name>/` folder into your agent's skills directory.

## License

MIT — see [LICENSE](LICENSE).
