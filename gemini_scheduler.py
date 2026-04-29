"""Gemini function-calling agent for weekly pet care scheduling."""
import json
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are a pet care scheduling assistant. Your job is to propose a weekly schedule for pet care tasks around the owner's existing calendar events and active hours.

Rules you MUST follow:
1. DAILY tasks must be scheduled on each specific day independently. If a day has no viable slot, mark the task as unschedulable for THAT DAY ONLY — never move a daily task to a different day.
2. WEEKLY tasks may be placed on any day that has a free slot.
3. ONCE tasks must be scheduled on or before their due_date.
4. Never propose a pet task outside the owner's active_hours_start to active_hours_end window.
5. Never propose a pet task that overlaps an existing calendar event.
6. Every task that cannot be scheduled must appear in the unschedulable list with a specific reason.

Use the available tools to gather all data first, then return ONLY a JSON object with this exact structure:
{
  "proposed_events": [
    {"task_name": str, "pet_name": str, "day": "YYYY-MM-DD", "start_time": "HH:MM", "duration_min": int, "priority": str}
  ],
  "unschedulable": [
    {"task_name": str, "pet_name": str, "day": "YYYY-MM-DD", "reason": str}
  ],
  "reasoning_summary": str
}"""

_TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="read_calendar_events",
        description="Read the user's Google Calendar events for the selected week.",
        parameters={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date":   {"type": "string", "description": "End date YYYY-MM-DD"},
            },
            "required": ["start_date", "end_date"],
        },
    ),
    types.FunctionDeclaration(
        name="list_pet_tasks",
        description="Get all pets, tasks, and owner scheduling preferences (active hours, week range).",
        parameters={"type": "object", "properties": {}},
    ),
]

_TOOLS = types.Tool(function_declarations=_TOOL_DECLARATIONS)
_MAX_TOOL_ROUNDS = 10


class GeminiScheduler:
    def __init__(self, api_key: str, calendar_reader, task_lister):
        """
        calendar_reader: callable(start_date: str, end_date: str) -> list[dict]
        task_lister:     callable() -> dict
        """
        self.client = genai.Client(api_key=api_key)
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[_TOOLS],
        )
        self.model_name = "gemini-3.1-flash-lite-preview"
        self.calendar_reader = calendar_reader
        self.task_lister = task_lister
        self.steps: list[dict] = []

    def _execute_tool(self, name: str, args: dict) -> str:
        if name == "read_calendar_events":
            start_date = args.get("start_date", "")
            end_date = args.get("end_date", "")
            if not start_date or not end_date:
                raise ValueError(f"read_calendar_events called with missing args: {args!r}")
            result = self.calendar_reader(start_date, end_date)
            self.steps.append({"tool": name, "args": args, "result_count": len(result)})
            return json.dumps(result)
        if name == "list_pet_tasks":
            result = self.task_lister()
            self.steps.append({"tool": name, "args": {}, "result": result})
            return json.dumps(result)
        raise ValueError(f"Unknown tool: {name}")

    def _run_loop(self, initial_message: str) -> dict:
        """Run the Gemini tool-call loop and return the parsed JSON schedule."""
        chat = self.client.chats.create(model=self.model_name, config=self.config)
        response = chat.send_message(initial_message)

        for _ in range(_MAX_TOOL_ROUNDS):
            fn_calls = response.function_calls
            if not fn_calls:
                break
            fn_response_parts = []
            for fc in fn_calls:
                tool_result = self._execute_tool(fc.name, dict(fc.args))
                fn_response_parts.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": tool_result},
                    )
                )
            response = chat.send_message(fn_response_parts)
        else:
            raise RuntimeError("Gemini tool-call loop exceeded maximum iterations")

        text = response.text
        if not text:
            raise ValueError(f"Model returned empty text. Finish reason: {getattr(response, 'finish_reason', 'unknown')}")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON object found in model response: {text!r}")
        return json.loads(text[start:end])

    def generate_schedule(self) -> dict:
        """Ask Gemini to gather data and propose a full weekly schedule."""
        self.steps = []
        return self._run_loop("Gather the necessary data using the available tools and propose the weekly schedule.")

    def reschedule_rejected(self, rejected: list[dict], confirmed: list[dict]) -> dict:
        """Ask Gemini to find new slots for rejected events, treating confirmed as blocked."""
        self.steps = []
        prompt = (
            f"The user rejected some proposed events. Gather fresh calendar data, then find new slots "
            f"for the rejected tasks only.\n"
            f"Already confirmed (treat as blocked): {json.dumps(confirmed)}\n"
            f"Rejected tasks to reschedule: {json.dumps(rejected)}\n"
            f"Return the same JSON structure for the rescheduled tasks only."
        )
        return self._run_loop(prompt)
