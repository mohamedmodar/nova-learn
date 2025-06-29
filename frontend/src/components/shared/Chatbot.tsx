import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageSquare, Send, X, Bot, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

export const Chatbot = () => {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen && messages.length === 0) {
      setMessages([{ sender: 'bot', text: "Hello! How can I help you today?" }]);
    }
  };

  const handleSend = async () => {
    if (input.trim() === '') return;
    
    const userMessage: ChatMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Fake bot response for now
    setTimeout(() => {
      const botMessage: ChatMessage = { sender: 'bot', text: "This is a test response." };
      setMessages(prev => [...prev, botMessage]);
      setIsLoading(false);
    }, 1000);
  };

  useEffect(() => {
    if (scrollAreaRef.current) {
        const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
        if (viewport) viewport.scrollTop = viewport.scrollHeight;
    }
  }, [messages]);

  if (!user) return null;

  return (
    <>
      <div className="fixed bottom-6 right-6 z-50">
        <Button 
          onClick={handleToggle} 
          className="rounded-full w-16 h-16 shadow-lg bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center"
        >
          {isOpen ? <X size={30} /> : <MessageSquare size={30} />}
        </Button>
      </div>

      {isOpen && (
        <Card className="fixed bottom-24 right-6 z-50 w-[400px] h-[60vh] max-h-[700px] flex flex-col shadow-2xl rounded-xl border-gray-200 overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between bg-blue-600 text-white border-b">
            <div className="flex items-center gap-3">
              <Bot className="h-6 w-6"/> 
              <CardTitle className="text-lg">Nova AI Assistant</CardTitle>
            </div>
            <Button variant="ghost" size="icon" onClick={handleToggle} className="text-white hover:bg-blue-700 hover:text-white">
              <X className="h-5 w-5"/>
            </Button>
          </CardHeader>
          <CardContent className="flex-1 p-0 bg-gray-50">
            <ScrollArea className="h-full" ref={scrollAreaRef}>
              <div className="p-4 space-y-4">
                {messages.map((msg, index) => (
                  <div key={index} className={`flex items-start gap-3 w-full ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                    <div className={`text-sm max-w-[85%] p-3 rounded-xl ${ msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800 shadow-sm' }`}>
                      <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                    </div>
                  </div>
                ))}
                 {isLoading && (
                    <div className="flex items-start gap-3">
                         <div className="prose text-sm max-w-[85%] p-3 rounded-xl bg-white text-gray-800 shadow-sm">
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
          <CardFooter className="border-t bg-white p-4">
            <div className="flex w-full items-center space-x-2">
              <Input
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                disabled={isLoading}
              />
              <Button onClick={handleSend} disabled={isLoading} className="bg-blue-600 hover:bg-blue-700">
                <Send className="h-4 w-4"/>
              </Button>
            </div>
          </CardFooter>
        </Card>
      )}
    </>
  );
}; 