"""
RealNotionAgent ? Notion API Integration

Capabilities:
- create_page      : Create a new page in a Notion database or as child of another page
- search_pages     : Search across Notion workspace
- update_page      : Append content blocks to an existing page
- log_mission      : Structured mission log (dedicated shortcut for Maestro)
- get_page         : Retrieve a page by ID

Requires env var: NOTION_TOKEN (Bearer token from Notion integration)
                  NOTION_DEFAULT_DATABASE_ID (optional, parent DB for new pages)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

from twisterlab.config.unified_settings import settings

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class RealNotionAgent(TwisterAgent):
    """
    Agent d'int?gration Notion pour TwisterLab.
    Refactoris? Phase 21 : Configuration centralis?e.
    """

    def __init__(self, registry=None) -> None:
        super().__init__(registry)
        self._token = settings.infra.notion_token
        self._default_db_id = settings.infra.notion_default_database_id


    @property
    def name(self) -> str:
        return "notion"

    @property
    def description(self) -> str:
        return "G?re les pages Notion pour la documentation des missions et la knowledge base"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="create_page",
                description="Cr?e une nouvelle page Notion dans une base de donn?es ou en tant qu'enfant d'une page",
                handler="handle_create_page",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("title", ParamType.STRING, "Titre de la page", required=True),
                    CapabilityParam("content", ParamType.STRING, "Contenu Markdown de la page", required=True),
                    CapabilityParam("parent_id", ParamType.STRING, "ID de la page/DB parente (utilise NOTION_DEFAULT_DATABASE_ID si vide)", required=False),
                    CapabilityParam("tags", ParamType.ARRAY, "Tags/cat?gories ? appliquer", required=False),
                ],
            ),
            AgentCapability(
                name="search_pages",
                description="Recherche dans l'espace Notion par mot-cl?",
                handler="handle_search",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("query", ParamType.STRING, "Texte de recherche", required=True),
                    CapabilityParam("limit", ParamType.INTEGER, "Nombre max de r?sultats (d?faut: 10)", required=False),
                ],
            ),
            AgentCapability(
                name="update_page",
                description="Ajoute des blocs de contenu ? une page Notion existante",
                handler="handle_update_page",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("page_id", ParamType.STRING, "ID de la page ? mettre ? jour", required=True),
                    CapabilityParam("content", ParamType.STRING, "Contenu Markdown ? ajouter", required=True),
                ],
            ),
            AgentCapability(
                name="log_mission",
                description="Cr?e une page de log structur? pour une mission Maestro (shortcut)",
                handler="handle_log_mission",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("mission_id", ParamType.STRING, "ID de la mission (ex: M-20260415-042)", required=True),
                    CapabilityParam("task", ParamType.STRING, "Description de la t?che originale", required=True),
                    CapabilityParam("status", ParamType.STRING, "Statut final de la mission", required=False),
                    CapabilityParam("findings", ParamType.ARRAY, "R?sultats / findings cl?s", required=False),
                    CapabilityParam("resolution", ParamType.STRING, "R?sum? de la r?solution", required=False),
                    CapabilityParam("agents_used", ParamType.ARRAY, "Liste des agents utilis?s", required=False),
                ],
            ),
            AgentCapability(
                name="get_page",
                description="R?cup?re les m?tadonn?es d'une page Notion par son ID",
                handler="handle_get_page",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("page_id", ParamType.STRING, "ID de la page Notion", required=True),
                ],
            ),
            AgentCapability(
                name="list_pages",
                description="R?cup?re une liste compl?te des pages (Search + Enfants directs)",
                handler="handle_list_pages",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("limit", ParamType.INTEGER, "Limite de r?sultats", required=False),
                ],
            ),
        ]

    # -------------------------------------------------------------------------
    # HANDLERS
    # -------------------------------------------------------------------------

    async def handle_create_page(
        self,
        title: str,
        content: str,
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> AgentResponse:
        """Cr?e une page Notion avec titre et contenu Markdown."""
        if not self._token:
            return AgentResponse(
                success=False,
                error="NOTION_TOKEN non configur?. Ajoutez-le dans le fichier .env."
            )

        parent = parent_id or self._default_db_id
        if not parent:
            return AgentResponse(
                success=False,
                error="Aucun parent_id fourni et NOTION_DEFAULT_DATABASE_ID non configur?."
            )

        # D?terminer si le parent est une DB ou une Page
        # Par d?faut on consid?re que c'est une Page si non sp?cifi?
        parent_type = os.getenv("NOTION_PARENT_TYPE", "page").lower()
        is_db = (parent_type == "database") if not parent_id else False

        try:
            blocks = self._markdown_to_blocks(content)
            payload = self._build_page_payload(title, parent, blocks, is_database=is_db)

            response = await self._notion_request("POST", "/pages", payload)

            page_id = response.get("id", "")
            page_url = response.get("url", "")
            logger.info(f"? [notion] Page cr??e : {title} ({page_id})")

            return AgentResponse(
                success=True,
                data={
                    "page_id": page_id,
                    "title": title,
                    "url": page_url,
                    "blocks_created": len(blocks),
                    "parent_id": parent,
                },
            )

        except Exception as e:
            logger.error(f"? [notion] create_page failed: {e}")
            return AgentResponse(success=False, error=str(e))

    async def handle_search(
        self,
        query: str,
        limit: int = 10,
    ) -> AgentResponse:
        """Recherche des pages Notion par mot-cl?."""
        if not self._token:
            return AgentResponse(success=False, error="NOTION_TOKEN non configur?.")

        try:
            payload = {
                "query": query,
                "page_size": min(limit, 100),
                "filter": {"value": "page", "property": "object"},
            }
            response = await self._notion_request("POST", "/search", payload)

            results = []
            for item in response.get("results", []):
                props = item.get("properties", {})
                # Extraire le titre selon le type de propri?t?
                title = self._extract_title(item)
                results.append({
                    "id": item.get("id"),
                    "title": title,
                    "url": item.get("url"),
                    "created_time": item.get("created_time"),
                    "last_edited_time": item.get("last_edited_time"),
                })

            logger.info(f"? [notion] Recherche '{query}' ? {len(results)} r?sultats")
            return AgentResponse(
                success=True,
                data={"results": results, "count": len(results), "query": query},
            )

        except Exception as e:
            logger.error(f"? [notion] search failed: {e}")
            return AgentResponse(success=False, error=str(e))

    async def handle_update_page(self, page_id: str, content: str) -> AgentResponse:
        """Ajoute des blocs ? une page Notion existante."""
        if not self._token:
            return AgentResponse(success=False, error="NOTION_TOKEN non configur?.")

        try:
            blocks = self._markdown_to_blocks(content)
            payload = {"children": blocks}

            await self._notion_request("PATCH", f"/blocks/{page_id}/children", payload)

            logger.info(f"? [notion] Page {page_id} mise ? jour ({len(blocks)} blocs)")
            return AgentResponse(
                success=True,
                data={"page_id": page_id, "blocks_added": len(blocks)},
            )

        except Exception as e:
            logger.error(f"? [notion] update_page failed: {e}")
            return AgentResponse(success=False, error=str(e))

    async def handle_log_mission(
        self,
        mission_id: str,
        task: str,
        status: str = "completed",
        findings: Optional[List[str]] = None,
        resolution: Optional[str] = None,
        agents_used: Optional[List[str]] = None,
    ) -> AgentResponse:
        """Cr?e une page de rapport structur? pour une mission Maestro."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        content_lines = [
            f"## 🎯 Mission : {mission_id}",
            f"",
            f"**Date** : {now}",
            f"**Statut** : {'? ' if status == 'completed' else '?? '}{status.upper()}",
            f"",
            f"## 📋 T?che Originale",
            f"{task}",
            f"",
        ]

        if agents_used:
            content_lines += [
                f"## 🤖 Agents Utilis?s",
                *[f"- {a}" for a in agents_used],
                f"",
            ]

        if findings:
            content_lines += [
                f"## 🔍 Findings",
                *[f"- {f}" for f in findings],
                f"",
            ]

        if resolution:
            content_lines += [
                f"## ? R?solution",
                f"{resolution}",
                f"",
            ]

        content_lines += [
            f"---",
            f"*G?n?r? automatiquement par TwisterLab Maestro v3.5*",
        ]

        content = "\n".join(content_lines)
        title = f"[{mission_id}] {task[:60]}{'...' if len(task) > 60 else ''}"

        return await self.handle_create_page(
            title=title,
            content=content,
            tags=["mission", "auto-generated", status],
        )

    async def handle_get_page(self, page_id: str) -> AgentResponse:
        """R?cup?re les m?tadonn?es d'une page."""
        if not self._token:
            return AgentResponse(success=False, error="NOTION_TOKEN non configur?.")

        try:
            response = await self._notion_request("GET", f"/pages/{page_id}", None)
            title = self._extract_title(response)

            return AgentResponse(
                success=True,
                data={
                    "page_id": response.get("id"),
                    "title": title,
                    "url": response.get("url"),
                    "created_time": response.get("created_time"),
                    "last_edited_time": response.get("last_edited_time"),
                    "archived": response.get("archived", False),
                },
            )

        except Exception as e:
            logger.error(f"? [notion] get_page failed: {e}")
            return AgentResponse(success=False, error=str(e))

    async def handle_list_pages(self, limit: int = 20) -> AgentResponse:
        """Combine Search et Fetch Children pour une synchro parfaite."""
        if not self._token:
            return AgentResponse(success=False, error="NOTION_TOKEN non configur?.")

        all_pages = {}

        try:
            # 1. Recherche globale (pour attraper tout ce qui est accessible)
            search_res = await self.handle_search(query="", limit=limit)
            if search_res.success:
                for p in search_res.data.get("results", []):
                    all_pages[p["id"]] = p

            # 2. Fetch direct des enfants du parent par d?faut (si c'est une page)
            if self._default_db_id:
                try:
                    # On utilise l'API blocks children car les sous-pages sont des blocs
                    response = await self._notion_request("GET", f"/blocks/{self._default_db_id}/children", None)
                    for block in response.get("results", []):
                        if block["type"] == "child_page":
                            pid = block["id"]
                            if pid not in all_pages:
                                all_pages[pid] = {
                                    "id": pid,
                                    "title": block["child_page"]["title"],
                                    "url": f"https://www.notion.so/{pid.replace('-', '')}",
                                    "created_time": block["created_time"],
                                    "last_edited_time": block["last_edited_time"],
                                    "type": "page",
                                }
                except Exception as ex:
                    logger.warning(f"?? [notion] Fallback children fetch failed: {ex}")

            # Trier par date de modif d?croissante
            sorted_pages = sorted(all_pages.values(), key=lambda x: x.get("last_edited_time", ""), reverse=True)

            return AgentResponse(
                success=True,
                data={"pages": sorted_pages[:limit], "count": len(sorted_pages)}
            )

        except Exception as e:
            logger.error(f"? [notion] list_pages failed: {e}")
            return AgentResponse(success=False, error=str(e))

    # -------------------------------------------------------------------------
    # HELPERS PRIV?S
    # -------------------------------------------------------------------------

    async def _notion_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Ex?cute une requ?te vers l'API Notion."""
        if not httpx:
            raise RuntimeError("httpx non disponible. Installez-le : pip install httpx")

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(f"{NOTION_API_BASE}{path}", headers=headers)
            elif method == "POST":
                response = await client.post(f"{NOTION_API_BASE}{path}", headers=headers, json=payload)
            elif method == "PATCH":
                response = await client.patch(f"{NOTION_API_BASE}{path}", headers=headers, json=payload)
            else:
                raise ValueError(f"M?thode HTTP non support?e : {method}")

            if response.status_code >= 400:
                error_data = response.json()
                raise RuntimeError(
                    f"Notion API Error {response.status_code}: "
                    f"{error_data.get('message', response.text)}"
                )

            return response.json()

    def _markdown_to_blocks(self, markdown: str) -> List[Dict[str, Any]]:
        """Convertit du Markdown en blocs Notion (h1/h2/h3, bullets, paragraphes)."""
        blocks = []
        lines = markdown.split("\n")

        for line in lines:
            stripped = line.strip()
            if not stripped:
                # Bloc vide ? s?parateur
                continue

            if stripped.startswith("### "):
                blocks.append(self._heading_block(stripped[4:], level=3))
            elif stripped.startswith("## "):
                blocks.append(self._heading_block(stripped[3:], level=2))
            elif stripped.startswith("# "):
                blocks.append(self._heading_block(stripped[2:], level=1))
            elif stripped.startswith("- ") or stripped.startswith("* "):
                blocks.append(self._bullet_block(stripped[2:]))
            elif stripped.startswith("> "):
                blocks.append(self._quote_block(stripped[2:]))
            elif stripped.startswith("[!] "):
                blocks.append(self._callout_block(stripped[4:]))
            elif stripped.startswith("---"):
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            else:
                blocks.append(self._paragraph_block(stripped))

        return blocks

    def _heading_block(self, text: str, level: int = 2) -> Dict[str, Any]:
        block_type = f"heading_{level}"
        return {
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }

    def _bullet_block(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def _paragraph_block(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def _quote_block(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    def _callout_block(self, text: str) -> Dict[str, Any]:
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "icon": {"emoji": "🚀"}
            },
        }

    def _build_page_payload(
        self,
        title: str,
        parent_id: str,
        blocks: List[Dict[str, Any]],
        is_database: bool = False,
    ) -> Dict[str, Any]:
        """Construit le payload de cr?ation de page Notion."""
        if is_database:
            parent = {"database_id": parent_id}
            # Pour une DB, le titre est une propri?t? "Name"
            properties = {
                "Name": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            }
        else:
            parent = {"page_id": parent_id}
            properties = {
                "title": [{"type": "text", "text": {"content": title}}]
            }

        return {
            "parent": parent,
            "properties": properties,
            "children": blocks,
        }

    def _extract_title(self, item: Dict[str, Any]) -> str:
        """Extrait le titre d'un objet Notion (page ou DB) ? g?re tous les formats API."""
        props = item.get("properties", {})

        # Format DB item : propri?t? "Name" ou "Title" de type "title"
        for key in ["Name", "title", "Title"]:
            prop = props.get(key, {})
            # Format objet complet : {"type": "title", "title": [...]}
            if isinstance(prop, dict) and prop.get("type") == "title":
                texts = prop.get("title", [])
                if texts:
                    return texts[0].get("plain_text", "Sans titre")
            # Format liste directe : [{"plain_text": "..."}]
            if isinstance(prop, list) and prop:
                return prop[0].get("plain_text", "Sans titre")

        return "Sans titre"


__all__ = ["RealNotionAgent"]
