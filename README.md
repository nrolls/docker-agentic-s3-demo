# Build a feature in a Docker Sandbox

Companion repo for Session 3 of Docker's agentic development series,
**Agentic Development in Practice: Build a Feature in a Sandbox** (live Nov 17, 2026).

You'll hand a small task app to a coding agent running in a Docker Sandbox, let it
build real features, and watch three boundaries do their job:

- **File boundary.** In clone mode the agent works on a private copy of your repo.
  It can't change your checkout.
- **Network boundary.** The agent reaches only what your policy allows, and every
  blocked request shows up in a log.
- **Kits.** Tools, network rules, and team instructions packaged once, so every
  sandbox starts the same way.

The app uses only the Python standard library, so the agent never needs to install
packages. That keeps the one network moment in this demo the one we planned.

## What you need

- The `sbx` CLI, v0.45 or later (v3 kits need it). Docker Desktop isn't required.
  Install guide: https://docs.docker.com/ai/sandboxes/install/
- A Docker account. Run `sbx login` once after installing.
- Access to a coding agent. We use Claude Code, and other agents work too:
  https://docs.docker.com/ai/sandboxes/agents/
- Git.
- Optional: Python 3.10+ to run the app and its tests on your host. No packages to
  install.

Commands below are for macOS and Linux. Tested with sbx `TODO-version`.

## 1. Get the app running (optional)

```
git clone https://github.com/nrolls/docker-agentic-s3-demo.git
cd docker-agentic-s3-demo
python3 -m unittest
python3 app.py
```

Open http://localhost:8000, then stop the app with Ctrl+C.

## 2. Check your sandbox policy

```
sbx policy ls
```

If the first line says `Governance: Managed by <your org>`, your organization manages
network policy centrally. Local `sbx policy allow` rules won't do anything for you, so
in step 5 the allow happens in Docker Home instead. That's the path we use live.

Then confirm the holiday API starts out blocked:

```
sbx policy check network date.nager.at
```

You should see `Denied`. If you see `Allowed`, your policy already permits it and
step 5 won't show a block.

## 3. Start the agent in clone mode

```
cp .env.example .env
sbx run --clone --name taskapp claude .
```

`--clone` mounts your repo read-only inside the sandbox and gives the agent its own
private Git clone to work in. Your working tree and your `.git` folder stay exactly
as they are until you choose to fetch the agent's work.

Paste **Feature 1** from [PROMPTS.md](PROMPTS.md). The agent creates its own branch,
`feat/due-dates`, inside its clone.

## 4. Prove the file boundary

While the agent works, open a second terminal in the repo folder:

```
sbx exec taskapp -- touch /run/sandbox/source/agent-was-here.txt
git status
```

The `touch` fails because your repo is mounted read-only, and `git status` on your
host stays clean.

Now try reading the `.env` file you created:

```
sbx exec taskapp -- cat /run/sandbox/source/.env
```

That works. Clone mode protects your repo from being changed, not from being read.
Keep real secrets out of your working directory and let `sbx` inject credentials
through its proxy instead.

## 5. Watch the network boundary

Paste **Feature 2** from [PROMPTS.md](PROMPTS.md). The agent will try to call
`date.nager.at` and get blocked. In your second terminal:

```
sbx policy log --limit 5
```

You'll see the blocked host and the rule that stopped it. How you open it up depends
on who owns your policy.

**If your org manages policy** (the path we use live), an admin adds the host in
Docker Home: select your organization, open **AI Platform > Network access**, open the
policy's menu (⋮), select **Edit**, and add an allow rule for `date.nager.at`. Then
check it from your terminal:

```
sbx policy check network --sandbox taskapp date.nager.at
```

An org rule applies to every sandbox the policy covers, not just this one, so remove
it from the policy when you're done.

**If you manage your own local policy**, allow it for this one sandbox only:

```
sbx policy allow network --sandbox taskapp date.nager.at
sbx policy check network --sandbox taskapp date.nager.at
```

When you're done with the demo, remove the local rule:

```
sbx policy rm network --sandbox taskapp --resource date.nager.at
```

Either way, tell the agent to try again once the check says `Allowed`.

## 6. Review the agent's work on your host

When the agent says it has committed:

```
git fetch sandbox-taskapp
git log --oneline main..sandbox-taskapp/feat/due-dates
git diff --stat main...sandbox-taskapp/feat/due-dates
```

`sandbox-taskapp` is a Git remote that `sbx` added to your repo. Treat what comes
through it like a pull request from a contributor you haven't worked with yet. The
remote only answers while the sandbox is running.

When you're happy with it:

```
git switch -c feat/due-dates sandbox-taskapp/feat/due-dates
python3 -m unittest
python3 app.py
```

If the app was already running, stop it with Ctrl+C first so it picks up the new
code. Your tasks carry over, because they're saved in the git-ignored `data/` folder.

## 7. Package the setup as a kit

Open [kits/taskapp-tools/taskapp-tools.yaml](kits/taskapp-tools/taskapp-tools.yaml).
It's a v3 mixin that adds a linter, allows the holiday API, and gives the agent the
team's conventions. Create a second sandbox with it:

```
sbx create --clone --name taskapp-kit --kit ./kits/taskapp-tools claude .
sbx exec taskapp-kit -- ruff --version
sbx policy ls taskapp-kit --source kit --type network --wide
sbx policy check network --sandbox taskapp-kit date.nager.at
```

On a machine you manage yourself, the holiday API is allowed here without you typing
an allow rule, because the kit carried it. If your org manages policy, the kit's rule
is a request: it only takes effect where the org already allows the host. A kit can't
grant access beyond your org's policy.

Start the agent and paste the **Kit check** prompt:

```
sbx run --name taskapp-kit
```

## 8. Run tasks in parallel (optional)

Back in the `taskapp` sandbox, paste **Feature 3**. One clone can hold several
branches, so you can review each one separately:

```
git fetch sandbox-taskapp
git branch -r
```

## 9. Clean up

```
sbx ls
sbx rm taskapp-kit
sbx rm taskapp
```

`sbx rm` warns you if the sandbox has commits you haven't fetched yet.

## Try it on your own project

- **Today:** run one real task from your backlog in clone mode and review the branch
  like a PR.
- **Next:** check `sbx policy log` to see what your agent actually reached for, then
  tighten your rules.
- **This week:** package your team's tools and rules as a kit.
- **Want help?** Request an onboarding session: https://www.docker.com/onboarding-request/

## Learn more

- Git workflows and clone mode: https://docs.docker.com/ai/sandboxes/workflows/git/
- Isolation layers: https://docs.docker.com/ai/sandboxes/security/isolation/
- Local network rules: https://docs.docker.com/ai/governance/local/network-rules/
- Use kits: https://docs.docker.com/ai/sandboxes/customize/use-kits/
- Build a tool mixin: https://docs.docker.com/ai/sandboxes/customize/author/tool-mixins/

## What's in this repo

| Path | What it is |
| --- | --- |
| `app.py` | The web app and JSON API (standard library HTTP server) |
| `tasks.py` | A small JSON-file task store |
| `templates/index.html` | The page the app renders |
| `tests/` | Unit tests. Run `python3 -m unittest` |
| `PROMPTS.md` | The prompts used in the session |
| `kits/taskapp-tools/` | A v3 kit: linter, network rule, and agent instructions |
| `.env.example` | A fake secret for the file boundary demo |
