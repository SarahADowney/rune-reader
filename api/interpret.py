from http.server import BaseHTTPRequestHandler
import json
import os
from anthropic import Anthropic

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Read request body
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body.decode('utf-8'))

        spread_name = data.get("spread")
        runes = data.get("runes")

        # Build prompt
        prompt = "You are an expert in Elder Futhark rune divination. Provide a thoughtful, nuanced interpretation of this rune reading. Be general and neutral so anyone can relate to it.\n\n"
        prompt += f"Spread: {spread_name}\n\n"
        prompt += "Runes drawn:\n"

        for rune in runes:
            orientation = "(Reversed/Merkstave)" if rune.get("reversed") else "(Upright)"
            meaning = rune.get("reversed_meaning") if rune.get("reversed") else rune.get("upright_meaning")
            prompt += f"- {rune['name']} {orientation} in position \"{rune['position']}\": {meaning}\n"

        prompt += "\nProvide an interpretation that:\n"
        prompt += "1. Considers each rune in context of its position\n"
        prompt += "2. Explores how the runes relate to each other\n"
        prompt += "3. Offers insight and guidance\n"
        prompt += "4. Is written in a contemplative, wise tone\n"
        prompt += "5. Is 2-3 paragraphs\n"
        prompt += "\nDo not include headers or formatting, just the interpretation text."

        try:
            # Initialize Anthropic client
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise Exception("ANTHROPIC_API_KEY not set")

            client = Anthropic(api_key=api_key)

            # Get interpretation from Claude
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            interpretation = response.content[0].text

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "interpretation": interpretation
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": str(e)
            }).encode())

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
