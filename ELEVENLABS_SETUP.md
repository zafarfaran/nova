# ElevenLabs Voice Setup Guide

## Quick Setup

1. **Get your ElevenLabs API Key:**
   - Go to [https://elevenlabs.io](https://elevenlabs.io)
   - Sign in or create an account
   - Navigate to your profile settings
   - Copy your API key

2. **Add the API Key to your .env file:**
   Open `/home/sahid/Documents/Saturn AI/nova/.env` and replace the empty string with your API key:
   ```bash
   NEXT_PUBLIC_ELEVENLABS_API_KEY="your_api_key_here"
   ```

3. **Restart your Next.js development server:**
   ```bash
   npm run dev
   ```

## Voice Configuration

The app is currently configured to use **Rachel's voice** - a professional, clear female voice perfect for assistant tasks.

### Voice ID: `21m00Tcm4TlvDq8ikWAM` (Rachel)

### Voice Settings:
- **Stability:** 0.5 (balanced naturalness)
- **Similarity Boost:** 0.75 (consistent voice quality)
- **Speaker Boost:** Enabled (clearer speech)

## Alternative Voices

If you want to use a different voice, edit `AIChat.tsx` line ~158 and change the `voiceId`:

### Professional Voices:
- **Rachel** (current): `21m00Tcm4TlvDq8ikWAM` - Clear, professional female
- **Bella**: `EXAVITQu4vr4xnSDxMaL` - Soft, expressive female
- **Elli**: `MF3mGyEYCl7XYWbV9V6O` - Young, energetic female
- **Josh**: `TxGEqnHWrfWFTfGW9XjX` - Deep, calm male

## Features

✅ **High-quality natural voice** using ElevenLabs neural TTS
✅ **Automatic fallback** to browser speech if ElevenLabs fails
✅ **Visual indicator** showing when speech is playing
✅ **Smart voice control** - stops speech when disabled
✅ **Professional assistant tone** optimized for clarity

## Testing

1. Enable voice in the chat (speaker icon in bottom right)
2. Send a message to the AI
3. The response will be spoken using ElevenLabs Rachel voice
4. You'll see a pulsing green indicator when speech is playing

## Troubleshooting

**No sound?**
- Check that your API key is correct in `.env`
- Verify you've restarted the dev server
- Check browser console for errors
- The app will automatically fallback to browser TTS if ElevenLabs fails

**Voice sounds different?**
- The voice quality depends on your ElevenLabs subscription tier
- Free tier has good quality, paid tiers have exceptional quality

## Cost

ElevenLabs pricing (as of 2024):
- **Free tier:** 10,000 characters/month
- **Starter:** $5/month for 30,000 characters
- **Creator:** $22/month for 100,000 characters

Each AI response will consume characters based on its length.
