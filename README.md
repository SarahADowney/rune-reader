# Elder Futhark Rune Reader

A divination tool for Elder Futhark runes with AI-powered interpretations.

## Features

- Multiple spreads (1, 2, 3, 5, and 9 rune layouts)
- Optional reversed/merkstave runes
- AI interpretations using Claude
- Saves last 3 readings locally
- Beautiful visual rune display

## Deployment to Vercel

1. Install Vercel CLI (if you haven't):
   ```bash
   npm install -g vercel
   ```

2. Navigate to this directory:
   ```bash
   cd rune-reader-vercel
   ```

3. Deploy:
   ```bash
   vercel
   ```

4. Set environment variable in Vercel dashboard:
   - Go to your project settings
   - Add `ANTHROPIC_API_KEY` with your Anthropic API key

5. Redeploy after setting the environment variable

## Local Testing

You can test locally with:
```bash
vercel dev
```

Make sure to create a `.env` file with:
```
ANTHROPIC_API_KEY=your_key_here
```

## Tech Stack

- Frontend: Vanilla HTML/CSS/JavaScript
- Backend: Vercel Serverless Functions (Python)
- AI: Anthropic Claude API
