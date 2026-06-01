
### 2. **Makefile** (REPLACE)

```makefile
.PHONY: install demo serve test clean docker-build docker-run

install:
	pip install -e .[dev]

demo:
	python examples/demo.py

serve:
	uvicorn api.server:app --host 0.0.0.0 --port 8080 --reload

test:
	pytest tests/ -v --cov=antisim

test-predictor:
	python -m pytest tests/test_predictor.py -v

benchmark:
	python scripts/benchmark.py

docker-build:
	docker build -t antisim-abyss:latest .

docker-run:
	docker run -p 8080:8080 antisim-abyss:latest

clean:
	rm -rf build/ dist/ *.egg-info __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

generate-keys:
	python scripts/generate_keys.py

help:
	@echo "Available commands:"
	@echo "  make install      - Install package and dependencies"
	@echo "  make demo         - Run demonstration"
	@echo "  make serve        - Start API server"
	@echo "  make test         - Run all tests"
	@echo "  make benchmark    - Run performance benchmarks"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
