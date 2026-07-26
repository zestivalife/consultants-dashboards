# People & Access Domain Model

## Purpose

Defines the canonical business model for Identity, Authentication,
Authorisation, Organisations, Products, Workspaces, Capabilities,
Permissions and Actions.

## Pipeline

Identity → Authentication → Access Profile → Organisation → Product →
Workspace → Capability → Feature → Permission → Action

## Rules

-   Workspace access is independent of feature permissions.
-   One source of truth per business object.
-   Frontend and backend evaluate identical policies.
