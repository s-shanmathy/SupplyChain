from typing import List, Optional

from engine import SupplyChainEnv
from models import Action
from tasks import EasyTask, MediumTask, HardTask


def select_action(env: SupplyChainEnv) -> Action:
    # Prioritize rerouting a pending order first.
    pending_orders = [order for order in env.pending_orders if order.status == "PENDING"]
    if pending_orders and env.alternative_suppliers:
        order = pending_orders[0]
        alt = next((alt for alt in env.alternative_suppliers if alt.product == order.product and alt.available_qty >= order.quantity), None)
        if alt:
            return Action(
                action_type="reroute_order",
                target_id=order.order_id,
                value=1.0,
                parameters={"supplier_id": alt.supplier_id},
            )

    late_orders = [order for order in env.pending_orders if order.status == "LATE" and not order.notified]
    if late_orders:
        return Action(action_type="notify_customer", target_id=late_orders[0].order_id, value=0.0)

    assigned_orders = [order for order in env.pending_orders if order.status == "ASSIGNED" and order.expected_delivery is not None]
    if assigned_orders:
        return Action(action_type="expedite", target_id=assigned_orders[0].order_id, value=1.0)

    if env.alternative_suppliers:
        # Negotiate with the cheapest alternative supplier.
        alt = min(env.alternative_suppliers, key=lambda alt: alt.unit_cost)
        return Action(action_type="negotiate", target_id=alt.supplier_id, value=0.0)

    # Fallback query action.
    order_id = env.pending_orders[0].order_id if env.pending_orders else "O1"
    return Action(action_type="query", target_id=order_id, value=0.0)


def run_baseline(seed: int = 1234, steps: int = 30) -> dict:
    env = SupplyChainEnv(random_seed=seed, max_steps=steps)
    env.reset()

    rewards: List[float] = []
    last_action: Optional[Action] = None
    for _ in range(steps):
        action = select_action(env)
        obs, reward, done, info = env.step(action)
        rewards.append(reward.value)
        last_action = action
        if done:
            break

    easy_score = EasyTask.evaluate(env, last_action) if last_action else 0.0
    medium_score = MediumTask.evaluate(env, last_action) if last_action else 0.0
    hard_score = HardTask.evaluate(env)

    return {
        "avg_reward": sum(rewards) / len(rewards) if rewards else 0.0,
        "total_reward": sum(rewards),
        "easy_score": easy_score,
        "medium_score": medium_score,
        "hard_score": hard_score,
        "final_state": env.state(),
    }


if __name__ == "__main__":
    results = run_baseline(seed=42, steps=30)
    print("Baseline results:")
    for k, v in results.items():
        if k == "final_state":
            continue
        print(f"  {k}: {v}")
