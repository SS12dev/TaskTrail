"""
A2A Protocol Client

Client for discovering and communicating with external A2A-compatible agents.
"""

import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from uuid import uuid4

from app.models.a2a_models import (
    AgentCard,
    A2AMessage,
    A2AResponse,
    ExternalAgent,
)
from app.config import get_settings

logger = logging.getLogger(__name__)


class A2AClientError(Exception):
    """Base exception for A2A client errors"""
    pass


class AgentDiscoveryError(A2AClientError):
    """Error during agent discovery"""
    pass


class AgentCommunicationError(A2AClientError):
    """Error during agent communication"""
    pass


class A2AClient:
    """
    Client for interacting with external A2A-compatible agents

    Features:
    - Discover agents via Agent Card
    - Send messages to external agents
    - Capability matching
    - Response handling
    """

    def __init__(self):
        self.settings = get_settings()
        self._agent_card_cache: Dict[str, tuple[AgentCard, datetime]] = {}
        self._cache_ttl = timedelta(hours=1)

    async def discover_agent(self, domain: str, force_refresh: bool = False) -> AgentCard:
        """
        Discover an agent by fetching its Agent Card

        Args:
            domain: Agent's domain (e.g., "agent.example.com")
            force_refresh: Force refresh cached Agent Card

        Returns:
            AgentCard from the agent

        Raises:
            AgentDiscoveryError: If discovery fails
        """
        # Check cache
        if not force_refresh and domain in self._agent_card_cache:
            card, cached_at = self._agent_card_cache[domain]
            if datetime.utcnow() - cached_at < self._cache_ttl:
                logger.info(f"Using cached Agent Card for {domain}")
                return card

        # Fetch Agent Card
        discovery_url = f"https://{domain}/.well-known/agent-card.json"
        logger.info(f"Discovering agent at {discovery_url}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(discovery_url)
                response.raise_for_status()

                agent_card_data = response.json()
                agent_card = AgentCard(**agent_card_data)

                # Cache the result
                self._agent_card_cache[domain] = (agent_card, datetime.utcnow())

                logger.info(
                    f"Discovered agent: {agent_card.name} ({agent_card.agentId})"
                )

                return agent_card

        except httpx.HTTPError as e:
            logger.error(f"Failed to discover agent at {domain}: {e}")
            raise AgentDiscoveryError(f"Failed to discover agent at {domain}: {e}")
        except Exception as e:
            logger.error(f"Error parsing Agent Card from {domain}: {e}")
            raise AgentDiscoveryError(f"Error parsing Agent Card: {e}")

    async def send_message(
        self,
        agent_card: AgentCard,
        message: A2AMessage,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> A2AResponse:
        """
        Send an A2A message to an external agent

        Args:
            agent_card: Target agent's Agent Card
            message: A2A message to send
            auth_token: Optional bearer token for authentication
            api_key: Optional API key for authentication

        Returns:
            A2A response from the agent

        Raises:
            AgentCommunicationError: If communication fails
        """
        endpoint = f"{agent_card.serviceEndpoint}/messages"
        logger.info(
            f"Sending message to {agent_card.name} at {endpoint} "
            f"(contextId: {message.contextId})"
        )

        # Build headers
        headers = {
            "Content-Type": "application/json",
        }

        # Add authentication
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        elif api_key:
            # Check Agent Card for API key header name
            api_key_scheme = agent_card.securitySchemes.get("apiKey")
            if api_key_scheme and api_key_scheme.name:
                headers[api_key_scheme.name] = api_key
            else:
                headers["X-API-Key"] = api_key

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    json=message.model_dump(),
                    headers=headers,
                )
                response.raise_for_status()

                response_data = response.json()
                a2a_response = A2AResponse(**response_data)

                logger.info(
                    f"Received response from {agent_card.name} - "
                    f"taskState: {a2a_response.taskState}"
                )

                return a2a_response

        except httpx.HTTPError as e:
            logger.error(f"Failed to communicate with {agent_card.name}: {e}")
            raise AgentCommunicationError(
                f"Failed to communicate with {agent_card.name}: {e}"
            )
        except Exception as e:
            logger.error(f"Error processing response from {agent_card.name}: {e}")
            raise AgentCommunicationError(f"Error processing response: {e}")

    def find_agents_with_capability(
        self,
        agent_cards: List[AgentCard],
        capability_id: str,
    ) -> List[AgentCard]:
        """
        Find agents that support a specific capability

        Args:
            agent_cards: List of Agent Cards to search
            capability_id: Capability ID to match

        Returns:
            List of matching Agent Cards
        """
        matching_agents = []

        for card in agent_cards:
            if any(cap.id == capability_id for cap in card.capabilities):
                matching_agents.append(card)

        return matching_agents

    def find_best_agent_for_task(
        self,
        agent_cards: List[AgentCard],
        task_description: str,
        required_capabilities: Optional[List[str]] = None,
    ) -> Optional[AgentCard]:
        """
        Find the best agent for a task based on capabilities

        Simple heuristic matching - can be enhanced with semantic search

        Args:
            agent_cards: Available Agent Cards
            task_description: Task description
            required_capabilities: Optional list of required capability IDs

        Returns:
            Best matching Agent Card or None
        """
        if not agent_cards:
            return None

        # If required capabilities specified, filter by them
        if required_capabilities:
            candidates = []
            for card in agent_cards:
                card_capabilities = {cap.id for cap in card.capabilities}
                if all(req in card_capabilities for req in required_capabilities):
                    candidates.append(card)

            if not candidates:
                logger.warning(
                    f"No agents found with required capabilities: {required_capabilities}"
                )
                return None

            agent_cards = candidates

        # Simple scoring based on description matching
        task_lower = task_description.lower()
        scored_agents = []

        for card in agent_cards:
            score = 0

            # Check agent description
            if any(word in card.description.lower() for word in task_lower.split()):
                score += 1

            # Check capability descriptions
            for capability in card.capabilities:
                if any(
                    word in capability.description.lower()
                    for word in task_lower.split()
                ):
                    score += 2

                # Check examples
                if capability.examples:
                    for example in capability.examples:
                        if any(
                            word in example.lower() for word in task_lower.split()
                        ):
                            score += 1

            scored_agents.append((card, score))

        # Sort by score and return best
        scored_agents.sort(key=lambda x: x[1], reverse=True)

        if scored_agents and scored_agents[0][1] > 0:
            best_agent = scored_agents[0][0]
            logger.info(
                f"Selected agent {best_agent.name} for task (score: {scored_agents[0][1]})"
            )
            return best_agent

        # If no good match, return first agent as fallback
        logger.warning("No strong match found, returning first available agent")
        return agent_cards[0] if agent_cards else None

    async def load_external_agents(self) -> List[AgentCard]:
        """
        Load external agents from configuration

        Returns:
            List of discovered Agent Cards
        """
        if not self.settings.external_agents:
            logger.info("No external agents configured")
            return []

        # Parse comma-separated agent URLs
        agent_urls = [
            url.strip()
            for url in self.settings.external_agents.split(",")
            if url.strip()
        ]

        agent_cards = []

        for url in agent_urls:
            try:
                # Extract domain from URL
                domain = url.replace("https://", "").replace("http://", "").split("/")[0]
                agent_card = await self.discover_agent(domain)
                agent_cards.append(agent_card)
            except AgentDiscoveryError as e:
                logger.error(f"Failed to load external agent from {url}: {e}")
                continue

        logger.info(f"Loaded {len(agent_cards)} external agents")
        return agent_cards

    def create_a2a_message(
        self,
        text_content: str,
        context_id: str,
        task_id: Optional[str] = None,
        role: str = "user",
        structured_data: Optional[Dict[str, Any]] = None,
    ) -> A2AMessage:
        """
        Create an A2A message from text content

        Args:
            text_content: Message text
            context_id: Context identifier
            task_id: Optional task identifier
            role: Message role (default: "user")
            structured_data: Optional structured data to include

        Returns:
            A2A message ready to send
        """
        parts = [{"text": text_content}]

        if structured_data:
            parts.append({"data": structured_data})

        return A2AMessage(
            messageId=f"msg-{uuid4()}",
            contextId=context_id,
            taskId=task_id,
            role=role,
            parts=parts,
            timestamp=datetime.utcnow(),
        )


# Singleton instance
_client_instance: Optional[A2AClient] = None


def get_a2a_client() -> A2AClient:
    """
    Get singleton A2A client instance

    Returns:
        A2A client instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = A2AClient()
    return _client_instance
