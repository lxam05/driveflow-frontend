// Chatbot Widget Component
// Include this script in all HTML pages to add the chatbot functionality

(function() {
    'use strict';

    const API_URL = 'https://driving-test-backend-production.up.railway.app';
    
    // Create chatbot HTML structure
    const chatbotHTML = `
        <div id="chatbot-container" style="display: none;">
            <div id="chatbot-window">
                <div id="chatbot-header">
                    <h3>Driving Test Assistant</h3>
                    <button id="chatbot-close" aria-label="Close chatbot">×</button>
                </div>
                <div id="chatbot-messages"></div>
                <div id="chatbot-input-container">
                    <input 
                        type="text" 
                        id="chatbot-input" 
                        placeholder="Ask me about driving test questions..."
                        autocomplete="off"
                    >
                    <button id="chatbot-send" aria-label="Send message">Send</button>
                </div>
            </div>
        </div>
        <button id="chatbot-toggle" aria-label="Open chatbot">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        </button>
    `;

    // Create chatbot CSS
    const chatbotCSS = `
        <style id="chatbot-styles">
            #chatbot-toggle {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: var(--primary-blue, #5bc0be);
                border: 2px solid var(--accent-purple, #6fffe9);
                color: var(--bg-main, #0b132b);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 8px 24px rgba(91, 192, 190, 0.4);
                z-index: 9998;
                transition: all 0.3s ease;
                font-size: 24px;
                font-weight: bold;
            }

            #chatbot-toggle:hover {
                transform: scale(1.1);
                box-shadow: 0 12px 32px rgba(91, 192, 190, 0.6);
                background: var(--accent-purple, #6fffe9);
            }

            #chatbot-container {
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 380px;
                max-width: calc(100vw - 60px);
                height: 600px;
                max-height: calc(100vh - 140px);
                z-index: 9999;
                display: flex;
                flex-direction: column;
            }

            #chatbot-window {
                background: var(--bg-card, #2d3f5a);
                border: 1px solid var(--border-subtle, rgba(111, 255, 233, 0.2));
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                display: flex;
                flex-direction: column;
                height: 100%;
                overflow: hidden;
            }

            #chatbot-header {
                background: var(--bg-card-smaller, #3a506b);
                padding: 16px 20px;
                border-bottom: 1px solid var(--border-subtle, rgba(111, 255, 233, 0.2));
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            #chatbot-header h3 {
                margin: 0;
                font-size: 18px;
                font-weight: 700;
                color: var(--text-dark, #e5e7eb);
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
            }

            #chatbot-close {
                background: none;
                border: none;
                color: var(--text-light, #9ca3af);
                font-size: 28px;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: all 0.2s ease;
                line-height: 1;
            }

            #chatbot-close:hover {
                background: rgba(255, 255, 255, 0.1);
                color: var(--text-dark, #e5e7eb);
            }

            #chatbot-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 12px;
                scroll-behavior: smooth;
            }

            #chatbot-messages::-webkit-scrollbar {
                width: 6px;
            }

            #chatbot-messages::-webkit-scrollbar-track {
                background: var(--bg-main, #0b132b);
                border-radius: 3px;
            }

            #chatbot-messages::-webkit-scrollbar-thumb {
                background: var(--primary-blue, #5bc0be);
                border-radius: 3px;
            }

            .chatbot-message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 12px;
                font-size: 14px;
                line-height: 1.5;
                word-wrap: break-word;
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
            }

            .chatbot-message.user {
                align-self: flex-end;
                background: var(--primary-blue, #5bc0be);
                color: var(--bg-main, #0b132b);
                border-bottom-right-radius: 4px;
            }

            .chatbot-message.assistant {
                align-self: flex-start;
                background: var(--bg-card-smaller, #3a506b);
                color: var(--text-dark, #e5e7eb);
                border-bottom-left-radius: 4px;
                border: 1px solid var(--border-subtle, rgba(111, 255, 233, 0.2));
            }

            .chatbot-message.loading {
                align-self: flex-start;
                background: var(--bg-card-smaller, #3a506b);
                color: var(--text-light, #9ca3af);
                border: 1px solid var(--border-subtle, rgba(111, 255, 233, 0.2));
            }

            .chatbot-loading-dots {
                display: inline-flex;
                gap: 4px;
            }

            .chatbot-loading-dots span {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: var(--primary-blue, #5bc0be);
                animation: chatbot-pulse 1.4s ease-in-out infinite;
            }

            .chatbot-loading-dots span:nth-child(2) {
                animation-delay: 0.2s;
            }

            .chatbot-loading-dots span:nth-child(3) {
                animation-delay: 0.4s;
            }

            @keyframes chatbot-pulse {
                0%, 80%, 100% {
                    opacity: 0.3;
                    transform: scale(0.8);
                }
                40% {
                    opacity: 1;
                    transform: scale(1);
                }
            }

            #chatbot-input-container {
                padding: 16px 20px;
                border-top: 1px solid var(--border-subtle, rgba(111, 255, 233, 0.2));
                display: flex;
                gap: 10px;
                background: var(--bg-card-smaller, #3a506b);
            }

            #chatbot-input {
                flex: 1;
                padding: 12px 16px;
                background: var(--bg-card, #2d3f5a);
                border: 1px solid var(--border-subtle, rgba(111, 255, 233, 0.2));
                border-radius: 8px;
                color: var(--text-dark, #e5e7eb);
                font-size: 14px;
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
                outline: none;
                transition: border-color 0.2s ease;
            }

            #chatbot-input:focus {
                border-color: var(--primary-blue, #5bc0be);
            }

            #chatbot-input::placeholder {
                color: var(--text-light, #9ca3af);
            }

            #chatbot-send {
                padding: 12px 24px;
                background: var(--primary-blue, #5bc0be);
                border: none;
                border-radius: 8px;
                color: var(--bg-main, #0b132b);
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
            }

            #chatbot-send:hover:not(:disabled) {
                background: var(--accent-purple, #6fffe9);
                transform: translateY(-1px);
            }

            #chatbot-send:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            @media (max-width: 768px) {
                #chatbot-container {
                    right: 15px;
                    bottom: 80px;
                    width: calc(100vw - 30px);
                    height: calc(100vh - 120px);
                }

                #chatbot-toggle {
                    right: 15px;
                    bottom: 15px;
                    width: 56px;
                    height: 56px;
                }
            }
        </style>
    `;

    // Initialize chatbot
    function initChatbot() {
        // Check if user is authenticated
        const token = localStorage.getItem('auth_token');
        if (!token) {
            return; // Don't show chatbot if not logged in
        }

        // Inject CSS
        if (!document.getElementById('chatbot-styles')) {
            document.head.insertAdjacentHTML('beforeend', chatbotCSS);
        }

        // Inject HTML
        if (!document.getElementById('chatbot-container')) {
            document.body.insertAdjacentHTML('beforeend', chatbotHTML);
        }

        // Get elements
        const container = document.getElementById('chatbot-container');
        const toggle = document.getElementById('chatbot-toggle');
        const closeBtn = document.getElementById('chatbot-close');
        const messagesContainer = document.getElementById('chatbot-messages');
        const input = document.getElementById('chatbot-input');
        const sendBtn = document.getElementById('chatbot-send');

        // Conversation history
        let conversationHistory = [];

        // Toggle chatbot visibility
        function toggleChatbot() {
            const isVisible = container.style.display !== 'none';
            container.style.display = isVisible ? 'none' : 'flex';
            if (!isVisible) {
                input.focus();
            }
        }

        toggle.addEventListener('click', toggleChatbot);
        closeBtn.addEventListener('click', toggleChatbot);

        // Add message to chat
        function addMessage(text, isUser = false, isLoading = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chatbot-message ${isUser ? 'user' : isLoading ? 'loading' : 'assistant'}`;
            
            if (isLoading) {
                messageDiv.innerHTML = '<div class="chatbot-loading-dots"><span></span><span></span><span></span></div>';
            } else {
                messageDiv.textContent = text;
            }
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            return messageDiv;
        }

        // Send message to backend
        async function sendMessage(message, conversationHistory = []) {
            try {
                const token = localStorage.getItem('auth_token');
        
                if (!token) {
                    alert("❗ You must be logged in to use the chatbot.");
                    return;
                }
        
                const response = await fetch(`${API_URL}/chatbot/message`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        message: message,
                        conversationHistory: conversationHistory.slice(-10) // Keep last 10 for context
                    })
                });
        
                if (!response.ok) {
                    const error = await response.json().catch(() => ({}));
                    console.error("Chatbot API Error:", error);
                    alert("Chatbot error: " + (error.error || "Unknown server error"));
                    return;
                }
        
                const data = await response.json();
                console.log("AI Response:", data.response);
                return data.response;
            }
            catch (err) {
                console.error("SendMessage Error:", err);
                alert("Connection failed — are you logged in?");
            }
        }
        

        // Send on button click
        sendBtn.addEventListener('click', sendMessage);

        // Send on Enter key
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Add welcome message
        addMessage('Hello! I\'m your driving test assistant. Ask me anything about Irish driving test rules, road signs, theory questions, or test preparation!', false);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChatbot);
    } else {
        initChatbot();
    }
})();

