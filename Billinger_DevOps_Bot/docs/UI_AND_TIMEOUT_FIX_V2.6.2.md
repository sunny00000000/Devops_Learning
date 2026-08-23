# Billinger Bot v2.6.2 — AI Dashboard and Timeout Fix

## Corrected issues

1. **Only two AI providers appeared visible**
   - All four provider cards—Gemini, OpenAI, Groq and OpenRouter—now appear in one row on normal laptop and desktop widths.
   - Medium screens use a 2×2 layout.
   - Mobile screens use one card per row.
   - The provider overview remains visible above the forms and can jump directly to a provider.

2. **Dashboard lettering was too light**
   - Body copy, labels, helper text, placeholders, provider descriptions, route notes and usage text now use darker high-contrast colors on light surfaces.
   - Dark terminal and navigation surfaces retain light text.

3. **AI connection test timed out**
   - The default request timeout is 120 seconds.
   - The dashboard permits 10–300 seconds.
   - Provider tests use a small output request and a minimum 120-second read window.
   - OpenAI connection tests request no deep reasoning when the selected model supports it.
   - Errors distinguish read timeout, network failure, authentication, quota/rate-limit and invalid response conditions.

## Responsive behavior

- Desktop/laptop: four provider cards in one row.
- Tablet/smaller window: two cards per row.
- Mobile: one card per row.
- Full-screen navigation remains independently scrollable.
