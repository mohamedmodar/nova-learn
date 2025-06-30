import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Send, X, Bot, ExternalLink, ArrowRight, HelpCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

// --- Enhanced Type Definitions ---
interface Course {
  item_id: string;
  title?: string | null;
  description?: string | null;
  url?: string | null;
  provider?: string | null;
  level?: string | null;
  reasoning?: string | null;
}

interface EnhancedChatMessage {
  sender: 'user' | 'bot';
  text: string;
  recommendations?: Course[];
  suggested_actions?: string[];
  follow_up_questions?: string[];
  timestamp: Date;
}

// --- Enhanced Chatbot Component ---
export const Chatbot = () => {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<EnhancedChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const API_URL = 'http://localhost:8000';

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen && messages.length === 0) {
      setMessages([{ 
        sender: 'bot', 
        text: `Hello ${user?.full_name || 'there'}! I'm Nova, your enhanced AI learning assistant. I can help you with:
        
• Finding personalized course recommendations
• Creating custom learning paths
• Developing study plans
• Explaining complex concepts
• Tracking your progress

What would you like to explore today?`,
        timestamp: new Date(),
        suggested_actions: [
          "Ask for course recommendations",
          "Request a learning path", 
          "Get help with a concept"
        ]
      }]);
    }
  };

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input.trim();
    if (textToSend === '' || isLoading) return;
    
    const userMessage: EnhancedChatMessage = { 
      sender: 'user', 
      text: textToSend,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
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
        body: JSON.stringify({ message: textToSend })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      
      const botMessage: EnhancedChatMessage = {
        sender: 'bot',
        text: data.response || "I received your message but couldn't generate a response.",
        recommendations: data.recommendations || [],
        suggested_actions: data.suggested_actions || [],
        follow_up_questions: data.follow_up_questions || [],
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage: EnhancedChatMessage = { 
        sender: 'bot', 
        text: "Sorry, I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action: string) => {
    handleSend(action);
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
          aria-label={isOpen ? "Close chat" : "Open Nova AI Assistant"}
        >
          {isOpen ? <X size={30} /> : <MessageSquare size={30} />}
        </Button>
      </div>

      {/* Enhanced Chat Window */}
      {isOpen && (
        <Card className="fixed bottom-24 right-6 z-50 w-[420px] h-[70vh] max-h-[750px] flex flex-col shadow-2xl rounded-xl border-gray-200 overflow-hidden">
          {/* Enhanced Header */}
          <CardHeader className="flex flex-row items-center justify-between bg-gradient-to-r from-blue-600 to-indigo-600 text-white border-b shrink-0">
            <div className="flex items-center gap-3">
              <Bot className="h-6 w-6"/> 
              <div>
                <CardTitle className="text-lg">Nova AI Assistant</CardTitle>
              
              </div>
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

          {/* Enhanced Messages */}
          <CardContent className="flex-1 p-0 bg-gray-50 overflow-hidden">
            <ScrollArea className="h-full" ref={scrollAreaRef}>
              <div className="p-4 space-y-4">
                {messages.map((msg, index) => (
                  <div key={index} className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] ${
                      msg.sender === 'user' 
                        ? 'bg-blue-500 text-white rounded-xl p-3' 
                        : 'space-y-3'
                    }`}>
                      {/* Message Text */}
                      {msg.sender === 'user' ? (
                        <div className="text-sm whitespace-pre-wrap break-words">
                          {msg.text}
                        </div>
                      ) : (
                        <div className="bg-white text-gray-800 shadow-sm p-3 rounded-xl">
                          <div className="text-sm whitespace-pre-wrap break-words">
                            {msg.text}
                          </div>
                        </div>
                      )}
                      
                      {/* Course Recommendations */}
                      {msg.recommendations && msg.recommendations.length > 0 && (
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
                            <ExternalLink className="h-3 w-3" />
                            Recommended Courses:
                          </div>
                          {msg.recommendations.slice(0, 3).map(course => (
                            <a 
                              key={course.item_id} 
                              href={course.url || `/course/${course.item_id}`} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="block p-3 bg-white rounded-lg hover:bg-blue-50 transition-colors duration-200 border border-gray-200 shadow-sm"
                            >
                              <div className="font-medium text-sm text-gray-800 mb-1">
                                {course.title || 'Untitled Course'}
                              </div>
                              {course.provider && (
                                <div className="text-xs text-gray-600 mb-1">
                                  📚 {course.provider}
                                </div>
                              )}
                              {course.reasoning && (
                                <div className="text-xs text-blue-600 italic">
                                  💡 {course.reasoning}
                                </div>
                              )}
                            </a>
                          ))}
                        </div>
                      )}

                      {/* Suggested Actions */}
                      {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
                            <ArrowRight className="h-3 w-3" />
                            Suggested Actions:
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {msg.suggested_actions.map((action, idx) => (
                              <Button
                                key={idx}
                                variant="outline"
                                size="sm"
                                onClick={() => handleQuickAction(action)}
                                className="text-xs h-8 bg-white hover:bg-blue-50 border-blue-200"
                              >
                                {action}
                              </Button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Follow-up Questions */}
                      {msg.follow_up_questions && msg.follow_up_questions.length > 0 && (
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
                            <HelpCircle className="h-3 w-3" />
                            You might also ask:
                          </div>
                          <div className="space-y-1">
                            {msg.follow_up_questions.map((question, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleQuickAction(question)}
                                className="block w-full text-left text-xs p-2 bg-gray-100 hover:bg-blue-100 rounded-md transition-colors duration-200 text-gray-700"
                              >
                                💭 {question}
                              </button>
                            ))}
                          </div>
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
                        <span className="h-2 w-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="h-2 w-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="h-2 w-2 bg-blue-400 rounded-full animate-bounce"></span>
                        <span className="text-xs text-gray-600 ml-2">Nova is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>

          {/* Enhanced Input Footer */}
          <CardFooter className="border-t bg-white p-4 shrink-0">
            <div className="w-full space-y-3">
              {/* Quick Actions Bar */}
              <div className="flex flex-wrap gap-2">
                <Badge 
                  variant="outline" 
                  className="cursor-pointer hover:bg-blue-50"
                  onClick={() => handleQuickAction("I want to learn Python")}
                >
                  🐍 Learn Python
                </Badge>
                <Badge 
                  variant="outline" 
                  className="cursor-pointer hover:bg-blue-50"
                  onClick={() => handleQuickAction("Create a study plan for me")}
                >
                  📚 Study Plan
                </Badge>
                <Badge 
                  variant="outline" 
                  className="cursor-pointer hover:bg-blue-50"
                  onClick={() => handleQuickAction("Explain machine learning")}
                >
                  🤖 ML Help
                </Badge>
              </div>
              
              {/* Input Area */}
              <div className="flex w-full items-center space-x-2">
                <Input
                  placeholder="Ask Nova anything about learning..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button 
                  onClick={() => handleSend()} 
                  disabled={isLoading || input.trim() === ''} 
                  className="bg-blue-600 hover:bg-blue-700 shrink-0"
                  aria-label="Send message"
                >
                  <Send className="h-4 w-4"/>
                </Button>
              </div>
            </div>
          </CardFooter>
        </Card>
      )}
    </>
  );
}; 