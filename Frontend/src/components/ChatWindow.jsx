import React, { useEffect, useRef } from 'react';

const ChatWindow = ({ messages }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Welcome to Echocare. Start by speaking or recording your thoughts.</p>
          </div>
        ) : (
          messages.map(message => (
            <div 
              key={message.id} 
              className={`message-wrapper ${message.role === 'user' ? 'user' : 'assistant'}`}
            >
              <div className={`message-bubble ${message.role}`}>
                {message.text}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;