abyss:
	python -m antisim.core --full

prove:
	python -m antisim.vc_issuer --zkp

revoke:
	python -m antisim.vc_issuer --revoke-all

test:
	pytest tests/
