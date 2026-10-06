.DEFAULT_GOAL := help
PY := uv run

help: ## Komutları listele
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

sync: ## Bağımlılıkları kur
	uv sync --all-extras --dev

lint: ## ruff kontrolü
	$(PY) ruff check .

format: ## ruff biçimlendirme
	$(PY) ruff format .
	$(PY) ruff check --fix .

type: ## mypy (strict)
	$(PY) mypy

test: ## testler
	$(PY) pytest

cov: ## kapsamlı testler
	$(PY) pytest --cov=clause_cite --cov-report=term-missing

check: lint type test ## Tüm kalite kapıları

demo: ## Örnek belgeleri çıkar (çapa tarihi 2026-01-01)
	$(PY) clause-cite extract examples/data/*.txt --anchor 2026-01-01

verify: ## Alıntı invariyantını doğrula (örnek belgeler)
	$(PY) clause-cite verify examples/data/*.txt

eval: ## Altın set regresyon testleri
	$(PY) clause-cite eval examples/golden

kinds: ## Desteklenen madde türlerini ve modality karşılıklarını listele
	$(PY) clause-cite kinds

demo-svg: ## README için SVG çıktı üret
	$(PY) python scripts/make_demo_svg.py

clean: ## Temizlik
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: help sync lint format type test cov check demo verify eval kinds demo-svg clean
