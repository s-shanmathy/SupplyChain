from __future__ import annotations

from engine import SupplyChainEnv
from models import Action


class EasyTask:
    """Easy — Single disruption, one product: reroute within budget and meet the deadline."""

    @staticmethod
    def evaluate(env: SupplyChainEnv, action: Action) -> float:
        if env.last_reward is None:
            return 0.0

        if env.disruption_event.event_type != "SUPPLIER_DOWN":
            return 0.0

        if action.action_type != "reroute_order":
            return 0.0

        order = env._find_order(action.target_id)
        if not order or order.product != env.disruption_product:
            return 0.0

        on_time_score = 1.0 if order.status == "DELIVERED" and order.expected_delivery <= order.deadline else 0.0
        budget_score = max(0.0, min(1.0, env.budget_remaining / env.initial_budget))
        return round(0.7 * on_time_score + 0.3 * budget_score, 4)


class MediumTask:
    """Medium — Cascading disruption, triage multiple products and notify customers."""

    @staticmethod
    def evaluate(env: SupplyChainEnv, action: Action) -> float:
        if env.disruption_event.event_type != "PORT_BLOCKED":
            return 0.0

        delivered_on_time = sum(1 for order in env.pending_orders if order.status == "DELIVERED" and order.expected_delivery is not None and order.expected_delivery <= order.deadline)
        notified = sum(1 for order in env.pending_orders if order.status == "LATE" and order.notified)
        score = min(1.0, 0.4 * delivered_on_time + 0.6 * (notified / max(1, len(env.pending_orders))))
        return round(score, 4)


class HardTask:
    """Hard — Negotiation and split orders under bankruptcy and fuel shock."""

    @staticmethod
    def evaluate(env: SupplyChainEnv) -> float:
        if env.disruption_event.event_type not in {"SUPPLIER_BANKRUPTCY", "FUEL_SPIKE"}:
            return 0.0

        delivered = sum(1 for order in env.pending_orders if order.status == "DELIVERED")
        penalty_cost = sum(max(0, (order.expected_delivery or env.current_day) - order.deadline) * order.penalty_per_day for order in env.pending_orders if order.status == "LATE")
        reputation = env.customer_reputation
        score = max(0.0, min(1.0, 0.5 * (delivered / max(1, len(env.pending_orders))) + 0.3 * reputation + 0.2 * (1.0 - min(1.0, penalty_cost / 1000.0))))
        return score

