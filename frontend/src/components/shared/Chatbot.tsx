import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageSquare, Send, X, Bot } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

// --- Type Definitions ---
interface Course {
  item_id: string;
  title?: string | null;
  description?: string | null;
  url?: string | null;
  provider?: string | null;
  level?: string | null;
}

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
  recommendations?: Course[];
}

// --- Chatbot Component ---
export const Chatbot = () => {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const API_URL = 'http://localhost:8000';

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen && messages.length === 0) {
      setMessages([{ 
        sender: 'bot', 
        text: `Hello ${user?.full_name || 'there'}! I'm Nova, your AI assistant. How can I help you with your learning journey today?` 
      }]);
    }
  };

  const handleSend = async () => {
    if (input.trim() === '' || isLoading) return;
    
    const userMessage: ChatMessage = { sender: 'user', text: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('novalearn_token');
      if (!token) {
        throw new Error("You need to be logged in to use the chatbot.");
      }

      const response = await fetch(`${API_URL}/chatbot/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: currentInput })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      
      const botMessage: ChatMessage = {
        sender: 'bot',
        text: data.response || "I received your message but couldn't generate a response.",
        recommendations: data.recommendations || []
      };
      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage: ChatMessage = { 
        sender: 'bot', 
        text: "Sorry, I'm having trouble connecting right now. Please try again in a moment."
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages]);

  // Don't render if user is not logged in
  if (!user) return null;

  return (
    <>
      {/* Floating Chat Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <Button 
          onClick={handleToggle} 
          className="rounded-full w-16 h-16 shadow-lg bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center transition-all duration-200"
          aria-label={isOpen ? "Close chat" : "Open chat"}
        >
          {isOpen ? <X size={30} /> : <MessageSquare size={30} />}
        </Button>
      </div>

      {/* Chat Window */}
      {isOpen && (
        <Card className="fixed bottom-24 right-6 z-50 w-[400px] h-[60vh] max-h-[700px] flex flex-col shadow-2xl rounded-xl border-gray-200 overflow-hidden">
          {/* Header */}
          <CardHeader className="flex flex-row items-center justify-between bg-blue-600 text-white border-b shrink-0">
            <div className="flex items-center gap-3">
              <Bot className="h-6 w-6"/> 
              <CardTitle className="text-lg">Nova AI Assistant</CardTitle>
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={handleToggle} 
              className="text-white hover:bg-blue-700 hover:text-white"
              aria-label="Close chat"
            >
              <X className="h-5 w-5"/>
            </Button>
          </CardHeader>

          {/* Messages */}
          <CardContent className="flex-1 p-0 bg-gray-50 overflow-hidden">
            <ScrollArea className="h-full" ref={scrollAreaRef}>
              <div className="p-4 space-y-4">
                {messages.map((msg, index) => (
                  <div key={index} className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] p-3 rounded-xl ${
                      msg.sender === 'user' 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-white text-gray-800 shadow-sm'
                    }`}>
                      {/* Message Text */}
                      <div className="text-sm whitespace-pre-wrap break-words">
                        {msg.text}
                      </div>
                      
                      {/* Course Recommendations */}
                      {msg.recommendations && msg.recommendations.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <div className="text-xs font-semibold text-gray-600 border-t pt-2">
                            Recommended Courses:
                          </div>
                          {msg.recommendations.slice(0, 3).map(course => (
                            <a 
                              key={course.item_id} 
                              href={course.url || `/course/${course.item_id}`} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="block p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors duration-200 no-underline text-gray-800"
                            >
                              <div className="font-medium text-sm">{course.title || 'Untitled Course'}</div>
                              {course.provider && (
                                <div className="text-xs text-gray-600">{course.provider}</div>
                              )}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Loading Indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white text-gray-800 shadow-sm p-3 rounded-xl">
                      <div className="flex items-center space-x-1">
                        <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>

          {/* Input Footer */}
          <CardFooter className="border-t bg-white p-4 shrink-0">
            <div className="flex w-full items-center space-x-2">
              <Input
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="flex-1"
              />
              <Button 
                onClick={handleSend} 
                disabled={isLoading || input.trim() === ''} 
                className="bg-blue-600 hover:bg-blue-700 shrink-0"
                aria-label="Send message"
              >
                <Send className="h-4 w-4"/>
              </Button>
            </div>
          </CardFooter>
        </Card>
      )}
    </>
  );
}; 