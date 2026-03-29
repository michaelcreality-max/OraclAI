.PHONY: check verify verify-network wait-verify verify-quant-light

check: verify

verify:
	./scripts/verify.sh

verify-network:
	./scripts/verify.sh --network

verify-quant-light:
	./scripts/verify_quant_light.sh

wait-verify:
	./scripts/wait_for_verify.sh
