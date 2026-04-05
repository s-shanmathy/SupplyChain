<<<<<<< HEAD
# Supply Chain Disruption Response (OpenEnv)

A real-world-inspired OpenEnv environment for supply chain logistics and disruption response. The agent acts as a Lead Logistics Provider managing a supplier network, customer orders, and alternate sourcing choices under unpredictable market shocks.

## Scenario

- The environment starts with a disruption: supplier downtime, port blockage, bankruptcy, or fuel shock.
- The agent must fulfill customer orders while balancing budget, delivery deadlines, alternate supplier capacity, and reputation.
- Observations include supplier network capabilities, pending order status, alternative sourcing options, budgets, and feedback signals.

## Features

- OpenEnv-compliant `SupplyChainEnv` with `reset()`, `step()`, `state()`
- Strong type-safety via Pydantic models in `models.py`
- Rich observation space with supplier network, pending order status, and alternate sourcing details
- Dense reward shaped by delivery performance, budget discipline, negotiation, and reputation
- 7 action types for strategic disruption response decisions
- 3 grader tasks with easy → medium → hard difficulty progression
- FastAPI web service compatible with Hugging Face Spaces
- Docker validation script for quick integration testing

## Action Space

- `action_type`: `reroute_order`, `negotiate`, `split_order`, `notify_customer`, `expedite`, `cancel_order`, `query`
- `target_id`: order or supplier identifier, e.g. `O1` or `Alt1`
- `value`: numeric intensity for the action
- `parameters`: optional metadata such as `supplier_id` or `supplier_ids`

## Observation Space

- `supplier_network`: available suppliers, capacity, cost, reliability, and lead time
- `inventory_levels`: current stock for `Widget` and `Gadget`
- `pending_orders`: customer orders with deadlines, penalty rates, assigned supplier, and delivery status
- `disruption_event`: active disruption type, severity, recovery timeline, and affected entity
- `alternative_suppliers`: backup source options for rerouting and split ordering
- `budget_remaining`: current cash available for sourcing, expedited delivery, and negotiation
- `feedback`: operational summary and customer communication status

## Reward Structure

- `value`: dense trajectory reward
- `on_time_deliveries`: positive signal for deliveries meeting due dates
- `budget_spent`: cost pressure penalty
- `carbon_penalty`: environmental impact penalty
- `pending_penalty`: overdue shipment penalty
- `offset_benefit`: credit offset reward
- `resilience_delta`: reward for strengthening the supply chain
- `reputation_delta`: reward for improving customer reputation

## Novel Features

- **Supplier Network Resilience**: manage alternate providers, negotiations, and split sourcing
- **Customer Communication**: notify customers proactively for late or at-risk orders
- **Dynamic Disruption Types**: support supplier outages, port blockages, bankruptcy, and fuel shocks
- **Compound action space**: route changes, negotiation, split sourcing, expedited delivery, cancellation, and intelligence queries
- **Budget and penalty balancing**: trade cost, delay, and reputational outcomes
- **Docker validation script**: `docker-test.sh` builds, runs, queries endpoints, and cleans up

## Setup

```bash
git clone <this-repo> .
cd d:/supply_chain_openenv
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

## Run baseline

```bash
python baseline.py
```

## Run as API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker validation

```bash
chmod +x docker-test.sh
./docker-test.sh
```

## OpenEnv metadata

- `openenv.yaml` contains environment metadata and action/observation schema

## Task grader usage

### Task summaries

- `EasyTask`: handle a single supplier outage by rerouting a disrupted order to meet its deadline while conserving budget.
- `MediumTask`: manage a port blockage with multiple orders, notify affected customers for late shipments, and preserve on-time service.
- `HardTask`: survive supplier bankruptcy or fuel shock through negotiation, split sourcing, and minimizing late penalties.


```python
from tasks import EasyTask, MediumTask, HardTask
from engine import SupplyChainEnv
from models import Action

env = SupplyChainEnv(random_seed=42)
obs = env.reset()
action = Action(action_type='reroute_order', target_id='O1', value=1.0, parameters={'supplier_id': 'Alt1'})
obs, reward, done, info = env.step(action)

print('easy', EasyTask.evaluate(env, action))
print('medium', MediumTask.evaluate(env, action))
print('hard', HardTask.evaluate(env))
```
=======
# SuppleChain
>>>>>>> 55e89601e7cad36de4f68a1cee21aee6e0e51849
