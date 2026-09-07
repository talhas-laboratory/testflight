"""Provider-neutral, child-first routing for related knowledge containers."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContainerStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class KnowledgeContainer(BaseModel):
    """A canonical knowledge boundary; generated indexes are deliberately absent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: str = Field(min_length=1)
    route: str = Field(min_length=1)
    dataset_name: str = Field(min_length=1)
    parent_workspace_id: str | None = None
    owns_entity_ids: tuple[str, ...] = ()
    augments_entity_ids: tuple[str, ...] = ()
    status: ContainerStatus = ContainerStatus.DRAFT

    @model_validator(mode="after")
    def require_disjoint_ownership_lists(self) -> "KnowledgeContainer":
        if set(self.owns_entity_ids) & set(self.augments_entity_ids):
            raise ValueError("container cannot own and augment the same entity")
        return self


class FederationBridge(BaseModel):
    """An auditable, explicit permission to supplement one container from another."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bridge_id: str = Field(min_length=1)
    source_workspace_id: str = Field(min_length=1)
    target_workspace_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    predicate_id: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()
    allow_traversal: bool = False
    authority_grant_id: str | None = None


class FederationPlanStatus(StrEnum):
    HIT = "hit"
    NO_HIT = "no_hit"
    HOLD = "hold"


class FederationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: FederationPlanStatus
    primary_workspace_id: str | None = None
    supplemental_workspace_ids: tuple[str, ...] = ()
    route_rationale: tuple[str, ...] = ()
    omissions: tuple[str, ...] = ()


class FederationRegistry(BaseModel):
    """Registry and deterministic planner for a family of isolated containers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    containers: tuple[KnowledgeContainer, ...]
    bridges: tuple[FederationBridge, ...] = ()

    @model_validator(mode="after")
    def validate_references(self) -> "FederationRegistry":
        container_ids = {container.workspace_id for container in self.containers}
        if len(container_ids) != len(self.containers):
            raise ValueError("FederationRegistry contains duplicate workspace IDs")
        for container in self.containers:
            if container.parent_workspace_id and container.parent_workspace_id not in container_ids:
                raise ValueError("container parent_workspace_id is unknown")
        for bridge in self.bridges:
            if bridge.source_workspace_id not in container_ids:
                raise ValueError("bridge source workspace is unknown")
            if bridge.target_workspace_id not in container_ids:
                raise ValueError("bridge target workspace is unknown")
        return self

    def container(self, workspace_id: str) -> KnowledgeContainer:
        for container in self.containers:
            if container.workspace_id == workspace_id:
                return container
        raise KeyError(workspace_id)

    def is_descendant_of(self, workspace_id: str, ancestor_workspace_id: str) -> bool:
        current = self.container(workspace_id)
        visited: set[str] = set()
        while current.parent_workspace_id:
            if current.workspace_id in visited:
                raise ValueError("container hierarchy contains a cycle")
            visited.add(current.workspace_id)
            if current.parent_workspace_id == ancestor_workspace_id:
                return True
            current = self.container(current.parent_workspace_id)
        return False

    def depth(self, workspace_id: str) -> int:
        depth = 0
        current = self.container(workspace_id)
        visited: set[str] = set()
        while current.parent_workspace_id:
            if current.workspace_id in visited:
                raise ValueError("container hierarchy contains a cycle")
            visited.add(current.workspace_id)
            depth += 1
            current = self.container(current.parent_workspace_id)
        return depth

    def plan_child_first(
        self,
        *,
        root_workspace_id: str,
        entity_ids: tuple[str, ...] = (),
        route_hint: str | None = None,
        permitted_workspace_ids: frozenset[str] | None = None,
    ) -> FederationPlan:
        """Choose one smallest matching container and only explicit supplements.

        This method plans routing. It does not retrieve evidence and must not
        treat an empty child result as permission to search a whole parent.
        """

        self.container(root_workspace_id)
        permitted = permitted_workspace_ids or frozenset(
            container.workspace_id for container in self.containers
        )
        if root_workspace_id not in permitted:
            return FederationPlan(
                status=FederationPlanStatus.HOLD,
                omissions=("root workspace is not permitted",),
            )
        candidates = [
            container
            for container in self.containers
            if container.workspace_id in permitted
            and (
                container.workspace_id == root_workspace_id
                or self.is_descendant_of(container.workspace_id, root_workspace_id)
            )
        ]
        exact = [
            container
            for container in candidates
            if any(
                entity_id in {*container.owns_entity_ids, *container.augments_entity_ids}
                for entity_id in entity_ids
            )
        ]
        route_matches = [
            container
            for container in candidates
            if route_hint
            and (route_hint == container.route or route_hint.startswith(f"{container.route}/"))
        ]
        selected = sorted(exact or route_matches, key=lambda item: self.depth(item.workspace_id))
        if not selected:
            return FederationPlan(
                status=FederationPlanStatus.NO_HIT,
                omissions=("no permitted child container matches the requested entity or route",),
            )
        primary = selected[-1]
        supplements = tuple(
            bridge.target_workspace_id
            for bridge in self.bridges
            if bridge.source_workspace_id == primary.workspace_id
            and bridge.allow_traversal
            and bridge.target_workspace_id in permitted
            and (
                not entity_ids or bridge.subject_id in entity_ids or bridge.object_id in entity_ids
            )
        )
        return FederationPlan(
            status=FederationPlanStatus.HIT,
            primary_workspace_id=primary.workspace_id,
            supplemental_workspace_ids=tuple(dict.fromkeys(supplements)),
            route_rationale=(
                "selected the deepest permitted child matching a requested entity or route",
                "supplemental workspaces require an explicit traversable bridge",
            ),
        )


__all__ = [
    "ContainerStatus",
    "FederationBridge",
    "FederationPlan",
    "FederationPlanStatus",
    "FederationRegistry",
    "KnowledgeContainer",
]
