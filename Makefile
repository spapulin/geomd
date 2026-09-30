.PHONY: test smoke lint fmt jupyter api mcp mcp-inspector

# JupyterLab on 127.0.0.1:8888, no browser auto-open. Loopback only
jupyter:
	uv run jupyter lab \
		--ip=127.0.0.1 \
		--port=8888 \
		--no-browser

# Run the FastAPI app locally with auto-reload on 127.0.0.1:8000
api:
	uv run uvicorn app:app --host 127.0.0.1 --port 8000 --reload

# Run the MCP server over HTTP on 0.0.0.0:9000 with auto-reload.
# Bound to all interfaces so it can be reached from Docker / other hosts
mcp:
	fastmcp run mcp_server.py --transport http --host 0.0.0.0 --port 9000 --reload

# Launch the MCP Inspector web UI in Docker to interactively test
# the MCP server.
#
# Open http://localhost:6274 in a browser and connect to:
#   http://host.docker.internal:9000/mcp
#
# Requires `make mcp` to be running in another terminal.
mcp-inspector:
	# Note: Use http://host.docker.internal:9000/mcp in web interface
	docker run --rm \
	  -p 127.0.0.1:6274:6274 \
	  -p 127.0.0.1:6277:6277 \
	  -e HOST=0.0.0.0 \
	  -e MCP_AUTO_OPEN_ENABLED=false \
	  --add-host=host.docker.internal:host-gateway \
	  ghcr.io/modelcontextprotocol/inspector:latest