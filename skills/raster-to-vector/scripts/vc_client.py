"""Minimal stdio client for the VectorCraft MCP server (vectorcraft-cli mcp --headless)."""
import json
import subprocess


class VectorCraft:
    """One headless VectorCraft session driven over newline-delimited JSON-RPC."""

    def __init__(self, binary="vectorcraft-cli", args=("mcp", "--headless")):
        """Start the server and complete the MCP initialize handshake."""
        self.proc = subprocess.Popen([binary, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.next_id = 0
        self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                    "clientInfo": {"name": "raster-to-vector", "version": "0"}})
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")

    def request(self, method, params):
        """Send one request and return its result; raise on a JSON-RPC error."""
        self.next_id += 1
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params}) + "\n")
        while True:
            message = json.loads(self.proc.stdout.readline())
            if message.get("id") == self.next_id:
                break
        if "error" in message:
            raise RuntimeError(message["error"])
        return message["result"]

    def call(self, tool, **arguments):
        """Call one MCP tool; return its text content, raising if the tool reports an error."""
        result = self.request("tools/call", {"name": tool, "arguments": arguments})
        text = "\n".join(part.get("text", "") for part in result.get("content", []))
        if result.get("isError"):
            raise RuntimeError(f"{tool}: {text}")
        return text

    def tools(self):
        """Names of the tools the server offers."""
        return [tool["name"] for tool in self.request("tools/list", {})["tools"]]

    def close(self):
        """Stop the server."""
        self.proc.stdin.close()
        self.proc.wait(timeout=30)
