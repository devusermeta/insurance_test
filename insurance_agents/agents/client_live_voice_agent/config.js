/**
 * Voice Client Configuration
 * Azure Voice Live API configuration for the A2A Voice Agent
 * This file contains actual API keys and should NOT be committed to version control
 */

// Azure Voice Live API Configuration (Real credentials from client_live_voice)
window.VOICE_CONFIG = {
    // Azure Voice Live API WebSocket endpoint
    endpoint: 'wss://voice-liveresource.cognitiveservices.azure.com/openai/realtime?api-version=2024-10-01-preview',
    apiKey: '8HWK9Rh0rN98xrMJmnqC7ExKilopJZ6Qepafo6kkqUJlV1VO8ixeJQQJ99BIACHYHv6XJ3w3AAAAACOGahbN',
    model: 'gpt-4o-realtime-preview',
    
    // Voice Agent Configuration
    agent: {
        id: 'client_live_voice_agent',
        name: 'Voice Insurance Assistant',
        language: 'en-US',
        voice: 'en-US-JennyMultilingualNeural'
    },
    
    // Audio Configuration
    audio: {
        sampleRate: 24000,
        channels: 1,
        format: 'pcm16'
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
    console.log('Voice configuration loaded with Azure Voice Live API');
    console.log('Model:', window.VOICE_CONFIG.model);
    console.log('Voice:', window.VOICE_CONFIG.agent.voice);
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.VOICE_CONFIG;
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.VOICE_CONFIG;
}