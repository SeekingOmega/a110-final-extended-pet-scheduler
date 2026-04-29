# Model Card — PawPal+ Calendar Agent

## AI Feature

**Model:** `gemini-3.1-flash-lite-preview` (`google-genai` SDK)
**Role:** Function-calling scheduling agent

The model is given two read-only tools (`read_calendar_events`, `list_pet_tasks`) and uses them to gather context before proposing a weekly pet care schedule as structured JSON. Python owns all writes to Google Calendar — the model never writes directly.

## How It Works

1. User clicks "Generate Schedule with Gemini"
2. Gemini calls `list_pet_tasks()` to get all pets, tasks, active hours, and the selected week
3. Gemini calls `read_calendar_events(start, end)` to see existing calendar events
4. Gemini returns a JSON object with `proposed_events`, `unschedulable`, and `reasoning_summary`
5. The app renders the proposal — user approves or rejects individual events
6. Approved events are written to Google Calendar only after explicit user confirmation

## Scheduling Rules (enforced via prompt)

1. **Daily tasks are per-day independent** — if Monday has no slot, Monday's task is unschedulable. Tuesday still gets its own fresh attempt. Never doubled up.
2. **Weekly tasks can float** to any day in the week with a free slot
3. **Once tasks** must land on or before their due date
4. **No tasks outside active hours** — user sets a daily window
5. **No overlap** with existing Google Calendar events
6. **No silent drops** — every unschedulable task appears with a human-readable reason

## Limitations

- Active hours are a single daily window — does not handle different schedules on weekdays vs. weekends
- No concept of task dependencies (e.g., vet visit must precede medication)
- Relies on the quality of existing Google Calendar data (missing events = missed conflicts)
- The model may create an implicit morning bias — it tends to schedule tasks early in the active window even when later slots would be equally valid
- JSON output is parsed with a `{...}` extraction heuristic; highly unusual model responses could cause parsing errors

## Misuse Prevention

- The model has **no write tools** — it can only read calendar events and pet tasks
- All proposed events are shown to the user before any write occurs
- User must explicitly click "Add to Google Calendar" to trigger writes
- `token.json` and `.env` are excluded from version control via `.gitignore`

## Testing

The `eval/test_harness.py` script contains five validation functions that check scheduling rule compliance. It runs entirely against a hardcoded `MOCK_SCHEDULE` dict that was manually written to satisfy every rule — no Gemini calls, no real API calls.

```bash
python eval/test_harness.py
# 5/5 tests passed
```

```
[PASS] Daily tasks not carried over to wrong day
[PASS] No task appears in both proposed and unschedulable
[PASS] All events within active hours
[PASS] No proposed event overlaps existing calendar events
[PASS] All unschedulable tasks have a reason
```

The 5/5 result confirms the validation logic is correct, not that the model follows the rules. Because the mock data was crafted to comply with every rule, the tests were guaranteed to pass before they ran. To test actual model compliance, `MOCK_SCHEDULE` would need to be replaced with live Gemini output.

## Testing Surprises

- **Timezone offset bug:** Events scheduled at 7am appeared at 10am in Google Calendar because the app hardcoded `America/Los_Angeles` while the test account was in Eastern time. The fix was to detect the calendar timezone via the API at runtime rather than assuming one. This was not a model failure — it was a data pipeline bug that only showed up during live testing.
- **Edge-of-slot overlap:** In a few test runs, Gemini proposed an event starting at the exact minute an existing event ended. This technically wasn't an overlap (end == start), but it felt unrealistic and highlighted that prompt rules like "no overlap" need explicit definitions of boundary behavior.
- **Dense schedule behavior:** When the task list had 10+ daily tasks and the calendar was 60–70% full, Gemini occasionally placed one or two events outside the active hours window by a few minutes. This appeared in manual inspection of live output; it did not appear in lighter test cases.

## AI Collaboration Notes

**Helpful:** Claude (Claude Code) suggested moving `_calendar_reader` and `_task_lister` outside the Streamlit button block so they stay in scope when the "Reschedule Rejected" button triggers a rerun — this was a non-obvious Streamlit-specific issue that would have caused a `NameError` at runtime with no clear error message pointing to the cause.

**Flawed suggestion:** Claude recommended switching from `google-generativeai` to the newer `google-genai` SDK and provided a full rewrite of the scheduler. The migration itself was correct, but the `GenerateContentConfig` structure it wrote placed `system_instruction` in a position the SDK rejected at runtime with a cryptic validation error. The fix required reading the SDK source to find the correct config field layout — something Claude's suggestion skipped over.

## Reflections

This project taught me that agentic AI systems are mostly infrastructure problems. The Gemini prompt took an afternoon; the OAuth flow, timezone handling, Streamlit rerun lifecycle, and Google Calendar API edge cases took the rest of the project. The model itself was the easiest part once the data pipeline was reliable.

What surprised me about Gemini's tool use was how naturally it sequenced the two tool calls. Without explicit instruction, it consistently called `list_pet_tasks` first (to learn the week range), then `read_calendar_events` with those exact dates. That emergent sequencing — figuring out what it needs before fetching it — felt like genuine reasoning rather than pattern matching. It made me more confident in the function-calling approach for this kind of structured planning task.
