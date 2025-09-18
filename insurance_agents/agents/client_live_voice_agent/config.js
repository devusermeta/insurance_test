/**
 * Voice Client Configuration
 * Azure Voice Live API configuration for the A2A Voice Agent
 */

// Voice Live API Configuration
window.VOICE_CONFIG = {
    // Azure Voice Live API WebSocket endpoint
    // This will be configured in Step 5 with real credentials
    endpoint: 'wss://eastus.api.azureml.ms/voice/live/v1/chat',
    
    // Voice Agent Configuration
    agent: {
        id: 'client_live_voice_agent',
        name: 'Voice Insurance Assistant',
        language: 'en-US',
        voice: 'en-US-AriaNeural'
    },
    
    // Audio Configuration
    audio: {
        sampleRate: 16000,
        channels: 1,
        format: 'pcm'
    },
    
    // A2A Agent Integration
    a2a: {
        agentUrl: 'http://localhost:8007',
        agentCardEndpoint: '/.well-known/agent.json'
    },
    
    // Development Configuration
    debug: true,
    logLevel: 'info'
};

// Configuration validation
if (window.VOICE_CONFIG.debug) {
    console.log('🔧 Voice configuration loaded:', window.VOICE_CONFIG);
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.VOICE_CONFIG;
}