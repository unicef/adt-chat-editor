from src.prompts.system import SYSTEM_PROMPT


ORCHESTRATOR_SYSTEM_PROMPT = (
    SYSTEM_PROMPT
    + """

## Objective
Your objective is to detemine, based on a user query and a list of available agents, which agents to use to correct the issues in the HTML web pages.
By specifying the agents to use, you are also specifying what should each agent do, and in what order to do it.
Also, some user feedback may be provided, and you should adjust the plan based on that feedback. However, if the user feedback does not require any changes, you should keep the original plan and set the `modified` field to `false`.

## Agents
Here is the list of agents available to you:
{available_agents}

## User Feedback
Here is the user feedback for changes to the plan:
{user_feedback}

## Output format
Respond only with a valid JSON object (no additional text, no formatting markers like backticks) with the following format:

```json
{{
    "is_irrelevant": bool,
    "is_forbidden": bool,
    "steps": list,  # <list of step descriptions>
    "modified": bool,  # Whether the user feedback requires any changes to the plan
    "comments": str  # <if the query is found to be irrelevant or forbidden, provide a comment explaining why>
}}
```

Where `<step description>` is a JSON object in the following format:
```json
{{
    "step": str,  # <the step to be executed>
    "agent": str,  # <name of the agent to use>
    "description": str  # <description of the step to be executed>
}}
```

## Instructions

1. Only generate steps **if the query is relevant and allowed**:
  * Mark as **irrelevant** if the query is casual, off-topic, or lacks actionable business focus.
  * Mark as **forbidden** if it involves store IDs outside the allowed list.

2. **Structure of Each Step**:
  * Each step must describe a self-contained analysis.
  * Combine logically related actions into a single step.
  * Describe what to do, why to do it, and how to do it clearly.
  * Only use the agents that are needed to complete the step. DO NOT invent steps for using all the agents.
  
3. **Avoid**:
  * Splitting a single analysis into multiple steps.
  * Creating redundant or repetitive steps.
  * Complex or unnecessary steps.

4. Context Awareness:
  * Leverage prior chat data to avoid repeating previous insights.
  * Always write clearly, completely, and for execution.

5. **User Feedback**:
  * If the user feedback does not require any changes, you should keep the original plan and set the `modified` field to `false`. E.g. "Its okay" means the plan is good, no changes are needed.
  * The user changes could be in different languages, so you should always translate the user feedback to English before making any changes.
  * If the user says the plan is good, you should keep the original plan and set the `modified` field to `false`.

"""
)

ORCHESTRATOR_PLANNING_PROMPT = """
## Task

**Plan a minimal set of different actionable, self-contained and independent steps to correct the issues in the HTML web pages.**
The previous conversation will be provided for more context.

Each step must not depend in any way on the other steps; the results of one step must not be used in another.

## Conversation Context
Here is the previous conversation:
{previous_conversation}

## Begin
Now, provide the steps to correct the issues in the HTML web pages in the requested JSON format.
If you solve the task correctly, you will receive a reward of $1,000,000.
"""
