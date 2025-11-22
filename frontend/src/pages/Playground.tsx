import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Send, ChevronLeft, Bot, User } from "lucide-react";
import MapView from "@/components/MapView";

const Playground = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // State for the full data object
  const [data, setData] = useState<any>(location.state?.initialData || {});
  
  // Derived state
  const [currentRecIndex, setCurrentRecIndex] = useState(0);
  const currentRec = data?.recommendations?.[currentRecIndex] || {};
  const mapActions = currentRec.map_actions || [];

  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>(() => {
    const history = data?.message_history || [];
    const initialChatbotText = data?.chatbot_text;
    
    // If we have history, check if we need to append the initial response
    if (history.length > 0) {
      const lastMsg = history[history.length - 1];
      // If the last message is from user, we should append the assistant's response
      if (lastMsg.role === 'user' && initialChatbotText) {
        return [...history, { role: 'assistant', content: initialChatbotText }];
      }
      return history;
    }
    
    // Fallback
    return [
      { role: 'assistant', content: initialChatbotText || 'Hola! Basándome en tu descripción, te voy a mostrar los mejores barrios para ti. ¿Qué más te gustaría saber?' }
    ];
  });

  const [input, setInput] = useState("");
  const [expandedButton, setExpandedButton] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Map top 5 variables to button labels
  const buttonLabels = (currentRec.top_5_variables || []).map((v: any, idx: number) => ({
    id: idx + 1,
    title: v.variable_name,
    content: v.justification
  }));

  // Atwater Village polygon (Default or dynamic if available)
  const atwaterVillagePolygon = currentRec.map_polygon || "POLYGON ((-118.30068619528 34.0373138507143, -118.303884196041 34.037204851199, -118.300287171334 34.0372359462978, -118.297604625712 34.0372591365581, -118.296712194924 34.0372668512001, -118.296295194457 34.0372348512573, -118.29636119452 34.036894851016, -118.291561193707 34.0368418515945, -118.291550192661 34.0255018502656, -118.291552596393 34.0255018543774, -118.308899196446 34.025557849759, -118.309000196885 34.0374328504795, -118.30801419718 34.0374008510931, -118.30068619528 34.0373138507143))";

  const [activeMapAction, setActiveMapAction] = useState<any>(null);

  const handleMapAction = (action: any) => {
    console.log("Action clicked:", action);
    setActiveMapAction(action);
  };

  const formatMessage = (content: string) => {
    // Simple bold parser: **text** -> <strong>text</strong>
    const parts = content.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-bold text-white">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMsg = input;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput("");
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }),
      });
      
      if (!response.ok) throw new Error('Network response was not ok');
      
      const newData = await response.json();
      
      // Simulate process logs
      if (newData.process_log && Array.isArray(newData.process_log)) {
        for (const step of newData.process_log) {
           setMessages(prev => [...prev, { role: 'assistant', content: `⚙️ ${step}` }]);
           await new Promise(r => setTimeout(r, 800));
        }
      }
      
      // Update full data state
      setData(newData);
      
      // Update messages - Remove process logs and add final response
      setMessages(prev => {
        const filtered = prev.filter(m => !m.content.startsWith('⚙️'));
        return [...filtered, { role: 'assistant', content: newData.chatbot_text }];
      });
      
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Lo siento, hubo un error al procesar tu mensaje." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative h-screen w-full overflow-hidden">
      {/* Background Video */}
      <div className="absolute inset-0 z-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="h-full w-full object-cover"
        >
          <source src="/LA_Loop.mp4" type="video/mp4" />
        </video>
        {/* Dark overlay */}
        <div className="absolute inset-0 bg-black/40" />
      </div>

      {/* Main Content Container */}
      <div className="relative z-10 h-screen w-full flex">
        {/* Chat Sidebar - Left 25% */}
        <div className="w-1/4 h-full backdrop-blur-xl bg-black/40 border-r border-white/10 flex flex-col shadow-2xl">
          {/* Header */}
          <div className="p-4 border-b border-white/10 flex items-center gap-3 bg-white/5">
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => navigate("/")}
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h2 className="font-light text-white tracking-wider">COMPASS AI</h2>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  msg.role === 'user' ? 'bg-white/20' : 'bg-transparent'
                }`}>
                  {msg.role === 'user' ? (
                    <User className="h-4 w-4 text-white" />
                  ) : (
                    null
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-white/20 backdrop-blur-md text-white rounded-tr-none'
                      : 'bg-black/40 backdrop-blur-md text-gray-100 rounded-tl-none border border-white/10'
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {formatMessage(msg.content)}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/10 bg-white/5">
            <div className="flex gap-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Pregunta sobre los barrios..."
                className="min-h-[44px] max-h-[120px] resize-none bg-black/20 backdrop-blur-sm border-white/10 text-white placeholder:text-white/40 focus-visible:ring-white/20"
              />
              <Button 
                onClick={handleSend}
                size="icon"
                disabled={!input.trim() || isLoading}
                className="bg-white/20 hover:bg-white/30 text-white transition-colors"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content - Right 75% */}
        <div className="w-3/4 h-full flex flex-col p-8 gap-6">
          {/* Neighborhood Title */}
          <div className="w-full">
            <h1 className="text-4xl font-light tracking-tight text-white">
              {currentRec.name || "Cargando..."}
            </h1>
          </div>

          {/* Bottom Section - Justification and Map */}
          <div className="flex-1 flex gap-6">
            {/* Left - Justification (takes remaining space) */}
            <div className="flex-1 flex flex-col gap-6">
              {/* Top section - 1/4 */}
              <div className="h-1/4 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-lg overflow-y-auto">
                <p className="text-sm text-white/90 leading-relaxed">
                  {currentRec.overview || "Selecciona un barrio para ver los detalles."}
                </p>
              </div>

              {/* Bottom section - 3/4 split horizontally with fixed proportions */}
              <div className="flex-1 flex gap-6">
                {/* Left container - 3/4 - 5 clickable sections or expanded content */}
                <div className="w-3/4 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-lg overflow-hidden">
                  {expandedButton === null ? (
                    <div className="h-full flex flex-col">
                      {buttonLabels.map((btn: any) => (
                        <button
                          key={btn.id}
                          onClick={() => setExpandedButton(btn.id)}
                          className="flex-1 border-b border-white/10 last:border-b-0 hover:bg-white/5 transition-colors flex items-center justify-center text-white/90 text-sm px-4 text-center"
                        >
                          {btn.title}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="h-full p-6 flex flex-col">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedButton(null)}
                        className="self-start mb-4 text-white hover:bg-white/10"
                      >
                        <ChevronLeft className="h-4 w-4 mr-2" />
                        Volver
                      </Button>
                      <div className="flex-1 overflow-y-auto">
                        <h3 className="text-xl font-light text-white mb-4">
                          {buttonLabels.find((b: any) => b.id === expandedButton)?.title}
                        </h3>
                        <p className="text-sm text-white/90 leading-relaxed">
                          {buttonLabels.find((b: any) => b.id === expandedButton)?.content}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Right container - 1/4 - Map Actions */}
                <div className="w-1/4 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-lg overflow-hidden flex flex-col">
                  {mapActions.map((action: any, idx: number) => (
                    <button
                      key={idx}
                      className={`flex-1 border-b border-white/10 last:border-b-0 hover:bg-white/5 transition-all flex items-center justify-center text-white/90 text-xs font-light hover:font-normal px-2 text-center ${activeMapAction === action ? 'bg-white/20 font-normal' : ''}`}
                      onClick={() => handleMapAction(action)}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right - Map */}
            <div className="w-1/3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl overflow-hidden shadow-lg">
              <MapView 
                polygonCoordinates={atwaterVillagePolygon} 
                activeAction={activeMapAction}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Playground;
