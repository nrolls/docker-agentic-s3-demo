# Prompts

Copy these into your agent one at a time. Each one asks the agent to make its own
branch, because in clone mode the agent manages branches inside its private clone.

## Feature 1: due dates

```
Create a branch called feat/due-dates before you change anything.

Add optional due dates to tasks. Store them as ISO dates (YYYY-MM-DD). Let me set
one when I add a task, in both the HTML form and the JSON API. Show the date next
to each task, and add a badge for tasks that are overdue or due today. Sort open
tasks by due date, with undated tasks last. Existing tasks without a due date must
still load.

Use only the Python standard library. Add unit tests, run `python3 -m unittest`,
and commit when everything passes.
```

## Feature 2: holiday warnings (this one hits the network boundary)

```
On the same branch, warn me when a task's due date falls on a US public holiday.
Use the Nager.Date API: https://date.nager.at/api/v3/PublicHolidays/{year}/US

Cache results per year in memory, and fail gracefully if the API can't be reached:
no warning, no crash. Standard library only. Tests must not hit the network, so
stub the API in tests. Run the suite and commit.
```

If the agent tells you the request was blocked, that's the point. See step 5 in the
README, then tell the agent:

```
I've allowed date.nager.at for this sandbox. Try the request again.
```

## Feature 3: a parallel branch (optional)

```
Create a separate branch called feat/priority from main, not from feat/due-dates.
Add a priority field (low, normal, high), show it as a colored chip, and sort high
priority first. Add tests, run the suite, and commit.
```

## Kit check (use in the taskapp-kit sandbox)

```
Read the instructions your kits gave you, then tell me which conventions and tools
this project expects. Run the project's checks and show me the results.
```
