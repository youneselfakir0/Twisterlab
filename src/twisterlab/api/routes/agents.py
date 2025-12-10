from fastapi import APIRouter, Depends, HTTPException, Response

from twisterlab.api.schemas.index import AgentCreate, AgentResponse, AgentUpdate
from twisterlab.api.dependencies import get_agent_repo
from twisterlab.storage.base import AgentRepo

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(agent: AgentCreate, repo: AgentRepo = Depends(get_agent_repo)):
    # Avoid creating duplicate agent with the same name - best-effort check for SQL backend
    if hasattr(repo, "list_agents"):
        existing_list = await repo.list_agents(
            partition_key=agent.tenantId or "default"
        )
        for existing in existing_list:
            if existing.get("name") == agent.name:
                raise HTTPException(status_code=400, detail="Agent already exists")
    agent_dict = agent.model_dump()
    created = await repo.create_agent(agent_dict)
    return created


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    tenantId: str | None = None,
    repo: AgentRepo = Depends(get_agent_repo),
):
    agent_obj = await repo.get_agent(agent_id, partition_key=tenantId)
    if not agent_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_obj


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    tenantId: str | None = None,
    repo: AgentRepo = Depends(get_agent_repo),
):
    patch = {k: v for k, v in agent_update.model_dump().items() if v is not None}
    agent_obj = await repo.update_agent(agent_id, partition_key=tenantId, patch=patch)
    if not agent_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_obj


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    tenantId: str | None = None,
    repo: AgentRepo = Depends(get_agent_repo),
):
    success = await repo.delete_agent(agent_id, partition_key=tenantId)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return Response(status_code=204)


@router.get("/", response_model=list[AgentResponse])
async def list_agents(
    tenantId: str | None = None, repo: AgentRepo = Depends(get_agent_repo)
):
    return await repo.list_agents(partition_key=tenantId or "default")
