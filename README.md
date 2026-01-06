# Project Structure

```
capstone-project/
├── backend/           # backend python + docker app
├── database/          # postgreSQL database
├── frontend/          # frontend expo + react native app
├── docs/              # all submitted documents & deliverables
├── meetings/          # meeting notes
├── compose.yml        # docker config file (only backend for now)
└── README.md
```

# Development

## Branch Conventions

##### Branch Name Format:

> `<jira ticket>/<short summary>`

- Each new feature or bug assigned by a Jira ticket will have the ticket number followed with a short explanation of the ticket in the branch name

Example: `CP-0/translation-api-integration`

## Commit Conventions

Will generally follow [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/) style. You can read into the actual specifics of it through the link if you want to, but this is what's relevant to our codebase.

##### Commit Message Format:

> `<type>: <short summary>`

where `<type>` is one of the following prefixes

| Prefix      | Meaning                                                   |
| ----------- | --------------------------------------------------------- |
| `feat:`     | New feature or functionality                              |
| `fix:`      | Bug fix                                                   |
| `test:`     | Adding or improving tests                                 |
| `chore:`    | Non-code change (dependency, config, CI, github workflow) |
| `docs:`     | Documentation update (README, docs folder, meeting notes) |
| `style:`    | Code styling or formatting only                           |
| `refactor:` | Code restructure without behavior change                  |

Examples:

- `feat: add new button to homepage`
- `fix: correct API pagination bug`
- `test: add unit tests for login flow`
- `chore: add github workflow`
- `docs: create 2025-10-10 meeting notes`
- `refactor: simplify auth middleware`

## Pull Request Conventions

As a safeguard, try to add **at least one reviewer** (whoever you think is appropriate) for a PR.

##### PR Title Format:

> `<type>: <short summary> [<jira ticket>]`

- Can omit `[<jira ticket>]` if the PR isn't related to a jira ticket (like if it's a hotfix that just came up during development)

##### PR Description

- The template in `.github/PULL_REQUEST_TEMPLATE` will automatically show up in the description when you create a PR.
- Under the **`What did you change?`** section, add the appropriate bullet points (and delete unused ones).
- Go through the **`To Do Checklist`** section and mark the completed items. Ideally all items are checked when creating a PR.

# Design

## Frontend Design

The figma containing frontend design mock up for each frame and a simple prototype flow can be viewed [here](https://www.figma.com/design/BnNfhmeOhBtzgYaucYX4FY/App-Figma--Revised-?node-id=2119-2805&t=z3D5bA4m46rnNm35-1)
