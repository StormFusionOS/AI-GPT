SERVICE ?= ops
MESSAGE ?=
MESSAGE_LOWER := $(message)
MESSAGE := $(if $(strip $(MESSAGE)),$(MESSAGE),$(MESSAGE_LOWER))

ifeq ($(strip $(MESSAGE)),)
$(error message="..." is required. Usage: make migrate SERVICE=ops message="add table")
endif

SERVICE_DIR := $(if $(filter $(SERVICE),ops),ops_api,$(if $(filter $(SERVICE),crm),crm_api,))

ifeq ($(strip $(SERVICE_DIR)),)
$(error Unsupported SERVICE '$(SERVICE)'. Use SERVICE=ops or SERVICE=crm)
endif

migrate:
cd $(SERVICE_DIR) && poetry run alembic revision --autogenerate -m "$(MESSAGE)"
