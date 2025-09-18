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
        
        // UI Elements
        this.statusElement = document.getElementById('status');
        this.statusTextElement = document.getElementById('status-text');
        this.startButton = document.getElementById('start-button');
        this.stopButton = document.getElementById('stop-button');
        this.conversationElement = document.getElementById('conversation');
        this.agentInfoElement = document.getElementById('agent-info');
        
        this.initializeEventListeners();
        this.loadAgentInfo();
    }

    initializeEventListeners() {
        this.startButton.addEventListener('click', () => this.startVoiceConversation());
        this.stopButton.addEventListener('click', () => this.stopVoiceConversation());
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                this.websocket.close();
            }
        });
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
            if (!window.VOICE_CONFIG || !window.VOICE_CONFIG.endpoint) {
                throw new Error('Voice Live API configuration not found. Please check config.js');
            }
            
            // Create WebSocket connection to Azure Voice Live API
            const websocketUrl = window.VOICE_CONFIG.endpoint;
            console.log('🔗 Connecting to:', websocketUrl);
            
            this.websocket = new WebSocket(websocketUrl);
            
            this.websocket.onopen = () => {
                console.log('✅ Connected to Azure Voice Live API');
                this.isConnected = true;
                this.updateStatus('connected', 'Connected - Voice conversation active');
                this.startButton.disabled = true;
                this.stopButton.disabled = false;
                
                // Send initial configuration
                this.sendVoiceConfiguration();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleVoiceMessage(event);
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 Voice Live API connection closed');
                this.isConnected = false;
                this.updateStatus('disconnected', 'Disconnected');
                this.startButton.disabled = false;
                this.stopButton.disabled = true;
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ Voice Live API error:', error);
                this.updateStatus('disconnected', 'Connection error');
                this.addMessageToConversation('system', 'Voice connection error occurred');
            };
            
        } catch (error) {
            console.error('❌ Error starting voice conversation:', error);
            this.updateStatus('disconnected', 'Failed to connect');
            this.addMessageToConversation('system', `Error: ${error.message}`);
        }
    }

    stopVoiceConversation() {
        if (!this.isConnected) return;
        
        console.log('🛑 Stopping voice conversation...');
        
        if (this.websocket) {
            this.websocket.close();
        }
        
        this.isConnected = false;
        this.updateStatus('disconnected', 'Disconnected');
        this.startButton.disabled = false;
        this.stopButton.disabled = true;
        
        this.addMessageToConversation('system', 'Voice conversation ended');
    }

    sendVoiceConfiguration() {
        if (!this.websocket || !this.isConnected) return;
        
        // Send configuration to Azure Voice Live API
        const config = {
            type: 'configuration',
            audio: {
                input: {
                    format: 'pcm',
                    sampleRate: 16000,
                    channels: 1
                },
                output: {
                    format: 'pcm',
                    sampleRate: 16000,
                    channels: 1
                }
            },
            agent: {
                id: this.agentInfo?.id || 'client_live_voice_agent',
                name: this.agentInfo?.name || 'Voice Insurance Assistant',
                instructions: this.agentInfo?.instructions || 'Provide voice-based insurance assistance'
            }
        };
        
        console.log('📤 Sending voice configuration:', config);
        this.websocket.send(JSON.stringify(config));
    }

    handleVoiceMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('📥 Received voice message:', message.type);
            
            switch (message.type) {
                case 'speech_started':
                    this.handleSpeechStarted(message);
                    break;
                    
                case 'speech_ended':
                    this.handleSpeechEnded(message);
                    break;
                    
                case 'transcript':
                    this.handleTranscript(message);
                    break;
                    
                case 'response':
                    this.handleAgentResponse(message);
                    break;
                    
                case 'audio':
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

    handleSpeechStarted(message) {
        console.log('🎤 Speech started');
        this.addMessageToConversation('system', 'Listening...');
    }

    handleSpeechEnded(message) {
        console.log('🔇 Speech ended');
    }

    handleTranscript(message) {
        const transcript = message.text || message.transcript || '';
        console.log('📝 Transcript:', transcript);
        
        if (transcript.trim()) {
            this.addMessageToConversation('user', transcript);
        }
    }

    async handleAgentResponse(message) {
        const response = message.text || message.response || '';
        console.log('🤖 Agent response:', response);
        
        if (response.trim()) {
            this.addMessageToConversation('assistant', response);
            
            // Send response to A2A agent for processing
            await this.sendToA2AAgent(response);
        }
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