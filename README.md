# 3D Print Flow Backend

Django backend for managing 3D print operations: custom user auth, catalog, order workflow, docs.

## Auth highlights
- Email-first user model with dj-rest-auth + allauth
- Workspace auto-provisioning on registration
- Mailpit SMTP for dev + Google OAuth wiring ready

## Catalog
- Materials/colors per workspace
- Products with versioned documents (PDFs) stored under `/media/product_docs/<product_id>/`
- Admin inline for managing specs/manuals; primary-per-kind constraint enforced

## Orders
- `totals_locked` keeps marketplace totals untouched
- Importers copy platform totals into `total_cost` and `external_total_cost`, then set `totals_locked=True`
- Manual orders leave `totals_locked=False`; unit price defaults to product price if blank and totals recompute via signal
- JSON fields (`attributes`, `external_payload`) default to `{}` to avoid NULL edge cases

## Development
- Docker setup with Postgres, Redis, Mailpit, Celery workers (workers unused yet)
- `docker compose up -d --build` to start the stack
- `docker compose exec backend python manage.py migrate` to sync DB
- Admin at `http://localhost:8001/admin/`

## Next steps
- Build order API endpoints + tests
- Model inventory/filament and queue workflow
- Add admin UX niceties (live totals preview, hide integration-only fields)
