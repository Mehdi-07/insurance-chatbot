// In widget/src/app.jsx

import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import './index.css';

// This is the function Cursor just generated for us
const handleApiCall = async (messageText, apiKey) => {
  try {
    const response = await fetch('https://t-ai.onrender.com/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({ message: messageText }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching from API:", error);
    return { text: "Sorry, there was an error connecting to the server." };
  }
};


export function App() {
  const [isOpen, setIsOpen] = useState(true); // Default to open for easy dev
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null); // Ref to help us auto-scroll

  const WIDGET_API_KEY = "allahm3ajahl3aliboomboomchetetl9lawi1998morphoalbatros"; // <-- IMPORTANT

  // Function to automatically scroll to the latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]); // This effect runs every time the messages array changes

  // Main function to handle sending a message (user input or button click)
  const handleSendMessage = async (messageText) => {
    if (!messageText || messageText.trim() === '') return;

    // Add the user's message to the chat window immediately
    if (!messageText.startsWith("__CLICKED__")) {
      const userMessage = { sender: 'user', text: messageText };
      setMessages(prev => [...prev, userMessage]);
    }

    // Clear the input box if it was a typed message
    setInputValue('');

    // Call the API and get the bot's response
    const botResponseData = await handleApiCall(messageText, WIDGET_API_KEY);

    // Add the bot's complete response object to the chat history
    const botMessage = { ...botResponseData, sender: 'bot' };
    setMessages(prev => [...prev, botMessage]);
  };

  return (
    <div data-theme="tpi_theme">
      {/* Floating Chat Window */}
      {isOpen && (
        <div
          className="fixed bottom-24 right-5 sm:right-10 w-full max-w-md h-[70vh] max-h-[700px] z-50
            bg-white/80 backdrop-blur-lg border border-[#0057B8]/30 shadow-2xl rounded-2xl flex flex-col
            transition-all duration-300 ease-in-out animate-fade-in"
          style={{ boxShadow: '0 8px 32px 0 rgba(0, 87, 184, 0.18)' }}
        >
          {/* Header with Royal Blue gradient and close button */}
          <div className="bg-gradient-to-r from-[#0057B8] to-[#003974] text-white p-4 rounded-t-2xl flex justify-between items-center shadow-md">
            <h3 className="font-bold text-lg tracking-wide flex items-center gap-2">
              <span role='img' aria-label='chat'>💬</span> TPI Insurance Assistant
            </h3>
            <button className="btn btn-ghost btn-xs btn-circle text-white hover:bg-[#FFB81C]/80 transition-colors duration-200" onClick={() => setIsOpen(false)}>
              ✕
            </button>
          </div>

          {/* Message List Area */}
          <div className="flex-grow p-4 overflow-y-auto space-y-3 custom-scrollbar bg-white/0">
            {messages.length === 0 && (
              <div className="chat chat-start animate-fade-in">
                <div className="flex items-end gap-2">
                  <div className="avatar placeholder">
                    <div className="w-8 h-8 rounded-full bg-[#0057B8] flex items-center justify-center text-white font-bold border-2 border-white shadow">
                      <span>🤖</span>
                    </div>
                  </div>
                  <div className="chat-bubble bg-[#0057B8] text-white shadow animate-slide-in-left">Welcome to TPI! How can I help you?</div>
                </div>
              </div>
            )}
            {messages.map((msg, index) => (
              <div key={index} className={`chat ${msg.sender === 'user' ? 'chat-end' : 'chat-start'} animate-fade-in`}>
                <div className={`flex items-end gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>  
                  {/* Avatar */}
                  <div className="avatar placeholder">
                    <div className={`w-8 h-8 rounded-full border-2 border-white shadow ${msg.sender === 'user' ? 'bg-[#FFB81C] text-[#0057B8]' : 'bg-[#0057B8] text-white'}`}>
                      {msg.sender === 'user' ? <span>🧑</span> : <span>🤖</span>}
                    </div>
                  </div>
                  {/* Message bubble */}
                  <div className={`chat-bubble shadow-md animate-pop-in ${msg.sender === 'user' ? 'bg-[#FFB81C] text-[#0057B8]' : 'bg-[#0057B8] text-white'}`}>
                    <p>{msg.text}</p>
                    {/* If the bot message has buttons, render them */}
                    {msg.sender === 'bot' && msg.buttons && msg.buttons.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {msg.buttons.map((button, i) => (
                          <button
                            key={i}
                            className="btn btn-xs border-0 font-semibold text-[#0057B8] bg-[#FFB81C] hover:bg-[#FFD966] transition-colors duration-200 shadow"
                            onClick={() => handleSendMessage(`__CLICKED__:${button.value}`)}
                          >
                            {button.text}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="p-3 border-t border-[#0057B8]/20 bg-white/70 rounded-b-2xl flex gap-2">
            <input
              type="text"
              placeholder="Type a message..."
              className="input input-bordered flex-1 bg-white/90 focus:bg-white border-[#0057B8]/40 text-[#0057B8] placeholder-[#0057B8]/60"
              value={inputValue}
              onInput={e => setInputValue(e.currentTarget.value)}
              onKeyPress={e => e.key === 'Enter' && handleSendMessage(inputValue)}
            />
            <button className="btn font-bold text-white bg-[#0057B8] hover:bg-[#003974] border-0 shadow-md transition-colors duration-200" onClick={() => handleSendMessage(inputValue)}>
              Send
            </button>
          </div>
        </div>
      )}

      {/* Floating Launcher Button */}
      {!isOpen && (
        <button
          className="fixed bottom-5 right-5 sm:right-10 btn btn-circle w-16 h-16 shadow-2xl z-50 flex items-center justify-center text-3xl animate-bounce border-4 border-[#FFB81C] bg-[#0057B8] text-white hover:bg-[#003974] transition-colors duration-200"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Open chat"
        >
          <span role="img" aria-label="chat">💬</span>
        </button>
      )}
      {/* Animations */}
      <style>{`
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        .animate-fade-in { animation: fade-in 0.5s ease; }
        @keyframes pop-in { 0% { transform: scale(0.95); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        .animate-pop-in { animation: pop-in 0.25s cubic-bezier(.4,2,.6,1) both; }
        @keyframes slide-in-left { from { transform: translateX(-20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .animate-slide-in-left { animation: slide-in-left 0.4s cubic-bezier(.4,2,.6,1) both; }
        .custom-scrollbar::-webkit-scrollbar { width: 8px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #0057B8; border-radius: 4px; }
        .custom-scrollbar { scrollbar-width: thin; scrollbar-color: #0057B8 #fff; }
      `}</style>
    </div>
  );
}