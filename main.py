from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from engine import SupplyChainEnv
from models import Action, Observation

app = FastAPI(title="SupplyChainDisruptionResponse", version="0.1.0")

env = SupplyChainEnv(random_seed=42)

env.reset()


class StepRequest(BaseModel):
    action_type: str
    target_id: str
    value: float
    parameters: Dict[str, Any] = Field(default_factory=dict)


@app.get("/reset", response_model=Observation)
def reset():
    return env.reset()


@app.post("/step")
def step(request: StepRequest):
    try:
        action = Action(
            action_type=request.action_type.lower(),
            target_id=request.target_id,
            value=request.value,
            parameters=request.parameters,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state():
    return env.state()
