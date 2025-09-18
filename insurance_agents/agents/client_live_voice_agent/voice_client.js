/**
 * Voice Client for A2A Agent Integration
 * Handles Azure Voice Live API WebSocket connection and A2A agent communication
 */

class VoiceInsuranceClient {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.isRecording = false;
        this.agentInfo = null;
        this.conversationHistory = [];
        this.sessionId = this.generateSessionId();
        this.conversationWebSocket = null;
        
        // UI Elements
        this.statusElement = document.getElementById('status');
        this.statusTextElement = document.getElementById('status-text');
        this.startButton = document.getElementById('start-button');
        this.stopButton = document.getElementById('stop-button');
        this.conversationElement = document.getElementById('conversation');
        this.agentInfoElement = document.getElementById('agent-info');
        
        this.initializeEventListeners();
        this.loadAgentInfo();
        this.initializeConversationTracking();
    }

    initializeEventListeners() {
        this.startButton.addEventListener('click', () => this.startVoiceConversation());
        this.stopButton.addEventListener('click', () => this.stopVoiceConversation());
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                this.websocket.close();
            }
            if (this.conversationWebSocket) {
                this.conversationWebSocket.close();
            }
        });
    }

    generateSessionId() {
        return `voice_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    initializeConversationTracking() {
        try {
            console.log('📝 Initializing conversation tracking...');
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/voice?session_id=${this.sessionId}`;
            
            console.log('🔗 Connecting to conversation tracker:', wsUrl);
            this.conversationWebSocket = new WebSocket(wsUrl);
            
            this.conversationWebSocket.onopen = () => {
                console.log('✅ Conversation tracking WebSocket connected');
                this.updateStatus('ready', 'Ready for voice conversation (tracking enabled)');
            };
            
            this.conversationWebSocket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('📨 Received from conversation tracker:', message);
                } catch (e) {
                    console.log('📨 Received from conversation tracker:', event.data);
                }
            };
            
            this.conversationWebSocket.onclose = () => {
                console.log('📝 Conversation tracking WebSocket disconnected');
            };
            
            this.conversationWebSocket.onerror = (error) => {
                console.error('❌ Conversation tracking WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('❌ Error initializing conversation tracking:', error);
        }
    }

    sendToConversationTracker(message) {
        if (this.conversationWebSocket && this.conversationWebSocket.readyState === WebSocket.OPEN) {
            try {
                this.conversationWebSocket.send(JSON.stringify(message));
            } catch (error) {
                console.error('❌ Error sending to conversation tracker:', error);
            }
        }
    }

    async loadAgentInfo() {
        try {
            console.log('🔍 Loading A2A agent information...');
            const response = await fetch('/.well-known/agent.json');
            
            if (!response.ok) {
                throw new Error(`Failed to load agent info: ${response.status}`);
            }
            
            this.agentInfo = await response.json();
            this.displayAgentInfo();
            console.log('✅ Agent information loaded:', this.agentInfo.name);
            
        } catch (error) {
            console.error('❌ Error loading agent info:', error);
            this.displayError('Failed to load agent information. Make sure the A2A agent is running.');
        }
    }

    displayAgentInfo() {
        if (!this.agentInfo) return;
        
        const skills = this.agentInfo.skills || [];
        const skillsHtml = skills.map(skill => 
            `<span class="skill-tag">${skill.name}</span>`
        ).join('');
        
        this.agentInfoElement.innerHTML = `
            <div class="agent-info">
                <h3>${this.agentInfo.name}</h3>
                <p><strong>Description:</strong> ${this.agentInfo.description}</p>
                <p><strong>Input Modes:</strong> ${(this.agentInfo.defaultInputModes || []).join(', ')}</p>
                <p><strong>Output Modes:</strong> ${(this.agentInfo.defaultOutputModes || []).join(', ')}</p>
                <div class="skills">
                    ${skillsHtml}
                </div>
            </div>
        `;
    }

    displayError(message) {
        this.agentInfoElement.innerHTML = `
            <div class="error">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }

    updateStatus(status, text) {
        this.statusElement.className = `status ${status}`;
        this.statusTextElement.textContent = text;
    }

    async startVoiceConversation() {
        if (this.isConnected) return;
        
        try {
            console.log('🎤 Starting voice conversation...');
            this.updateStatus('connecting', 'Connecting to Azure Voice Live API...');
            
            // Check if Voice Live API configuration is available
            if (!window.VOICE_CONFIG) {
                throw new Error('VOICE_CONFIG not found. Please ensure config.js is loaded.');
            }
            
            if (!window.VOICE_CONFIG.endpoint) {
                throw new Error('Voice Live API endpoint not configured. Please check config.js');
            }
            
            if (!window.VOICE_CONFIG.apiKey) {
                throw new Error('Voice Live API key not configured. Please check config.js');
            }
            
            console.log('✅ Voice configuration validated');
            console.log('Endpoint:', window.VOICE_CONFIG.endpoint);
            console.log('API Key length:', window.VOICE_CONFIG.apiKey?.length || 0);
            
            // Create WebSocket connection using the correct Azure Voice Live API format
            const websocketUrl = this.buildWebSocketUrl();
            console.log('🔗 Connecting to Azure Voice Live API:', websocketUrl.replace(/api-key=[^&]*/, 'api-key=***'));
            
            // Create WebSocket for Azure Voice Live API
            this.websocket = new WebSocket(websocketUrl);
            
            // Add authorization header for Azure OpenAI
            this.websocket.addEventListener('open', () => {
                console.log('✅ Connected to Azure Voice Live API');
                this.isConnected = true;
                this.updateStatus('connected', 'Connected - Voice conversation active');
                this.startButton.disabled = true;
                this.stopButton.disabled = false;
                
                // Send initial session configuration for OpenAI Realtime API
                this.sendRealtimeConfiguration();
            });
            
            this.websocket.addEventListener('message', (event) => {
                this.handleVoiceMessage(event);
            });
            
            this.websocket.addEventListener('close', (event) => {
                console.log('🔌 Voice Live API connection closed');
                console.log('Close code:', event.code, 'Reason:', event.reason);
                this.isConnected = false;
                this.updateStatus('disconnected', `Disconnected (${event.code}: ${event.reason || 'Unknown reason'})`);
                this.startButton.disabled = false;
                this.stopButton.disabled = true;
            });

            this.websocket.addEventListener('error', (error) => {
                console.error('❌ Voice Live API error:', error);
                console.error('Error details:', {
                    type: error.type,
                    target: error.target,
                    readyState: this.websocket?.readyState
                });
                this.updateStatus('disconnected', 'Connection error - Check console for details');
                this.addMessageToConversation('system', 'Voice connection error occurred. Please check the console for details.');
            });        } catch (error) {
            console.error('❌ Error starting voice conversation:', error);
            this.updateStatus('disconnected', 'Failed to connect');
            this.addMessageToConversation('system', `Error: ${error.message}`);
        }
    }

    buildWebSocketUrl() {
        // Convert HTTPS endpoint to WSS and build the correct URL format
        const endpoint = window.VOICE_CONFIG.endpoint.replace('https://', 'wss://').replace(/\/$/, '');
        const apiVersion = window.VOICE_CONFIG.apiVersion || '2025-05-01-preview';
        const model = window.VOICE_CONFIG.model;
        const apiKey = window.VOICE_CONFIG.apiKey;
        
        console.log('🔗 Building WebSocket URL with model:', model);
        const wsUrl = `${endpoint}/voice-live/realtime?api-version=${apiVersion}&model=${model}&api-key=${apiKey}`;
        
        return wsUrl;
    }

    sendRealtimeConfiguration() {
        if (!this.websocket || !this.isConnected) return;
        
        // Send session configuration for OpenAI Realtime API (Azure format)
        const sessionConfig = {
            type: 'session.update',
            session: {
                modalities: ['text', 'audio'],
                instructions: `You are a helpful insurance voice assistant. ${this.agentInfo?.instructions || 'Help users with insurance claims, definitions, and document guidance.'}`,
                voice: {
                    name: window.VOICE_CONFIG.agent.voice,
                    type: 'azure-standard'
                },
                input_audio_format: 'pcm16',
                output_audio_format: 'pcm16',
                input_audio_transcription: {
                    enabled: true,
                    model: 'whisper-1',
                    format: 'text'
                },
                turn_detection: {
                    type: 'azure_semantic_vad',
                    threshold: 0.4,
                    prefix_padding_ms: 300,
                    silence_duration_ms: 300,
                    remove_filler_words: true
                },
                input_audio_noise_reduction: {
                    type: 'azure_deep_noise_suppression'
                },
                input_audio_echo_cancellation: {
                    type: 'server_echo_cancellation'
                },
                tools: [],
                tool_choice: 'auto',
                temperature: 0.8,
                max_response_output_tokens: 4096
            }
        };
        
        console.log('📤 Sending session configuration:', sessionConfig);
        this.websocket.send(JSON.stringify(sessionConfig));
    }

    handleVoiceMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('📥 Received voice message:', message.type);
            
            // Send message to conversation tracker
            this.sendToConversationTracker(message);
            
            switch (message.type) {
                case 'session.created':
                    this.handleSessionCreated(message);
                    break;
                    
                case 'session.updated':
                    this.handleSessionUpdated(message);
                    break;
                    
                case 'input_audio_buffer.speech_started':
                    this.handleSpeechStarted(message);
                    break;
                    
                case 'input_audio_buffer.speech_stopped':
                    this.handleSpeechEnded(message);
                    break;
                    
                case 'conversation.item.input_audio_transcription.completed':
                    this.handleTranscript(message);
                    break;
                    
                case 'response.audio_transcript.delta':
                    this.handleAgentResponseDelta(message);
                    break;
                    
                case 'response.audio_transcript.done':
                    this.handleAgentResponseComplete(message);
                    break;
                    
                case 'response.audio.delta':
                    this.handleAudioData(message);
                    break;
                    
                case 'error':
                    this.handleVoiceError(message);
                    break;
                    
                default:
                    console.log('📨 Unknown message type:', message.type);
            }
            
        } catch (error) {
            console.error('❌ Error parsing voice message:', error);
        }
    }

    handleSessionCreated(message) {
        console.log('✅ Session created:', message.session?.id);
        this.addMessageToConversation('system', 'Voice session started - you can now speak');
    }

    handleSessionUpdated(message) {
        console.log('🔄 Session updated');
    }

    handleSpeechStarted(message) {
        console.log('🎤 Speech started');
        this.addMessageToConversation('system', 'Listening...');
        this.currentTranscript = '';
    }

    handleSpeechEnded(message) {
        console.log('🔇 Speech ended');
    }

    handleTranscript(message) {
        const transcript = message.transcript || '';
        console.log('📝 Transcript:', transcript);
        
        if (transcript.trim()) {
            this.addMessageToConversation('user', transcript);
            
            // Send to A2A agent for enhanced processing
            this.sendToA2AAgent(transcript);
        }
    }

    handleAgentResponseDelta(message) {
        const delta = message.delta || '';
        
        if (!this.currentResponse) {
            this.currentResponse = '';
        }
        
        this.currentResponse += delta;
        console.log('🤖 Response delta:', delta);
    }

    handleAgentResponseComplete(message) {
        const response = this.currentResponse || message.transcript || '';
        console.log('🤖 Complete response:', response);
        
        if (response.trim()) {
            this.addMessageToConversation('assistant', response);
        }
        
        this.currentResponse = '';
    }

    async sendToA2AAgent(userInput) {
        // This would integrate with the A2A agent for enhanced processing
        // For now, this is a placeholder for future A2A integration
        console.log('🔄 Would send to A2A agent:', userInput);
    }

    handleAudioData(message) {
        // Handle audio playback data
        console.log('🔊 Received audio data');
        // Implementation for audio playback would go here
    }

    handleVoiceError(message) {
        const error = message.error || 'Unknown voice error';
        console.error('❌ Voice error:', error);
        this.addMessageToConversation('system', `Voice error: ${error}`);
    }

    addMessageToConversation(sender, text) {
        const timestamp = new Date().toLocaleTimeString();
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        
        messageElement.innerHTML = `
            <div class="message-header">${this.formatSender(sender)} - ${timestamp}</div>
            <div>${this.escapeHtml(text)}</div>
        `;
        
        this.conversationElement.appendChild(messageElement);
        this.conversationElement.scrollTop = this.conversationElement.scrollHeight;
        
        // Add to conversation history
        this.conversationHistory.push({
            sender,
            text,
            timestamp: new Date().toISOString()
        });
        
        // Save conversation history
        this.saveConversationHistory();
    }

    formatSender(sender) {
        switch (sender) {
            case 'user': return 'You';
            case 'assistant': return 'Assistant';
            case 'system': return 'System';
            default: return sender;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    saveConversationHistory() {
        try {
            localStorage.setItem('voice_conversation_history', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.warn('⚠️ Could not save conversation history:', error);
        }
    }

    loadConversationHistory() {
        try {
            const saved = localStorage.getItem('voice_conversation_history');
            if (saved) {
                this.conversationHistory = JSON.parse(saved);
                
                // Display recent conversation history
                this.conversationHistory.slice(-10).forEach(msg => {
                    this.addMessageToConversation(msg.sender, msg.text);
                });
            }
        } catch (error) {
            console.warn('⚠️ Could not load conversation history:', error);
        }
    }
}

// Initialize the voice client when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Voice Insurance Client...');
    window.voiceClient = new VoiceInsuranceClient();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceInsuranceClient;
}