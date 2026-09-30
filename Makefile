.PHONY: test smoke lint fmt jupyter api mcp mcp-inspector

jupyter:
	uv run jupyter lab \
		--ip=127.0.0.1 \
		--port=8888 \
		--no-browser

api:
	uv run uvicorn app:app --host 127.0.0.1 --port 8000 --reload

mcp:
	fastmcp run mcp_server.py --transport http --host 0.0.0.0 --port 9000

mcp-inspector:
	# Note: Use http://host.docker.internal:9000/mcp in web interface
	docker run --rm \
	  -p 127.0.0.1:6274:6274 \
	  -p 127.0.0.1:6277:6277 \
	  -e HOST=0.0.0.0 \
	  -e MCP_AUTO_OPEN_ENABLED=false \
	  --add-host=host.docker.internal:host-gateway \
	  ghcr.io/modelcontextprotocol/inspector:latest