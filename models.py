from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class SupplierInfo(BaseModel):
    supplier_id: str = Field(...)
    products: Dict[str, int] = Field(..., description="Product capacities available from the supplier")
    capacity: int = Field(..., description="Maximum order quantity this supplier can fulfill")
    lead_time: int = Field(..., description="Lead time in days")
    unit_cost: float = Field(..., description="Cost per unit")
    reliability: float = Field(..., description="Reliability score between 0 and 1")


class PendingOrder(BaseModel):
    order_id: str = Field(...)
    product: str = Field(...)
    quantity: int = Field(...)
    deadline: int = Field(..., description="Days until due")
    penalty_per_day: float = Field(...)
    customer_id: str = Field(...)
    status: Literal["PENDING", "ASSIGNED", "DELIVERED", "LATE", "CANCELLED"] = Field("PENDING")
    assigned_supplier: Optional[str] = Field(None)
    expected_delivery: Optional[int] = Field(None)
    notified: bool = Field(False)


class DisruptionEvent(BaseModel):
    event_type: Literal["SUPPLIER_DOWN", "PORT_BLOCKED", "FACTORY_FLOODED", "SUPPLIER_BANKRUPTCY", "FUEL_SPIKE"] = Field(...)
    affected_entity: str = Field(...)
    severity: str = Field(...)
    recovery_days: int = Field(...)
    active: bool = Field(...)


class AlternativeSupplier(BaseModel):
    supplier_id: str = Field(...)
    product: str = Field(...)
    lead_time: int = Field(...)
    unit_cost: float = Field(...)
    reliability: float = Field(...)
    available_qty: int = Field(...)


class Observation(BaseModel):
    supplier_network: List[SupplierInfo] = Field(...)
    inventory_levels: Dict[str, int] = Field(...)
    pending_orders: List[PendingOrder] = Field(...)
    disruption_event: DisruptionEvent = Field(...)
    alternative_suppliers: List[AlternativeSupplier] = Field(...)
    budget_remaining: float = Field(...)
    feedback: str = Field(...)


class Action(BaseModel):
    action_type: Literal[
        "reroute_order",
        "negotiate",
        "split_order",
        "notify_customer",
        "expedite",
        "cancel_order",
        "query",
    ] = Field(...)
    target_id: str = Field(..., description="Target order or supplier identifier")
    value: float = Field(..., description="Numeric intensity of the action")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Optional additional action parameters")


class Reward(BaseModel):
    value: float = Field(...)
    on_time: float = Field(...)
    late_notified: float = Field(...)
    late_unnotified: float = Field(...)
    cancelled: float = Field(...)
    negotiation_bonus: float = Field(...)
    budget_penalty: float = Field(...)
    waste_penalty: float = Field(...)
