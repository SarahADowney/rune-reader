from http.server import BaseHTTPRequestHandler
import json
import os
import time
from anthropic import Anthropic

# Simple in-memory rate limiter
# Note: This resets on cold starts, but provides protection during active periods
rate_limit_store = {}
RATE_LIMIT = 5  # requests per hour
RATE_WINDOW = 3600  # 1 hour in seconds

def check_rate_limit(ip_address):
    """Returns (allowed, remaining, reset_time)"""
    current_time = time.time()

    if ip_address not in rate_limit_store:
        rate_limit_store[ip_address] = []

    # Remove old requests outside the time window
    rate_limit_store[ip_address] = [
        req_time for req_time in rate_limit_store[ip_address]
        if current_time - req_time < RATE_WINDOW
    ]

    # Check if under limit
    request_count = len(rate_limit_store[ip_address])

    if request_count >= RATE_LIMIT:
        oldest_request = min(rate_limit_store[ip_address])
        reset_time = oldest_request + RATE_WINDOW
        return False, 0, reset_time

    # Add current request
    rate_limit_store[ip_address].append(current_time)
    remaining = RATE_LIMIT - (request_count + 1)
    reset_time = current_time + RATE_WINDOW

    return True, remaining, reset_time

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Get client IP
        ip_address = self.headers.get('x-forwarded-for', self.client_address[0])
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()

        # Check rate limit
        allowed, remaining, reset_time = check_rate_limit(ip_address)

        if not allowed:
            self.send_response(429)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('X-RateLimit-Limit', str(RATE_LIMIT))
            self.send_header('X-RateLimit-Remaining', '0')
            self.send_header('X-RateLimit-Reset', str(int(reset_time)))
            self.end_headers()

            minutes_until_reset = int((reset_time - time.time()) / 60)
            self.wfile.write(json.dumps({
                "error": f"Rate limit exceeded. You can cast {RATE_LIMIT} runes per hour. Please try again in {minutes_until_reset} minutes."
            }).encode())
            return

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

            # Send response with rate limit headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('X-RateLimit-Limit', str(RATE_LIMIT))
            self.send_header('X-RateLimit-Remaining', str(remaining))
            self.send_header('X-RateLimit-Reset', str(int(reset_time)))
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
