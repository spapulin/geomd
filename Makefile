.PHONY: test smoke lint fmt jupyter

jupyter:
	uv run jupyter lab \
		--ip=0.0.0.0 \
		--port=8888
