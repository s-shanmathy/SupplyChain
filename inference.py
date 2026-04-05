import asyncio
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from engine import SupplyChainEnv
from models import Action

# Environment variables
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "<your-active-endpoint>"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
TASK_NAME = os.getenv("MY_ENV_V4_TASK", "supply-chain-disruption-response")
BENCHMARK = os.getenv("MY_ENV_V4_BENCHMARK", "supply_chain_openenv")
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))
SUCCESS_SCORE_THRESHOLD = float(os.getenv("SUCCESS_SCORE_THRESHOLD", "0.1"))

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are controlling a supply chain disruption response environment.

    Available actions are:
    - reroute_order: redirect a delayed order to an alternate supplier
    - negotiate: improve supplier contract terms to lower costs
    - split_order: split a customer order across multiple suppliers
    - notify_customer: alert a customer about a late or delayed order
    - expedite: pay to accelerate delivery for an assigned order
    - cancel_order: cancel a risky order to reduce loss
    - query: request information about an order or supplier

    Reply with a single line in the format: ACTION_TYPE target_id value
    Examples:
    reroute_order O1 1.0
    negotiate Alt2 0.0
    split_order O2 0.0
    notify_customer O3 0.0
    expedite O1 1.0
    cancel_order O2 0.0
    query O1 0.0
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def get_model_action(client: OpenAI, step: int, obs: object, history: List[str]) -> str:
    try:
        observation_text = (
            f"inventory={obs.inventory_levels} "
            f"pending_orders={[o.order_id + ':' + o.status for o in obs.pending_orders]} "
            f"disruption={obs.disruption_event.event_type} "
            f"budget={obs.budget_remaining} "
            f"feedback={obs.feedback}"
        )
    except Exception:
        observation_text = "obs unavailable"

    previous_actions = "\n".join(history[-4:]) if history else "None"
    prompt = textwrap.dedent(
        f"""
        Step {step}.
        Observation: {observation_text}
        Previous actions:
        {previous_actions}
        Provide one action in format ACTION_TYPE target_id value.
        """
    ).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=64,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        # normalize to first line
        first_line = text.splitlines()[0].strip()
        if not first_line:
            return "NOTIFY S1 0.1"
        return first_line
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "NOTIFY S1 0.1"


def parse_action(action_str: str) -> Action:
    tokens = action_str.strip().split()
    if len(tokens) < 3:
        raise ValueError("Action format invalid; expected ACTION target_id value")

    action_type = tokens[0].lower()
    target_id = tokens[1]
    value = float(tokens[2])
    parameters = {}

    if len(tokens) > 3:
        if action_type in {"reroute_order", "negotiate"}:
            parameters["supplier_id"] = tokens[3]
        elif action_type == "split_order":
            parameters["supplier_ids"] = tokens[3:]

    if action_type not in {
        "reroute_order",
        "negotiate",
        "split_order",
        "notify_customer",
        "expedite",
        "cancel_order",
        "query",
    }:
        raise ValueError(f"Invalid action_type {action_type}")

    return Action(action_type=action_type, target_id=target_id, value=value, parameters=parameters)


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    env = SupplyChainEnv(random_seed=42)
    result_obs = env.reset()

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0
    error_msg = None

    try:
        for step in range(1, MAX_STEPS + 1):
            action_str = get_model_action(client, step, result_obs, history)
            try:
                action = parse_action(action_str)
                obs, rew, done, info = env.step(action)
                reward_value = float(rew.value)
                error_msg = None
            except Exception as e:
                reward_value = 0.0
                done = False
                obs = result_obs
                error_msg = str(e)

            log_step(step=step, action=action_str, reward=reward_value, done=done, error=error_msg)

            rewards.append(reward_value)
            steps_taken = step
            result_obs = obs
            history.append(f"{action_str} -> {reward_value:.2f}")

            if done:
                break

        # normalize final success
        total_reward = sum(rewards)
        score = max(0.0, min(1.0, total_reward / (MAX_STEPS * 10.0)))
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            # no close method in local env but keep format
            if hasattr(env, "close"):
                close_result = env.close()
                if asyncio.iscoroutine(close_result):
                    await close_result
        except Exception as close_exc:
            print(f"[DEBUG] env.close() error: {close_exc}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())
