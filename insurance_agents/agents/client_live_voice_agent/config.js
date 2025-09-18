// Configuration file for Azure AI Services and Database connections
// This file contains actual API keys and should NOT be committed to version control
// Make sure config.js is in .gitignore

window.AZURE_CONFIG = {
    // Azure Voice Live API Configuration
    endpoint: "https://voice-liveresource.cognitiveservices.azure.com/",
    apiKey: "8HWK9Rh0rN98xrMJmnqC7ExKilopJZ6Qepafo6kkqUJlV1VO8ixeJQQJ99BIACHYHv6XJ3w3AAAAACOGahbN",
    model: "gpt-4o-realtime-preview",
    voice: "en-US-JennyMultilingualNeural"
};

window.COSMOS_CONFIG = {
    // Cosmos DB Configuration for Claims Data
    endpoint: "https://macae-cosmos-7dfokqmjfelni.documents.azure.com:443/",
    key: "AkdZ8vkUxrSm1obmhCgOF50AGM2y7ACLwGfV48vHyXHo0GCm5fov2nLPLIPz8o1pFspk7Dl5QpqHACDbLoFBmw==",
    database: "insurance",
    container: "claim_details"
};

// Legacy naming for compatibility
window.VOICE_CONFIG = window.AZURE_CONFIG;

console.log('✅ Config loaded - Azure endpoint:', window.AZURE_CONFIG.endpoint);
console.log('✅ Config loaded - Model:', window.AZURE_CONFIG.model);
console.log('✅ Config loaded - Voice:', window.AZURE_CONFIG.voice);