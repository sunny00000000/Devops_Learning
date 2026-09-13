"""
Billinger v2.6 Features Layer: Multi-Provider Adaptive AI Router
Directly integrates with ai.router and ai.providers for 4-provider failover + offline engine.
"""
from ai.router import ai_router, AIRouter
from ai.providers import ai_provider_manager, AIProviderManager

class AdaptiveAIRouter:
    def __init__(self):
        self.router = ai_router
        self.manager = ai_provider_manager

    def get_provider_status(self):
        return self.manager.get_status()

    def query(self, prompt, preferred_provider="gemini"):
        return self.router.route(prompt, provider=preferred_provider)

# Root instance
router = AdaptiveAIRouter()
