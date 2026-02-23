.PHONY: test docker-build docker-up docker-down docker-logs db-tables bundle

test:
	pytest tests/

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

db-tables:
	sqlite3 $${DB_PATH:-./data/scrapers.db} ".tables"

show-data:
	@echo "Recent AI Articles Scraped:"
	@sqlite3 -header -column $${DB_PATH:-./data/scrapers.db} "SELECT source, title, investment_relevant FROM articles ORDER BY inserted_at DESC LIMIT 10;"

bundle:
	@echo "Building review bundle..."
	python bundle_project.py
