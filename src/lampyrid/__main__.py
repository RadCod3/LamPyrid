import os
from .server import mcp


def main() -> None:
	# Support both stdio (for local development) and http (for containerized deployment)
	transport = os.environ.get('MCP_TRANSPORT', 'stdio')

	if transport == 'http':
		# HTTP mode for containerized deployment
		host = os.environ.get('MCP_HOST', '0.0.0.0')
		port = int(os.environ.get('MCP_PORT', '3000'))
		mcp.run(transport='streamable-http', host=host, port=port)
	else:
		# Default stdio mode for local development
		mcp.run(transport='stdio')


if __name__ == '__main__':
	main()
