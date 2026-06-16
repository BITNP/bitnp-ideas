# BITNP IDEAS 设计与实现计划书 v1

## 0. 文档目的

本文档用于指导实现 **BITNP IDEAS** 项目。

本文面向实现型 AI、开发者或工程代理，目标是提供足够明确的系统目标、架构边界、功能范围、数据模型、权限规则、API 设计、前后端工程约束和部署要求，使其可以据此分阶段实现系统。

------

# 1. 项目名称与定位

## 1.1 项目名称

```text
BITNP IDEAS
```

完整名称：

```text
BITNP IDEAS — Idea-Driven Execution Administration System
```

中文名称：

```text
BITNP 点子驱动的执行管理系统
```

------

## 1.2 命名含义

BITNP IDEAS 中：

- **BITNP**：组织名，表示该系统隶属于 BITNP 内部工程体系。
- **IDEAS**：系统名称，同时保留 “ideas / 点子” 的自然语义。
- **Idea-Driven**：系统入口来自点子、灵感、需求、提案或改进建议。
- **Execution**：系统目标不是单纯记录点子，而是推动项目和任务实际落地。
- **Administration**：系统负责执行过程中的权限、成员、进度、活动流和审计管理。
- **System**：系统不是单一页面，而是完整内部服务。

------

## 1.3 一句话介绍

**BITNP IDEAS 是一个面向组织内部的点子驱动执行管理系统，用于将点子转化为项目，并通过任务管理、甘特图排期、活动流和审计日志保证执行过程可管理、可追踪、可审计。**

------

## 1.4 系统核心链路

```text
Idea → Project → Task → Execution → Activity / Audit
```

系统的核心不是“单纯的点子库”，也不是“普通项目管理工具”，而是：

```text
从点子产生，到项目化推进，再到任务执行和过程审计的完整内部管理闭环。
```

------

# 2. 最终目的

BITNP IDEAS 的最终目的包括：

## 2.1 沉淀点子

系统应允许用户将想法、需求、改进建议、项目构想沉淀为结构化 idea。

idea 需要支持：

- 标题
- 描述
- 状态
- tag
- 创建人
- 关联项目
- 关联外部链接
- 状态历史

------

## 2.2 推动执行

idea 不应停留在记录层面。

系统需要支持将 idea 推进到项目，并进一步拆解为任务：

```text
Idea → Project → Task
```

项目和任务需要支持：

- 项目成员管理
- 任务拆解
- 任务执行人
- 任务起止时间
- 任务进度
- 甘特图排期
- 任务依赖关系
- 项目活动流

------

## 2.3 管理执行过程

系统需要清晰记录：

- 谁创建了项目
- 谁加入了项目
- 谁修改了任务
- 谁调整了甘特图
- 谁变更了执行人
- 谁推动 idea 状态变化

因此系统必须同时具备：

- Activity Stream：面向用户和项目管理者可见的行为流
- Audit Log：面向系统审计的不可变日志

------

## 2.4 安全接入 AI 工作流

系统需要允许 AI workflow 或外部自动化系统通过 API Key 接入点子库。

但第一版必须限制 API Key 权限：

```text
API Key 只能接入 Idea 系统，不允许操作 Project / Task / RBAC。
```

这样可以允许 AI 辅助收集和更新 idea，同时避免 AI 直接影响项目执行计划。

------

# 3. 整体设计思路

## 3.1 系统不是 Jira Clone

BITNP IDEAS 不应试图完整复刻 Jira、ClickUp、Linear、Asana 等成熟项目管理系统。

第一版重点是建立：

- idea intake
- idea tagging
- idea 状态流转
- idea 到 project 的推进关系
- project 到 task 的执行关系
- 甘特图排期
- developer 操作审计
- API Key 安全接入
- SSO 用户身份体系

------

## 3.2 系统分为四层

```text
Idea Layer
Project Layer
Task Layer
Governance Layer
```

------

### 3.2.1 Idea Layer

负责点子沉淀、分类、筛选和推进。

包括：

- idea CRUD
- idea status
- idea tags
- idea status history
- idea-project link
- API Key idea ingestion

------

### 3.2.2 Project Layer

负责将有价值的 idea 纳入项目容器。

包括：

- project CRUD
- project members
- project dashboard
- linked ideas
- external links
- activity stream

------

### 3.2.3 Task Layer

负责项目执行。

包括：

- task CRUD
- assignee
- task status
- task progress
- task start/end date
- task dependency
- gantt chart
- drag scheduling
- dependency drag line

------

### 3.2.4 Governance Layer

负责身份、权限、审计和接入边界。

包括：

- OIDC SSO
- global RBAC
- API Key HMAC signature
- audit log
- activity stream
- developer 操作可见性

------

# 4. 技术栈约束

## 4.1 后端

使用：

```text
Python 3.12+
FastAPI
SQLAlchemy 2.0
Alembic
PostgreSQL
Pydantic v2
uv
Ruff
pytest
```

后端选择 FastAPI 的原因：

- API-first
- 适合 OpenAPI 驱动前端开发
- 与 Pydantic v2 配合较好
- 适合实现自定义 OIDC、API Key、HMAC 签名和 RBAC 逻辑

------

## 4.2 前端

使用：

```text
Vue 3
TypeScript
Vuetify 4
Pinia
Vue Router
Vite
pnpm
```

前端要求：

- 支持 light / dark theme
- 不强制 i18n
- 不强制 a11y
- UI 风格参考成熟项目管理工具
- 甘特图必须直观、可拖拽、可切换执行人

------

## 4.3 数据库

使用：

```text
PostgreSQL
```

原因：

- 支持 JSONB
- 支持强约束
- 支持复杂索引
- 适合 activity / audit / external link metadata
- SQLAlchemy + Alembic 支持成熟

------

# 5. 仓库结构与命名空间

## 5.1 仓库形态

建议使用 monorepo。

```text
bitnp-ideas/
  apps/
    backend/
    frontend/
  packages/
    shared-types/
    eslint-config/
    commitlint-config/
  tools/
    scripts/
  docs/
```

------

## 5.2 后端包命名

后端 Python 包使用：

```text
bitnp_ideas
```

理由：

- 与项目和组织命名保持一致
- 避免和通用 `ideas` 模块冲突
- 未来如需发布为内部 Python 包，不需要再次迁移命名空间
- 保留完整项目语义

推荐结构：

```text
apps/backend/
  bitnp_ideas/
    api/
    core/
    db/
    models/
    schemas/
    services/
    repositories/
    security/
    integrations/
    workers/
    main.py
```

内部应用代码与未来包发布统一使用：

```text
bitnp_ideas
```

## 5.3 数据库表命名

数据库表建议使用普通业务名，不加过长前缀：

```text
users
ideas
idea_tags
idea_tag_links
projects
project_tasks
task_dependencies
activity_stream
audit_logs
api_keys
external_links
```

如果部署环境中多个系统共用同一个数据库 schema，可以使用 schema 隔离：

```sql
CREATE SCHEMA bitnp_ideas;
```

优先推荐：

```text
PostgreSQL schema: bitnp_ideas
table: bitnp_ideas.ideas
```

而不是把所有表写成：

```text
bitnp_ideas_ideas
bitnp_ideas_projects
```

------

## 5.4 API 路径命名

前端、网关和反向代理层推荐使用带版本号路径：

```text
/api/v1/ideas
/api/v1/projects
/api/v1/tasks
/api/v1/api-keys
```

不建议所有 API 都加 `bitnp_ideas_` 前缀。

后端 FastAPI 应用内部不挂载 `/api/v1` 前缀，实际注册路由为：

```text
/ideas
/projects
/tasks
/api-keys
```

版本前缀由部署层负责：

- 开发环境：Vite proxy 将 `/api/v1/*` 转发为后端 `/*`。
- 部署环境：nginx 将 `/api/v1/*` 转发为后端 `/*`。

这样前端代码仍然可以通过版本化端点区分 API 代际，后端应用保持无环境耦合的路由定义。

------

# 6. 核心系统边界

## 6.1 API Key 边界

第一版 API Key 仅允许接入点子库。

允许：

```text
ideas:read
ideas:write
```

不允许：

```text
projects:read
projects:write
tasks:read
tasks:write
rbac:write
```

系统内部需要保留扩展空间，但不得在第一版开放 project/task API Key 权限。

------

## 6.2 任务依赖边界

任务依赖只能发生在同一个 project 内。

禁止：

```text
Project A Task 1 → Project B Task 2
```

原因：

- 降低调度复杂度
- 避免跨项目拖拽和权限混乱
- 避免 activity stream 和 audit attribution 复杂化
- 第一版保持强边界

------

## 6.3 RBAC 边界

RBAC 是全局角色，不做项目级 role。

角色：

```text
superuser
administrator
developer
```

项目成员关系不是角色系统，只用于判断：

- developer 是否参与项目
- developer 是否可以操作项目任务
- 可分配任务的人员范围
- activity stream 展示范围

------

## 6.4 SSO 边界

SSO 使用 OIDC 标准协议。

具体接入：

```text
https://github.com/BITNP/keycloak-account-service
```

系统应通过 OIDC adapter 接入，不应把 Keycloak 具体实现散落在业务逻辑中。

------

# 7. 功能概述

## 7.1 用户系统

支持：

- OIDC SSO 登录
- 用户资料同步
- 用户角色管理
- 用户启用 / 禁用
- 初始化 superuser
- administrator 由 superuser 任命

------

## 7.2 点子库

支持：

- 创建 idea
- 编辑 idea
- 删除 / 归档 idea
- idea 状态流转
- idea tag 多对多关联
- idea tag 筛选
- idea 关联 project
- idea 关联外部 project URL
- idea 状态历史
- API Key 接入 idea
- HMAC 签名校验

------

## 7.3 Tag 功能

点子库必须支持 tag。

Tag 要求：

- tag 与 idea 是多对多关系
- 一个 idea 可以有多个 tag
- 一个 tag 可以关联多个 idea
- tag 名称唯一
- tag 支持颜色
- tag 支持描述
- tag 支持启用 / 禁用
- tag 支持按使用频率排序
- idea 列表支持按 tag 筛选
- idea 详情页支持添加 / 删除 tag
- API Key 创建 idea 时允许附带 tags

------

## 7.4 项目管理

支持：

- 创建项目
- 编辑项目
- 项目归档
- 项目成员管理
- 项目 dashboard
- 项目状态
- 项目关联 ideas
- 项目 external links
- 项目 activity stream

仅 administrator / superuser 可以：

- 创建项目
- 管理项目
- 添加 / 移除项目成员

developer 可以：

- 查看自己参与的项目
- 参与项目任务管理
- 调整参与项目的甘特图
- 其所有操作必须进入 audit log 和 project activity stream

------

## 7.5 任务管理

支持：

- 创建任务
- 编辑任务
- 删除 / 归档任务
- 任务状态
- 任务执行人
- 任务起止日期
- 任务进度
- 任务父子关系
- 任务依赖关系
- optimistic lock

------

## 7.6 甘特图

必须支持：

- 任务条展示
- 拖动任务条调整开始 / 结束日期
- resize 任务条调整工期
- 拖拽依赖线创建任务依赖
- 删除依赖线
- 切换执行人
- 修改进度
- 按日 / 周 / 月查看
- 后端 cycle detection
- 禁止跨 project dependency

------

## 7.7 Activity Stream

Project dashboard 必须展示项目活动流。

Activity Stream 用于展示：

- 谁修改了任务
- 谁调整了任务时间
- 谁切换了执行人
- 谁新增了任务依赖
- 谁删除了任务依赖
- 谁关联了 idea
- 谁添加了项目成员

Activity Stream 是给用户看的。

------

## 7.8 Audit Log

Audit Log 是系统级不可变日志。

用于记录：

- role 变化
- project 创建 / 修改 / 归档
- project member 变化
- task 创建 / 修改 / 删除
- gantt 时间调整
- dependency 创建 / 删除
- idea 状态变化
- API Key 创建 / 禁用 / 轮换
- API Key 签名失败

Audit Log 不等同于 Activity Stream。

------

## 7.9 外部链接

支持给以下实体添加外部链接：

```text
idea
project
task
```

链接支持：

- GitHub repo
- 普通网址
- 文档链接
- 其他 URL

可选增强：

- Open Graph 解析
- GitHub repo 特殊解析
- 解析失败不阻塞保存

------

# 8. 权限模型

## 8.1 角色定义

### superuser

最高权限。

可以：

- 任命 administrator
- 撤销 administrator
- 管理所有用户
- 管理所有项目
- 查看所有 audit log
- 禁用 API Key

------

### administrator

项目管理者。

可以：

- 创建项目
- 编辑项目
- 添加项目成员
- 移除项目成员
- 查看项目 dashboard
- 查看项目 activity stream
- 管理项目任务
- 管理点子状态

不可以：

- 任命 administrator
- 修改 superuser
- 删除 superuser

------

### developer

普通开发者 / 执行者。

可以：

- 创建 idea
- 编辑自己的 idea
- 给 idea 添加 tag
- 查看自己参与的项目
- 管理自己参与项目中的任务
- 调整自己参与项目的甘特图
- 修改项目任务执行人，但目标执行人必须是项目成员

限制：

- 不能创建项目
- 不能添加 / 移除项目成员
- 不能任命角色
- 不能操作未参与项目
- 所有项目相关操作必须进入 activity stream 和 audit log

------

## 8.2 权限矩阵

| 操作               | developer                    | administrator | superuser |
| ------------------ | ---------------------------- | ------------- | --------- |
| 登录系统           | 是                           | 是            | 是        |
| 查看 idea          | 是                           | 是            | 是        |
| 创建 idea          | 是                           | 是            | 是        |
| 编辑自己的 idea    | 是                           | 是            | 是        |
| 管理所有 idea      | 否                           | 是            | 是        |
| 创建 / 管理 tag    | 可使用，管理受限             | 是            | 是        |
| 创建 API Key       | 是                           | 是            | 是        |
| 创建项目           | 否                           | 是            | 是        |
| 编辑项目           | 限参与项目任务，不含项目设置 | 是            | 是        |
| 管理项目成员       | 否                           | 是            | 是        |
| 查看参与项目       | 是                           | 是            | 是        |
| 查看所有项目       | 否                           | 是            | 是        |
| 创建任务           | 限参与项目                   | 是            | 是        |
| 编辑任务           | 限参与项目                   | 是            | 是        |
| 调整甘特图         | 限参与项目                   | 是            | 是        |
| 创建任务依赖       | 限参与项目                   | 是            | 是        |
| 任命 administrator | 否                           | 否            | 是        |
| 查看 audit log     | 否                           | 可按范围      | 是        |

------

# 9. 数据模型设计

## 9.1 users

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  sso_provider TEXT NOT NULL,
  sso_subject TEXT NOT NULL,
  email TEXT NOT NULL,
  display_name TEXT NOT NULL,
  avatar_url TEXT,
  global_role TEXT NOT NULL CHECK (global_role IN ('superuser', 'administrator', 'developer')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE (sso_provider, sso_subject)
);
```

------

## 9.2 ideas

```sql
CREATE TABLE ideas (
  id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'in_progress', 'completed')),
  creator_id UUID NOT NULL REFERENCES users(id),
  linked_project_id UUID,
  linked_project_url TEXT,
  priority TEXT CHECK (priority IN ('low', 'medium', 'high')),
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

业务约束：

```text
status in ('in_progress', 'completed') 时，linked_project_id 或 linked_project_url 必须至少存在一个。
```

------

## 9.3 idea_tags

```sql
CREATE TABLE idea_tags (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  color TEXT,
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

------

## 9.4 idea_tag_links

```sql
CREATE TABLE idea_tag_links (
  idea_id UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES idea_tags(id) ON DELETE CASCADE,
  added_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (idea_id, tag_id)
);
```

索引建议：

```sql
CREATE INDEX idx_idea_tag_links_tag_id ON idea_tag_links(tag_id);
CREATE INDEX idx_idea_tag_links_idea_id ON idea_tag_links(idea_id);
```

------

## 9.5 idea_status_history

```sql
CREATE TABLE idea_status_history (
  id UUID PRIMARY KEY,
  idea_id UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
  from_status TEXT,
  to_status TEXT NOT NULL,
  actor_id UUID REFERENCES users(id),
  note TEXT,
  linked_project_id UUID,
  linked_project_url TEXT,
  created_at TIMESTAMPTZ NOT NULL
);
```

------

## 9.6 projects

```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  key TEXT NOT NULL UNIQUE,
  description TEXT,
  status TEXT NOT NULL CHECK (status IN ('planning', 'active', 'paused', 'completed', 'cancelled')),
  owner_id UUID REFERENCES users(id),
  start_date DATE,
  target_end_date DATE,
  archived_at TIMESTAMPTZ,
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

------

## 9.7 project_members

```sql
CREATE TABLE project_members (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id),
  added_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE (project_id, user_id)
);
```

------

## 9.8 project_ideas

```sql
CREATE TABLE project_ideas (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  idea_id UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL CHECK (relation_type IN ('origin', 'related', 'inspired_by')),
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE (project_id, idea_id)
);
```

------

## 9.9 project_tasks

```sql
CREATE TABLE project_tasks (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  parent_task_id UUID REFERENCES project_tasks(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL CHECK (status IN ('todo', 'in_progress', 'blocked', 'review', 'done', 'cancelled')),
  assignee_id UUID REFERENCES users(id),
  start_date DATE,
  end_date DATE,
  progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
  sort_order INTEGER NOT NULL DEFAULT 0,
  version INTEGER NOT NULL DEFAULT 1,
  created_by UUID REFERENCES users(id),
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

------

## 9.10 task_dependencies

```sql
CREATE TABLE task_dependencies (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  predecessor_task_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
  successor_task_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
  dependency_type TEXT NOT NULL DEFAULT 'finish_to_start'
    CHECK (dependency_type IN ('finish_to_start')),
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE (predecessor_task_id, successor_task_id),
  CHECK (predecessor_task_id <> successor_task_id)
);
```

业务约束：

- predecessor 和 successor 必须属于同一个 project。
- dependency 不得形成环。
- 不允许跨 project dependency。

------

## 9.11 api_keys

```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  key_id TEXT NOT NULL UNIQUE,
  secret_hash TEXT NOT NULL,
  secret_last4 TEXT NOT NULL,
  scopes TEXT[] NOT NULL,
  allowed_entities TEXT[] NOT NULL DEFAULT ARRAY['idea'],
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL
);
```

第一版 allowed_entities 必须只允许：

```text
idea
```

------

## 9.12 api_key_nonces

```sql
CREATE TABLE api_key_nonces (
  id UUID PRIMARY KEY,
  key_id TEXT NOT NULL,
  nonce TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE (key_id, nonce)
);
```

------

## 9.13 activity_stream

```sql
CREATE TABLE activity_stream (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  actor_user_id UUID REFERENCES users(id),
  action_type TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID NOT NULL,
  before JSONB,
  after JSONB,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL
);
```

------

## 9.14 audit_logs

```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  actor_user_id UUID REFERENCES users(id),
  actor_api_key_id UUID REFERENCES api_keys(id),
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID,
  before JSONB,
  after JSONB,
  ip_address INET,
  user_agent TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL
);
```

------

## 9.15 external_links

```sql
CREATE TABLE external_links (
  id UUID PRIMARY KEY,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('idea', 'project', 'task')),
  entity_id UUID NOT NULL,
  url TEXT NOT NULL,
  title TEXT,
  description TEXT,
  image_url TEXT,
  site_name TEXT,
  link_type TEXT CHECK (link_type IN ('github_repo', 'website', 'doc', 'other')),
  metadata JSONB,
  last_fetched_at TIMESTAMPTZ,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL
);
```

------

# 10. API 设计

## 10.1 Auth

```text
GET  /api/v1/auth/login
GET  /api/v1/auth/callback
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

------

## 10.2 Users

```text
GET   /api/v1/users
GET   /api/v1/users/{user_id}
PATCH /api/v1/users/{user_id}/role
PATCH /api/v1/users/{user_id}/active
```

限制：

- role 修改仅 superuser 可执行。
- administrator 不能任命 administrator。
- administrator 不能修改 superuser。

------

## 10.3 Ideas

```text
GET    /api/v1/ideas
POST   /api/v1/ideas
GET    /api/v1/ideas/{idea_id}
PATCH  /api/v1/ideas/{idea_id}
DELETE /api/v1/ideas/{idea_id}
POST   /api/v1/ideas/{idea_id}/status
GET    /api/v1/ideas/{idea_id}/history
```

------

## 10.4 Idea Tags

```text
GET    /api/v1/idea-tags
POST   /api/v1/idea-tags
GET    /api/v1/idea-tags/{tag_id}
PATCH  /api/v1/idea-tags/{tag_id}
DELETE /api/v1/idea-tags/{tag_id}

POST   /api/v1/ideas/{idea_id}/tags
DELETE /api/v1/ideas/{idea_id}/tags/{tag_id}
```

tag 创建 payload：

```json
{
  "name": "backend",
  "color": "#1976D2",
  "description": "Backend-related ideas"
}
```

idea 添加 tag payload：

```json
{
  "tag_ids": ["uuid-1", "uuid-2"]
}
```

idea 创建时也允许传 tags：

```json
{
  "title": "Add AI workflow ingestion",
  "description": "Allow external AI agents to submit ideas.",
  "tag_names": ["ai", "workflow", "backend"]
}
```

如果 tag 不存在，是否允许自动创建可由配置决定。默认建议：

```text
Web UI：允许 administrator / superuser 创建 tag。
API Key：默认不自动创建 tag，只能使用已有 tag；可作为后续配置项开放。
```

------

## 10.5 Projects

```text
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}

POST   /api/v1/projects/{project_id}/members
DELETE /api/v1/projects/{project_id}/members/{user_id}

GET    /api/v1/projects/{project_id}/ideas
POST   /api/v1/projects/{project_id}/ideas
DELETE /api/v1/projects/{project_id}/ideas/{idea_id}
```

------

## 10.6 Tasks

```text
GET    /api/v1/projects/{project_id}/tasks
POST   /api/v1/projects/{project_id}/tasks
GET    /api/v1/tasks/{task_id}
PATCH  /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}
```

------

## 10.7 Gantt

```text
GET   /api/v1/projects/{project_id}/gantt
PATCH /api/v1/projects/{project_id}/gantt/bulk
```

bulk update payload：

```json
{
  "changes": [
    {
      "task_id": "uuid",
      "version": 3,
      "start_date": "2026-07-01",
      "end_date": "2026-07-05",
      "assignee_id": "uuid",
      "progress": 40
    }
  ]
}
```

------

## 10.8 Task Dependencies

```text
POST   /api/v1/projects/{project_id}/task-dependencies
DELETE /api/v1/projects/{project_id}/task-dependencies/{dependency_id}
```

create payload：

```json
{
  "predecessor_task_id": "uuid",
  "successor_task_id": "uuid",
  "dependency_type": "finish_to_start"
}
```

后端必须校验：

- 两个 task 属于同一个 project。
- 不形成 cycle。
- 不重复。
- predecessor != successor。

------

## 10.9 API Keys

```text
GET    /api/v1/api-keys
POST   /api/v1/api-keys
PATCH  /api/v1/api-keys/{api_key_id}
DELETE /api/v1/api-keys/{api_key_id}
POST   /api/v1/api-keys/{api_key_id}/rotate
```

------

## 10.10 Activity

```text
GET /api/v1/projects/{project_id}/activity
```

支持 query：

```text
actor_user_id
action_type
entity_type
limit
cursor
```

------

## 10.11 External Links

```text
GET    /api/v1/{entity_type}/{entity_id}/links
POST   /api/v1/{entity_type}/{entity_id}/links
DELETE /api/v1/links/{link_id}
POST   /api/v1/links/preview
```

------

# 11. API Key 签名机制

## 11.1 使用场景

API Key 用于 AI workflow 和外部自动化系统接入 idea 系统。

第一版只允许访问：

```text
/api/v1/ideas
/api/v1/idea-tags 只读
```

不允许访问：

```text
/api/v1/projects
/api/v1/tasks
/api/v1/gantt
/api/v1/users
```

------

## 11.2 Headers

```text
X-Api-Key: <key_id>
X-Api-Timestamp: <ISO8601 timestamp>
X-Api-Nonce: <random nonce>
X-Api-Signature-Version: v1
X-Api-Signature: <signature>
```

------

## 11.3 Canonical Request

```text
METHOD
PATH
CANONICAL_QUERY_STRING
SHA256_HEX(BODY)
TIMESTAMP
NONCE
```

------

## 11.4 Signature

```text
base64url(hmac_sha256(secret, canonical_request))
```

------

## 11.5 校验流程

1. 根据 `X-Api-Key` 查找 API Key。
2. 校验 active / expired / revoked。
3. 校验 allowed_entities 仅允许 idea。
4. 校验 scope。
5. 校验 timestamp 与服务端时间差，默认 ±5 分钟。
6. 校验 nonce 未使用。
7. 重建 canonical request。
8. 计算 HMAC。
9. 使用 constant-time compare 对比签名。
10. 写入 nonce。
11. 更新 last_used_at。
12. 记录 audit log。

------

# 12. SSO 设计

## 12.1 Provider

使用：

```text
BITNP keycloak-account-service
```

接入方式：

```text
OIDC / OAuth2
```

------

## 12.2 Adapter 设计

后端实现 OIDC adapter：

```text
bitnp_ideas/security/oidc_adapter.py
```

职责：

- 生成 login URL
- 处理 callback
- 校验 token
- 获取 userinfo
- 映射 internal user
- 创建 session / JWT

------

## 12.3 用户映射规则

唯一用户识别：

```text
sso_provider + sso_subject
```

email 不作为唯一身份主键，只作为展示和辅助匹配。

------

# 13. 甘特图设计

## 13.1 UI 结构

甘特图页面由两部分组成：

```text
左侧任务表格 + 右侧时间轴
```

左侧显示：

- task title
- assignee
- status
- progress
- start_date
- end_date

右侧显示：

- task bar
- dependency lines
- progress indicator
- drag handles

------

## 13.2 交互要求

必须支持：

- 拖动 task bar 调整日期
- resize task bar 调整工期
- 拖拽 dependency edge 创建依赖
- 点击 dependency edge 删除依赖
- 切换 assignee
- 修改 progress
- 点击 task 打开 drawer

------

## 13.3 后端强校验

前端不得作为唯一可信来源。

后端必须校验：

- task 属于 project
- dependency 不跨 project
- dependency 不成环
- assignee 是 project member
- developer 只能操作参与项目
- version 未冲突

------

## 13.4 Cycle Detection

创建 dependency 时进行有向图环检测。

示例：

```text
A → B → C
```

禁止再创建：

```text
C → A
```

------

# 14. Activity Stream 设计

## 14.1 作用

Activity Stream 面向项目管理者和项目成员，用于展示项目中发生的关键行为。

它不是系统审计表，而是产品功能。

------

## 14.2 示例事件

```text
task.created
task.updated
task.rescheduled
task.assigned
task.progress_changed
task.dependency_created
task.dependency_deleted
idea.linked
idea.unlinked
project.member_added
project.member_removed
```

------

## 14.3 示例 payload

```json
{
  "action_type": "task.rescheduled",
  "entity_type": "task",
  "entity_id": "uuid",
  "before": {
    "start_date": "2026-07-01",
    "end_date": "2026-07-05"
  },
  "after": {
    "start_date": "2026-07-03",
    "end_date": "2026-07-08"
  }
}
```

------

# 15. Audit Log 设计

## 15.1 作用

Audit Log 用于系统级审计，不面向普通项目成员展示。

必须尽量不可变。

------

## 15.2 必须记录的行为

- 用户角色变化
- 用户启用 / 禁用
- 项目创建 / 修改 / 归档
- 项目成员变化
- 任务创建 / 修改 / 删除
- 甘特图变更
- dependency 变更
- idea 状态变化
- idea tag 变更
- API Key 创建 / 禁用 / 轮换
- API Key 验签失败

------

# 16. 前端设计

## 16.1 页面结构

```text
/login
/dashboard
/ideas
/ideas/:id
/projects
/projects/:id
/projects/:id/tasks
/projects/:id/gantt
/projects/:id/activity
/api-keys
/users
/settings
```

------

## 16.2 Ideas 页面

需要支持：

- idea list
- status filter
- tag filter
- creator filter
- search
- sort by updated_at / created_at
- idea card
- idea detail drawer
- tag chips
- status change dialog
- link project dialog

------

## 16.3 Idea Tag UI

需要支持：

- tag chips
- tag autocomplete
- tag filter sidebar
- tag color
- tag usage count
- disabled tag 不可新增但历史 idea 保留显示

------

## 16.4 Project Detail

Tabs：

```text
Overview
Tasks
Gantt
Ideas
Links
Activity
Settings
```

------

## 16.5 Project Dashboard

显示：

- 项目基本信息
- 成员
- 任务进度
- 逾期任务
- 最近 activity
- 关联 ideas
- external links

项目管理者必须能看到 developer 的项目操作记录。

------

## 16.6 Gantt UI

必须直观，操作优先级：

1. 拖动任务时间
2. 拖动依赖线
3. 切换执行人
4. 修改进度
5. 打开任务详情
6. 查看 activity

------

# 17. 工程化约束

## 17.1 Monorepo

推荐：

```text
bitnp-ideas/
  apps/
    backend/
    frontend/
  packages/
    shared-types/
    eslint-config/
    commitlint-config/
  docs/
```

------

## 17.2 Backend Commands

```bash
uv sync
uv run ruff format
uv run ruff check
uv run pytest
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
uv run uvicorn bitnp_ideas.main:app
```

### 17.2.0 Backend 配置文件

后端运行配置统一写入 YAML 文件。

默认本地配置文件：

```text
apps/backend/config.yaml
```

默认本地数据库配置：

```yaml
database:
  url: postgres://bitnp_ideas:bitnp_ideas@127.0.0.1/bitnp_ideas
```

约定：

- 后端代码不得为关键配置提供会覆盖错误输入的业务默认值。
- YAML 缺字段、字段类型错误、URL scheme 不支持、OIDC 配置不完整、API Key 边界不符合第一版约束时，服务必须启动失败并直接退出。
- 运行时可以通过 `BITNP_IDEAS_CONFIG` 指定另一个 YAML 文件路径，但配置内容仍必须来自 YAML。
- 开发与部署可以使用不同 YAML 文件，例如 Docker Compose 使用 `apps/backend/config.docker.yaml` 连接 Compose 内部的 `postgres` 服务。

### 17.2.1 Migration 文件策略

Alembic 迁移文件默认不提交到仓库。

原因：

- 多个开发分支同时修改数据库结构时，迁移文件容易出现 revision 冲突。
- 迁移冲突处理不当时，常见结果是本地或测试库只能整体重建。
- 第一版优先保持模型为单一事实来源，迁移文件由拉取代码的一方在本地生成并执行。

约定：

- `apps/backend/alembic/versions/*.py` 默认写入 `.gitignore`。
- 拉取代码后，如模型发生变化，应在本地执行 `uv run alembic revision --autogenerate -m "describe schema change"` 生成迁移文件。
- 生成后执行 `uv run alembic upgrade head` 更新数据库。
- 迁移文件仅在团队明确协调 revision 链路、或发布流程要求固定迁移历史时才允许提交。

该流程类似 Django 中先根据当前模型生成迁移，再执行迁移；区别是本项目默认不把开发期迁移文件作为共享源文件提交。

------

## 17.3 Frontend Commands

```bash
pnpm install
pnpm lint
pnpm typecheck
pnpm build
pnpm dev
```

------

## 17.4 Commit Convention

使用 Conventional Commits。

示例：

```text
feat(ideas): add idea tag management
fix(gantt): prevent cross-project dependency
chore(ci): add backend lint workflow
docs(design): refine bitnp ideas architecture
```

------

## 17.5 Pre-commit

必须统一配置：

后端：

```text
ruff format
ruff check
pytest
```

前端：

```text
eslint
prettier
vue-tsc
```

commit message：

```text
commitlint
```

------

# 18. 部署要求

## 18.1 Docker 部署

提供：

```text
docker-compose.yml
```

包含：

- backend
- frontend
- postgres

用于：

- 本地开发
- 测试
- demo

------

## 18.2 非 Docker 部署

必须提供非 Docker 部署文档。

### Backend

使用：

```text
uv
uvicorn
systemd
```

示例：

```ini
[Unit]
Description=BITNP IDEAS Backend

[Service]
WorkingDirectory=/opt/bitnp-ideas/apps/backend
ExecStart=/usr/local/bin/uv run uvicorn bitnp_ideas.main:app --host 127.0.0.1 --port 8000
Restart=always
EnvironmentFile=/etc/bitnp-ideas/backend.env

[Install]
WantedBy=multi-user.target
```

------

### Frontend

使用：

```text
pnpm build
nginx
```

输出：

```text
apps/frontend/dist
```

部署到 nginx 静态目录。

------

### PostgreSQL

支持：

- 系统包安装 PostgreSQL
- 外部托管 PostgreSQL
- 独立数据库实例

Migration：

```bash
uv run alembic upgrade head
```

------

# 19. MVP 阶段计划

## Phase 0: Project Bootstrap

目标：

- monorepo 初始化
- backend skeleton
- frontend skeleton
- docker-compose
- pre-commit
- commitlint
- CI skeleton

------

## Phase 1: Auth & RBAC

目标：

- OIDC login
- user model
- session / JWT
- global role
- superuser init
- RBAC dependency

------

## Phase 2: Idea System

目标：

- idea CRUD
- idea status
- idea status history
- idea tags
- idea tag many-to-many
- tag filter
- idea-project linking
- API Key idea ingestion

------

## Phase 3: API Key Security

目标：

- API Key management
- HMAC signature
- nonce
- timestamp
- scopes
- idea-only enforcement
- audit log for API access

------

## Phase 4: Project System

目标：

- project CRUD
- project members
- linked ideas
- project dashboard
- external links

------

## Phase 5: Task System

目标：

- task CRUD
- assignee
- status
- progress
- date range
- optimistic lock
- developer project participation rule

------

## Phase 6: Gantt & Dependency

目标：

- gantt API
- gantt UI
- drag scheduling
- resize
- dependency drag line
- dependency delete
- cycle detection
- no cross-project dependency

------

## Phase 7: Activity & Audit

目标：

- activity stream
- audit log
- project dashboard visibility
- developer operation traceability

------

## Phase 8: Hardening

目标：

- tests
- error handling
- migration review
- deployment docs
- non-Docker deployment
- API documentation

------

# 20. 实现优先级

最高优先级：

```text
OIDC + RBAC
Idea + Tag
API Key signature
Project + Member
Task + Gantt
Activity + Audit
```

中优先级：

```text
External Links
Link Preview
Dashboard polish
OpenAPI generated client
```

低优先级：

```text
CSV import/export
Notifications
Attachments
Advanced workflow automation
Project-level roles
Cross-project dependencies
```

明确不做：

```text
第一版不做导入导出
第一版不做跨项目任务依赖
第一版 API Key 不操作项目和任务
第一版不做完整 Jira-style workflow engine
```

------

# 21. 关键验收标准

## 21.1 Idea

- 用户可以创建 idea。
- 用户可以给 idea 添加多个 tag。
- 用户可以按 tag 过滤 idea。
- idea 可以进入 paused / in_progress / completed 状态。
- in_progress / completed 必须关联 project 或 URL。
- idea 状态变化写入 history。
- API Key 可以创建 idea。
- API Key 不能访问 project / task。

------

## 21.2 Project

- administrator / superuser 可以创建 project。
- administrator / superuser 可以添加成员。
- developer 只能看到并操作自己参与的 project。
- project 可以关联多个 idea。
- project dashboard 可以看到 activity。

------

## 21.3 Task / Gantt

- 项目成员可以创建 / 编辑 task。
- task 可以设置 assignee、start_date、end_date、progress。
- 甘特图可以拖动调整任务时间。
- 甘特图可以拖动创建 dependency。
- 后端禁止跨 project dependency。
- 后端禁止 dependency cycle。
- developer 的任务操作写入 activity stream 和 audit log。

------

## 21.4 Security

- SSO 使用 OIDC。
- superuser 可任命 administrator。
- administrator 不能任命 administrator。
- API Key 使用 HMAC-SHA256 签名。
- API Key 请求必须包含 timestamp 和 nonce。
- nonce 不可重复使用。
- API Key secret 只展示一次。
- API Key secret 不以明文存储。

------

# 22. 当前实现对照、接口契约与测试覆盖

本章记录 v1 当前代码实现与设计目标之间的对照关系，用于后续开发、测试补齐和前后端接口联调。

## 22.1 当前已落地范围

当前仓库已经形成可运行的 monorepo 基础：

- 后端 FastAPI 应用已挂载 `health/auth/users/ideas/idea-tags/projects/tasks/gantt/api-keys/activity/external-links` 路由。
- 后端路由本身不带 `/api/v1` 前缀，前端通过 Vite proxy 和 nginx 将 `/api/v1/*` 剥离后转发到后端裸路径。
- 数据模型已覆盖用户、idea、tag、项目、成员、项目-idea 关联、任务、依赖、API Key、nonce、activity、audit、external link。
- 前端已具备登录、dashboard、ideas、projects、project detail、gantt、api keys、users 页面。
- 甘特图已接入前后端批量更新、任务依赖创建和删除。
- Activity Stream 和 Audit Log 写入 helper 已在任务、项目成员、依赖、idea、API Key 等关键动作中使用。
- 后端配置统一来自 YAML，开发默认配置为 `apps/backend/config.yaml`。

## 22.2 版本化 API 前缀契约

第一版必须保持以下分层：

```text
Frontend request: /api/v1/ideas
Vite/nginx proxy: strip /api/v1
Backend route: /ideas
OpenAPI path: /ideas
```

因此：

- 后端 FastAPI 不直接挂 `/api/v1`。
- OpenAPI 测试必须持续断言不存在 `/api/v1/*`。
- API Key 签名的 canonical path 使用后端实际接收路径，例如 `/ideas`，不是代理层的 `/api/v1/ideas`。
- 前端代码可以继续用 `/api/v1` 作为 axios baseURL。

## 22.3 前后端接口对接规则

后端 OpenAPI 是第一版 API 契约事实来源。前端手写类型必须与后端保持一致，尤其注意：

- API 字段使用 snake_case，例如 `created_at`、`updated_at`、`project_id`、`start_date`。
- `POST /ideas/{idea_id}/status` 返回 `ApiMessage`，前端成功后需要重新拉取 idea 或本地合并状态。
- `PATCH /users/{user_id}/role` 使用 query 参数 `role`，返回 `ApiMessage`。
- `PATCH /users/{user_id}/active` 使用 query 参数 `is_active`，返回 `ApiMessage`。
- `POST /api-keys` 和 `POST /api-keys/{api_key_id}/rotate` 返回 `{ api_key, secret }`，secret 只展示一次。
- `PATCH /api-keys/{api_key_id}` 返回 `ApiMessage`，前端应本地合并 name/is_active/scopes 或重新拉取列表。
- external link 的 `entity_type` 只允许单数：`idea`、`project`、`task`。
- `TaskDependencyCreate.dependency_type` 第一版只允许 `finish_to_start`。
- `IdeaCreate` 当前后端接收 `tag_names`；如果产品希望用 `tag_ids` 创建 idea，需要先变更后端 schema 和 OpenAPI。

## 22.4 当前端点测试覆盖

后端端点测试采用临时 SQLite async 数据库和 FastAPI dependency override，不依赖真实 PostgreSQL。

当前覆盖：

| 测试文件 | 覆盖内容 |
| -------- | -------- |
| `tests/test_app.py` | `/health`、OpenAPI smoke、后端无 `/api/v1` 前缀 |
| `tests/test_config.py` | YAML 配置解析、非法数据库 URL 拒绝 |
| `tests/test_openapi_contract.py` | 前端依赖的 schema 字段、Gantt bulk status、link preview shape |
| `tests/test_api_endpoints.py` | users RBAC、idea/tag/status/history、project/task/gantt/dependency/activity、external links、API key 管理和签名边界 |

测试必须继续覆盖以下边界：

- developer 不能创建项目。
- developer 只能访问自己参与的项目。
- task 日期不能倒置。
- task update 和 gantt bulk update 必须校验 version。
- task dependency 不允许重复、自依赖、跨项目和形成 cycle。
- idea 进入 `in_progress/completed` 必须关联 project 或 URL。
- API Key scope 只能是 `ideas:read` 和 `ideas:write`。
- API Key 只能访问 idea/tag 相关读写，不得访问 projects/tasks/users/gantt。
- Activity/Audit 写入 JSON 字段前必须进行 JSON-safe 编码，避免 date/enum 无法序列化。

## 22.5 当前已知偏差与待补项

以下项目尚未达到最终设计，需要后续补齐：

- API Key secret 当前实现仍以可签名明文形式写入 `secret_hash` 字段；最终必须改为不明文存储的方案，并相应调整验签机制。
- OIDC callback 当前未校验前端持有的 state，JWT 当前未包含 `exp`。
- Audit Log 已有模型和写入，但没有 `/audit-logs` 查询 API 和前端页面。
- 非 Docker 部署仍缺独立文档，需要补 systemd、nginx、PostgreSQL、配置路径和 migration 流程。
- Project Detail 已有 tabs，但成员管理、关联 idea 管理、external link 创建/删除、任务详情 drawer 仍需完善。
- Gantt UI 已支持核心拖动和依赖操作，但 day/week/month 三档视图和任务详情 drawer 仍需补全。
- Dashboard 当前按项目逐个拉 tasks/activity，项目多时需要后端聚合端点或分页策略。
- OpenAPI 到 TypeScript 的自动生成链路尚未建立，当前仍依赖手写 `apps/frontend/src/types/api.ts` 和契约测试保护。

## 22.6 后续优先级

下一阶段建议按以下顺序推进：

1. 修 API Key secret 存储与验签实现，确保 secret 不以明文或等价明文存储。
2. 增加 Audit Log 查询 API，只允许 superuser 或受限 administrator 查看。
3. 建立 OpenAPI -> TypeScript 生成或契约比对脚本，减少前后端类型漂移。
4. 补 Project Detail 的成员、linked ideas、external links 可操作 UI。
5. 补 OIDC state 校验、JWT 过期时间和 logout/session 语义。
6. 补非 Docker 部署文档。

------

# 23. 总结

BITNP IDEAS 的最终形态是：

```text
一个以点子为入口、以项目为管理容器、以任务为执行单元、以甘特图为调度界面、以 Activity Stream 和 Audit Log 为追踪治理机制的内部执行管理系统。
```

其核心设计原则是：

```text
点子可沉淀
执行可推进
任务可调度
行为可追踪
权限有边界
AI 可接入但不能越权
```

第一版必须守住以下边界：

```text
API Key 只接入 Idea
Task Dependency 不跨项目
RBAC 保持全局
Developer 可参与执行但必须审计
Tag 是 Idea 的核心分类能力
SSO 使用 OIDC 抽象
部署同时支持 Docker 与非 Docker
```
