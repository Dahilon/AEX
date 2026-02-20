"""
Market routes: agent prices, snapshot, WebSocket stream.
"""

import asyncio
import json
import logging
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()

# ── WebSocket connection manager ──────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WS client connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        logger.info(f"WS client disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


async def broadcast_tick(snapshot: dict) -> None:
    """Called by MarketEngine after each tick."""
    msg = {
        "type": "tick",
        "tick_number": snapshot["tick_number"],
        "agents": [
            {
                "id": a["id"],
                "price": a["price"],
                "price_change_pct": a["price_change_pct"],
                "inflow_velocity": a["inflow_velocity"],
                "inflow_direction": a["inflow_direction"],
            }
            for a in snapshot["agents"]
        ],
        "total_market_cap": snapshot["total_market_cap"],
        "active_shocks": len(snapshot["active_shocks"]),
        "cascade_probability": snapshot["cascade_probability"],
    }
    await manager.broadcast(msg)


# ── REST endpoints ────────────────────────────────────────────────────────────

@router.get("/agents")
async def get_agents(request: Request) -> list[dict]:
    """Returns all agents with current state."""
    return request.app.state.engine.get_agents()


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, request: Request) -> dict:
    """Returns a single agent with full details."""
    agents = request.app.state.engine.state.agents
    if agent_id not in agents:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    agent = agents[agent_id]
    detail = agent.to_dict()
    detail["price_history"] = agent.price_history
    return detail


@router.get("/snapshot")
async def get_snapshot(request: Request) -> dict:
    """Returns full market snapshot: all agents, sectors, shocks."""
    return request.app.state.engine.get_snapshot()


@router.post("/agents/{agent_id}/buy")
async def buy_agent(agent_id: str, amount: float, request: Request) -> dict:
    """Simulate a buy event (capital inflow) for an agent."""
    request.app.state.engine.simulate_buy(agent_id, amount)
    return {"status": "ok", "agent_id": agent_id, "amount": amount, "action": "buy"}


@router.post("/agents/{agent_id}/sell")
async def sell_agent(agent_id: str, amount: float, request: Request) -> dict:
    """Simulate a sell event (capital outflow) for an agent."""
    request.app.state.engine.simulate_sell(agent_id, amount)
    return {"status": "ok", "agent_id": agent_id, "amount": amount, "action": "sell"}


# ── WebSocket stream ──────────────────────────────────────────────────────────

@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """
    Real-time market price stream.
    Client receives a message every market tick (default 2s).
    Also receives shock events when they are injected.
    """
    await manager.connect(websocket)
    try:
        # Send current snapshot immediately on connect
        engine = websocket.app.state.engine  # type: ignore
        snapshot = engine.get_snapshot()
        await websocket.send_text(json.dumps({
            "type": "connected",
            "snapshot": snapshot,
        }))

        # Keep connection alive — data flows via broadcast_tick
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
