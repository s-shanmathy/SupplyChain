from __future__ import annotations
import random
from typing import Dict, List, Optional, Tuple

from models import (
    Action,
    AlternativeSupplier,
    DisruptionEvent,
    Observation,
    PendingOrder,
    Reward,
    SupplierInfo,
)


class SupplyChainEnv:
    def __init__(
        self,
        scenario: str = "medium",
        random_seed: Optional[int] = None,
        max_steps: int = 30,
    ) -> None:
        self.scenario = scenario
        self.random_seed = random_seed
        self.max_steps = max_steps

        self.current_day = 0
        self.initial_budget = 10000.0
        self.budget_remaining = 10000.0
        self.supplier_network: List[SupplierInfo] = []
        self.inventory_levels: Dict[str, int] = {}
        self.pending_orders: List[PendingOrder] = []
        self.disruption_event: Optional[DisruptionEvent] = None
        self.alternative_suppliers: List[AlternativeSupplier] = []
        self.feedback = ""
        self.last_reward: Optional[Reward] = None
        self.disruption_product: Optional[str] = None
        self.fuel_surcharge = 1.0

        if random_seed is not None:
            random.seed(random_seed)

    def reset(self) -> Observation:
        self.current_day = 0
        self.budget_remaining = self.initial_budget
        self.fuel_surcharge = 1.0
        self.feedback = "Supply chain disruption started."
        self.supplier_network = self._build_supplier_network()
        self.inventory_levels = {"Widget": 120, "Gadget": 80}
        self.pending_orders = self._build_pending_orders()
        self.disruption_event = self._build_disruption_event()
        self.alternative_suppliers = self._build_alternatives()
        self.last_reward = None
        self.disruption_product = self._infer_disruption_product()
        return self._build_observation()

    def _build_supplier_network(self) -> List[SupplierInfo]:
        return [
            SupplierInfo(supplier_id="SupplierA", products={"Widget": 100, "Gadget": 50}, capacity=120, lead_time=4, unit_cost=10.0, reliability=0.9),
            SupplierInfo(supplier_id="SupplierB", products={"Widget": 80, "Gadget": 70}, capacity=110, lead_time=5, unit_cost=11.5, reliability=0.85),
            SupplierInfo(supplier_id="SupplierC", products={"Widget": 60, "Gadget": 90}, capacity=100, lead_time=3, unit_cost=12.0, reliability=0.8),
        ]

    def _build_pending_orders(self) -> List[PendingOrder]:
        if self.scenario == "easy":
            return [
                PendingOrder(order_id="O1", product="Widget", quantity=80, deadline=5, penalty_per_day=150.0, customer_id="Cust1"),
            ]
        if self.scenario == "hard":
            return [
                PendingOrder(order_id="O1", product="Widget", quantity=60, deadline=6, penalty_per_day=200.0, customer_id="CustA"),
                PendingOrder(order_id="O2", product="Gadget", quantity=40, deadline=5, penalty_per_day=180.0, customer_id="CustB"),
                PendingOrder(order_id="O3", product="Widget", quantity=30, deadline=7, penalty_per_day=220.0, customer_id="CustC"),
            ]
        return [
            PendingOrder(order_id="O1", product="Widget", quantity=70, deadline=6, penalty_per_day=150.0, customer_id="Cust1"),
            PendingOrder(order_id="O2", product="Gadget", quantity=50, deadline=7, penalty_per_day=140.0, customer_id="Cust2"),
            PendingOrder(order_id="O3", product="Widget", quantity=40, deadline=8, penalty_per_day=160.0, customer_id="Cust3"),
        ]

    def _build_disruption_event(self) -> DisruptionEvent:
        if self.scenario == "easy":
            return DisruptionEvent(
                event_type="SUPPLIER_DOWN",
                affected_entity="SupplierA",
                severity="high",
                recovery_days=5,
                active=True,
            )
        if self.scenario == "hard":
            self.fuel_surcharge = 1.4
            return DisruptionEvent(
                event_type="SUPPLIER_BANKRUPTCY",
                affected_entity="SupplierB",
                severity="critical",
                recovery_days=999,
                active=True,
            )
        return DisruptionEvent(
            event_type="PORT_BLOCKED",
            affected_entity="Port of Oakland",
            severity="medium",
            recovery_days=7,
            active=True,
        )

    def _build_alternatives(self) -> List[AlternativeSupplier]:
        if self.scenario == "hard":
            return [
                AlternativeSupplier(supplier_id="Alt1", product="Widget", lead_time=4, unit_cost=13.0, reliability=0.8, available_qty=60),
                AlternativeSupplier(supplier_id="Alt2", product="Widget", lead_time=5, unit_cost=11.0, reliability=0.7, available_qty=50),
                AlternativeSupplier(supplier_id="Alt3", product="Gadget", lead_time=3, unit_cost=15.0, reliability=0.85, available_qty=40),
                AlternativeSupplier(supplier_id="Alt4", product="Gadget", lead_time=6, unit_cost=12.5, reliability=0.75, available_qty=50),
            ]
        return [
            AlternativeSupplier(supplier_id="Alt1", product="Widget", lead_time=4, unit_cost=12.0, reliability=0.8, available_qty=100),
            AlternativeSupplier(supplier_id="Alt2", product="Gadget", lead_time=5, unit_cost=14.0, reliability=0.75, available_qty=80),
            AlternativeSupplier(supplier_id="Alt3", product="Widget", lead_time=6, unit_cost=11.5, reliability=0.7, available_qty=40),
        ]

    def _infer_disruption_product(self) -> Optional[str]:
        if self.disruption_event.event_type == "SUPPLIER_DOWN":
            return "Widget"
        if self.disruption_event.event_type == "PORT_BLOCKED":
            return "Widget"
        if self.disruption_event.event_type == "SUPPLIER_BANKRUPTCY":
            return "Widget"
        return None

    def _find_order(self, order_id: str) -> Optional[PendingOrder]:
        return next((order for order in self.pending_orders if order.order_id == order_id), None)

    def _find_alternative(self, supplier_id: str) -> Optional[AlternativeSupplier]:
        return next((alt for alt in self.alternative_suppliers if alt.supplier_id == supplier_id), None)

    def _apply_delivery_updates(self) -> None:
        for order in self.pending_orders:
            if order.status == "ASSIGNED" and order.expected_delivery is not None and self.current_day >= order.expected_delivery:
                if order.expected_delivery <= order.deadline:
                    order.status = "DELIVERED"
                else:
                    order.status = "LATE"
                self.feedback = f"Order {order.order_id} has been {'delivered' if order.status == 'DELIVERED' else 'delivered late'}."

            if order.status == "PENDING" and self.current_day > order.deadline:
                order.status = "LATE"
                self.feedback = f"Order {order.order_id} is now late."

    def _get_market_sentiment(self) -> str:
        if not self.disruption_event or not self.disruption_event.active:
            return "stable"
        if self.disruption_event.event_type in {"PORT_BLOCKED", "FUEL_SPIKE"}:
            return "volatile"
        if self.disruption_event.event_type == "SUPPLIER_BANKRUPTCY":
            return "falling"
        return "rising"

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, object]]:
        self.current_day += 1
        on_time = 0.0
        late_notified = 0.0
        late_unnotified = 0.0
        cancelled = 0.0
        negotiation_bonus = 0.0
        budget_penalty = 0.0
        waste_penalty = 0.0

        order = self._find_order(action.target_id)
        target_supplier_id = action.parameters.get("supplier_id") if isinstance(action.parameters.get("supplier_id"), str) else None

        if action.action_type == "reroute_order":
            if order and target_supplier_id:
                alt = self._find_alternative(target_supplier_id)
                if alt and alt.product == order.product and alt.available_qty >= order.quantity:
                    order.assigned_supplier = alt.supplier_id
                    order.expected_delivery = self.current_day + alt.lead_time
                    order.status = "ASSIGNED"
                    alt.available_qty -= order.quantity
                    cost = order.quantity * alt.unit_cost * self.fuel_surcharge
                    self.budget_remaining -= cost
                    self.feedback = f"Rerouted {order.order_id} to {alt.supplier_id} at ${alt.unit_cost}/unit."
                else:
                    self.feedback = "Reroute failed due to unavailable supplier or quantity."
                    waste_penalty = -0.05
            else:
                self.feedback = "Reroute requires order and supplier_id parameter."
                waste_penalty = -0.05

        elif action.action_type == "negotiate":
            if target_supplier_id:
                alt = self._find_alternative(target_supplier_id)
                if alt:
                    success_chance = alt.reliability + random.uniform(-0.2, 0.2)
                    if success_chance > 0.7:
                        alt.unit_cost = max(alt.unit_cost * 0.92, alt.unit_cost - 0.5)
                        negotiation_bonus = 0.1
                        self.feedback = f"Negotiation succeeded with {alt.supplier_id}. New cost ${alt.unit_cost:.2f}."
                    else:
                        self.feedback = f"Negotiation with {alt.supplier_id} did not improve terms."
                else:
                    self.feedback = "Negotiation failed: supplier not found."
                    waste_penalty = -0.05
            else:
                self.feedback = "Negotiation requires supplier_id parameter."
                waste_penalty = -0.05

        elif action.action_type == "split_order":
            if order and isinstance(action.parameters.get("supplier_ids"), list):
                supplier_ids = [str(s) for s in action.parameters.get("supplier_ids")][:2]
                allocations = []
                remaining = order.quantity
                for supplier_id in supplier_ids:
                    alt = self._find_alternative(supplier_id)
                    if alt and alt.product == order.product and remaining > 0:
                        qty = min(alt.available_qty, remaining)
                        allocations.append((alt, qty))
                        remaining -= qty
                if remaining == 0 and allocations:
                    order.assigned_supplier = ",".join(alt.supplier_id for alt, _ in allocations)
                    order.expected_delivery = self.current_day + max(alt.lead_time for alt, _ in allocations)
                    order.status = "ASSIGNED"
                    for alt, qty in allocations:
                        alt.available_qty -= qty
                        self.budget_remaining -= qty * alt.unit_cost * self.fuel_surcharge
                    self.feedback = f"Split {order.order_id} across {order.assigned_supplier}."
                else:
                    self.feedback = "Split order failed due to insufficient alternative capacity."
                    waste_penalty = -0.05
            else:
                self.feedback = "Split order requires supplier_ids parameter."
                waste_penalty = -0.05

        elif action.action_type == "notify_customer":
            if order:
                order.notified = True
                self.feedback = f"Customer notified for {order.order_id}."
            else:
                self.feedback = "Notify action requires valid order id."
                waste_penalty = -0.05

        elif action.action_type == "expedite":
            if order and order.assigned_supplier and order.expected_delivery is not None:
                cost = 200.0 * action.value * self.fuel_surcharge
                self.budget_remaining -= cost
                order.expected_delivery = max(order.deadline, order.expected_delivery - int(action.value))
                self.feedback = f"Expedited {order.order_id} to arrive sooner."
            else:
                self.feedback = "Expedite requires an assigned order."
                waste_penalty = -0.05

        elif action.action_type == "cancel_order":
            if order and order.status not in {"DELIVERED", "CANCELLED"}:
                order.status = "CANCELLED"
                cancelled = -0.3
                self.feedback = f"Order {order.order_id} cancelled as last resort."
            else:
                self.feedback = "Cancel action requires a pending order."
                waste_penalty = -0.05

        elif action.action_type == "query":
            if order:
                self.feedback = f"Order {order.order_id} has status {order.status} and deadline {order.deadline}."
            else:
                supplier = self._find_alternative(target_supplier_id or "")
                if supplier:
                    self.feedback = f"Supplier {supplier.supplier_id} has cost ${supplier.unit_cost}, lead time {supplier.lead_time}."
                else:
                    self.feedback = "Query did not find a matching order or supplier."
                    waste_penalty = -0.05

        else:
            self.feedback = "Unknown action."
            waste_penalty = -0.05

        self._apply_delivery_updates()

        on_time += sum(
            1.0
            for order in self.pending_orders
            if order.status == "DELIVERED" and order.expected_delivery is not None and order.expected_delivery <= order.deadline
        )
        late_notified += sum(0.6 for order in self.pending_orders if order.status == "LATE" and order.notified)
        late_unnotified += sum(0.2 for order in self.pending_orders if order.status == "LATE" and not order.notified)

        if self.budget_remaining < 0:
            budget_penalty = -0.2

        value = on_time + late_notified + late_unnotified + cancelled + negotiation_bonus + budget_penalty + waste_penalty

        reward = Reward(
            value=value,
            on_time=on_time,
            late_notified=late_notified,
            late_unnotified=late_unnotified,
            cancelled=cancelled,
            negotiation_bonus=negotiation_bonus,
            budget_penalty=budget_penalty,
            waste_penalty=waste_penalty,
        )

        self.last_reward = reward
        done = self.current_day >= self.max_steps or all(order.status in {"DELIVERED", "CANCELLED"} for order in self.pending_orders)

        observation = self._build_observation()
        info = {
            "day": self.current_day,
            "budget_remaining": self.budget_remaining,
            "disruption_event": self.disruption_event.dict() if self.disruption_event else None,
            "pending_orders": [order.dict() for order in self.pending_orders],
        }
        return observation, reward, done, info

    def state(self) -> Dict[str, object]:
        return {
            "current_day": self.current_day,
            "budget_remaining": self.budget_remaining,
            "supplier_network": [supplier.dict() for supplier in self.supplier_network],
            "inventory_levels": self.inventory_levels,
            "pending_orders": [order.dict() for order in self.pending_orders],
            "disruption_event": self.disruption_event.dict() if self.disruption_event else None,
            "alternative_suppliers": [alt.dict() for alt in self.alternative_suppliers],
            "feedback": self.feedback,
            "last_reward": self.last_reward.dict() if self.last_reward else None,
        }

    def _build_observation(self) -> Observation:
        return Observation(
            supplier_network=self.supplier_network,
            inventory_levels=self.inventory_levels,
            pending_orders=self.pending_orders,
            disruption_event=self.disruption_event,
            alternative_suppliers=self.alternative_suppliers,
            budget_remaining=self.budget_remaining,
            feedback=self.feedback,
        )

