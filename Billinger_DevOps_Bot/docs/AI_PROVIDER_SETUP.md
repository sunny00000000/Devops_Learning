# AI Provider Setup — Billinger Bot v2.9.0

## Dashboard setup

1. Start Billinger and open **System & AI**.
2. Authenticate as administrator.
3. In **Credential Vault**, choose a provider.
4. Paste the API key, select or enter the model identifier, set a daily request limit, and enable the provider.
5. Save and press **Test Provider**.
6. Open **Task Routes** and arrange the fallback order for each workload.
7. Configure the global daily limit, timeout, maximum output tokens, redaction, and automatic failover.

## Providers

### Google Gemini

Default use: lesson explanations and curriculum-gap review.
Default model in this release: `gemini-3.6-flash`.

### OpenAI API

Default use: test, interview, resume, and portfolio analysis.
Default model in this release: `gpt-5.6-terra`.
OpenAI API billing and credits are separate from ChatGPT subscriptions.

### Groq

Default use: fast adaptive questions and revision drills.
Default model in this release: `openai/gpt-oss-20b`.

### OpenRouter

Default use: company-role interview packs and broad model-routing fallback.
Default model in this release: `openrouter/auto`.

Provider model availability changes over time. The model field is editable so an administrator can replace a retired or unavailable model without rebuilding the bot.

## Failure behavior

The orchestrator advances to the next configured provider for quota/credit failures, HTTP 429 rate limits, temporary provider errors, timeouts, network failures, invalid JSON, or empty output. Authentication/configuration failures are logged and the next provider is attempted when automatic failover is enabled.

A failed provider enters a temporary cooldown. Local daily request limits prevent one provider from consuming more than the administrator-approved allowance.

## Moving the hard disk

DPAPI-encrypted keys are tied to the Windows account that stored them. Student records remain portable, but API keys must be re-entered when the bot is opened under another Windows account or on another computer.

## Key handling checklist

- Never paste API keys into lessons, resumes, portfolio evidence, or interview answers.
- Do not share the database while active keys are configured.
- Set modest daily limits first.
- Test each provider separately before enabling it in student routes.
- Remove or rotate a key immediately when exposure is suspected.


## Account model discovery

After saving a provider key, press **Discover models**. Billinger stores only the returned model metadata, never the key. Select a discovered identifier and run **Test connection**. A listed identifier may still be incompatible with a particular task, so the connection test remains mandatory. Use **Fallback dry-run** to test route behavior without sending a provider request or consuming credits.
