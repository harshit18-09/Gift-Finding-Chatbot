class GiftChatbot {
    constructor() {
        this.backendUrl = 'https://your-backend-url.vercel.app/api/chat'; // Update this after deployment
        this.conversationId = 'gift_chat_' + Date.now();
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.suggestionsChips = document.getElementById('suggestionsChips');
        this.giftPanel = document.getElementById('giftPanel');
        this.giftList = document.getElementById('giftList');
        this.closePanel = document.getElementById('closePanel');
        
        this.initializeEventListeners();
        this.showWelcomeMessage();
        this.loadDefaultSuggestions();
    }
    
    initializeEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.closePanel.addEventListener('click', () => {
            this.giftPanel.style.display = 'none';
        });
        
        // Auto-hide gift panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.giftPanel.contains(e.target) && 
                !e.target.closest('.message-content') &&
                this.giftPanel.style.display === 'flex') {
                this.giftPanel.style.display = 'none';
            }
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        // Show typing indicator
        const typingId = this.showTypingIndicator();
        
        try {
            const response = await fetch(this.backendUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            // Add bot response
            this.addMessage(data.reply, 'bot');
            
            // Update suggestions
            this.updateSuggestions(data.suggestions);
            
            // Show gift suggestions if available
            if (data.gifts && data.gifts.length > 0) {
                this.showGiftSuggestions(data.gifts);
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage('Sorry, I encountered an error. Please try again or check the backend connection.', 'bot');
        }
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(text)}
                <div class="message-time">${time}</div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Add click handler for gift-related messages
        if (sender === 'bot' && text.toLowerCase().includes('gift')) {
            messageDiv.querySelector('.message-content').style.cursor = 'pointer';
            messageDiv.querySelector('.message-content').addEventListener('click', () => {
                this.giftPanel.style.display = 'flex';
            });
        }
    }
    
    formatMessage(text) {
        // Convert markdown-like formatting to HTML
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/- (.*?)(?:\n|$)/g, '<li>$1</li>')
            .replace(/(\d+)\. (.*?)(?:\n|$)/g, '<li>$2</li>')
            .replace(/\n/g, '<br>');
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';
        
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
        
        return 'typing-indicator';
    }
    
    removeTypingIndicator(id) {
        const typingElement = document.getElementById(id);
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    updateSuggestions(suggestions) {
        this.suggestionsChips.innerHTML = '';
        
        // Add default suggestions if none provided
        if (!suggestions || suggestions.length === 0) {
            suggestions = [
                "Birthday gifts",
                "Christmas presents",
                "Anniversary ideas",
                "Under $50",
                "For teenagers"
            ];
        }
        
        suggestions.forEach(suggestion => {
            const chip = document.createElement('div');
            chip.className = 'chip';
            chip.innerHTML = `<i class="fas fa-lightbulb"></i> ${suggestion}`;
            chip.addEventListener('click', () => {
                this.messageInput.value = suggestion;
                this.messageInput.focus();
            });
            this.suggestionsChips.appendChild(chip);
        });
    }
    
    showGiftSuggestions(gifts) {
        this.giftList.innerHTML = '';
        
        gifts.forEach(gift => {
            const giftCard = document.createElement('div');
            giftCard.className = 'gift-card';
            
            giftCard.innerHTML = `
                <h4><i class="fas fa-gift"></i> ${gift.gift}</h4>
                <p><strong>Why it's perfect:</strong> ${gift.reason}</p>
                <span class="gift-price">${gift.price_range}</span>
            `;
            
            this.giftList.appendChild(giftCard);
        });
        
        this.giftPanel.style.display = 'flex';
    }
    
    showWelcomeMessage() {
        setTimeout(() => {
            this.addMessage(
                "Hello! I'm your Gift Finding Assistant. 🎁\n\n" +
                "I can help you find the perfect gift for any occasion. Tell me about the person you're shopping for!\n\n" +
                "Please include:\n" +
                "• Who the gift is for (relationship)\n" +
                "• Their age and interests\n" +
                "• The occasion (birthday, holiday, etc.)\n" +
                "• Your budget if you have one",
                'bot'
            );
        }, 500);
    }
    
    loadDefaultSuggestions() {
        const defaultSuggestions = [
            "For my mother's birthday",
            "Christmas gift for boyfriend",
            "Anniversary gift for wife",
            "Graduation gift for sister",
            "Budget under $50",
            "Tech lover gifts",
            "Book lover presents",
            "Outdoor enthusiast"
        ];
        
        this.updateSuggestions(defaultSuggestions);
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new GiftChatbot();
    
    // Add CSS for typing indicator
    const style = document.createElement('style');
    style.textContent = `
        .typing {
            display: inline-flex;
            align-items: center;
            height: 20px;
        }
        
        .typing span {
            height: 8px;
            width: 8px;
            background: #667eea;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1s infinite ease-in-out;
        }
        
        .typing span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
    `;
    document.head.appendChild(style);
});