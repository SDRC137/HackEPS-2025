import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Send, ChevronLeft, ChevronRight, Bot, User } from "lucide-react";
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
  
  const mapContext = currentRec.map_context || {};
  const mapButtons = mapContext.buttons || [];
  const mapLines = mapContext.lines || [];

  // Combine lines and buttons for the UI list, adapting to the component's expected format
  const mapActions = [
    ...mapLines.map((l: any) => ({
      label: l.label,
      type: 'line',
      action: 'show_line',
      data: l 
    })),
    ...mapButtons
  ];

  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string, recommendations?: any[] }>>(() => {
    const history = data?.message_history || [];
    const initialChatbotText = data?.chatbot_text;
    const currentRecs = data?.recommendations || [];
    
    let initialMessages = [...history];

    // If we have history, check if we need to append the initial response
    if (history.length > 0) {
      const lastMsg = history[history.length - 1];
      // If the last message is from user, we should append the assistant's response
      if (lastMsg.role === 'user' && initialChatbotText) {
        initialMessages.push({ role: 'assistant', content: initialChatbotText });
      }
    } else {
      // Fallback
      initialMessages = [
        { role: 'assistant', content: initialChatbotText || 'Hola! Basándome en tu descripción, te voy a mostrar los mejores barrios para ti. ¿Qué más te gustaría saber?' }
      ];
    }

    // Attach current recommendations to the last assistant message
    if (initialMessages.length > 0) {
        const lastIdx = initialMessages.length - 1;
        if (initialMessages[lastIdx].role === 'assistant') {
            initialMessages[lastIdx] = {
                ...initialMessages[lastIdx],
                recommendations: currentRecs
            };
        }
    }
    
    return initialMessages;
  });

  const [input, setInput] = useState("");
  const [expandedButton, setExpandedButton] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);

  const loadingMessages = [
    "Interpretando tus preferencias...",
    "Escaneando barrios de Los Angeles...",
    "Cruzando datos demográficos y criminalidad...",
    "Calculando match scores...",
    "Redactando justificación..."
  ];

  useEffect(() => {
    if (!isLoading) {
      setLoadingStep(0);
      return;
    }
    
    const interval = setInterval(() => {
      setLoadingStep(prev => (prev < loadingMessages.length - 1 ? prev + 1 : prev));
    }, 2000);
    
    return () => clearInterval(interval);
  }, [isLoading]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Map top 5 variables to button labels
  const buttonLabels = (currentRec.top_5_variables || []).map((v: any, idx: number) => ({
    id: idx + 1,
    title: v.variable_name,
    content: v.justification,
    chartData: v.chart_data
  }));

  // Atwater Village polygon (Default or dynamic if available)
  const atwaterVillagePolygon = mapContext.polygon || "POLYGON ((-118.30068619528 34.0373138507143, -118.303884196041 34.037204851199, -118.300287171334 34.0372359462978, -118.297604625712 34.0372591365581, -118.296712194924 34.0372668512001, -118.296295194457 34.0372348512573, -118.29636119452 34.036894851016, -118.291561193707 34.0368418515945, -118.291550192661 34.0255018502656, -118.291552596393 34.0255018543774, -118.308899196446 34.025557849759, -118.309000196885 34.0374328504795, -118.30801419718 34.0374008510931, -118.30068619528 34.0373138507143))";

  const [activeMapAction, setActiveMapAction] = useState<any>(null);

  const handleMapAction = (action: any) => {
    console.log("Action clicked:", action);
    setActiveMapAction(action);
  };

  const handleRecommendationClick = (recs: any[], index: number) => {
    setData((prev: any) => ({ ...prev, recommendations: recs }));
    setCurrentRecIndex(index);
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
      
      // Update full data state
      setData(newData);
      
      // Update messages - Add final response
      setMessages(prev => {
        return [...prev, { 
          role: 'assistant', 
          content: newData.chatbot_text,
          recommendations: newData.recommendations 
        }];
      });
      
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Lo siento, hubo un error al procesar tu mensaje." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  // Default images
  const defaultImages = [
    { url: "https://images.unsplash.com/photo-1449844908441-8829872d2607?q=80&w=2940&auto=format&fit=crop", description: "Vistas panorámicas de la ciudad" },
    { url: "https://images.unsplash.com/photo-1580655653885-65763b2597d0?q=80&w=2940&auto=format&fit=crop", description: "Zonas residenciales tranquilas" },
    { url: "https://images.unsplash.com/photo-1513161455079-7dc1bad15a49?q=80&w=2940&auto=format&fit=crop", description: "Ambiente local y acogedor" }
  ];

  const [neighborhoodImages, setNeighborhoodImages] = useState(defaultImages);

  // Fetch images when neighborhood changes
  useEffect(() => {
    const fetchImages = async () => {
        if (!currentRec.name) return;
        
        try {
            const res = await fetch(`http://localhost:5001/api/images?neighborhood=${encodeURIComponent(currentRec.name)}`);
            const data = await res.json();
            
            if (data.images && data.images.length > 0) {
                setNeighborhoodImages(data.images);
                setCurrentImageIndex(0);
            } else {
                setNeighborhoodImages(defaultImages);
            }
        } catch (e) {
            console.error("Failed to fetch images", e);
            setNeighborhoodImages(defaultImages);
        }
    };
    
    fetchImages();
  }, [currentRec.name]);

  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % neighborhoodImages.length);
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + neighborhoodImages.length) % neighborhoodImages.length);
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
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {/* Content Container */}
                <div className={`flex flex-col gap-2 max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Bubble */}
                  <div
                    className={`rounded-2xl px-5 py-4 shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-white/20 backdrop-blur-md text-white'
                        : 'bg-black/40 backdrop-blur-md text-gray-100 border border-white/10'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {formatMessage(msg.content)}
                    </p>
                  </div>

                  {/* External Buttons */}
                  {msg.role === 'assistant' && msg.recommendations && msg.recommendations.length > 1 && (
                    <div className="flex flex-wrap gap-2 px-1">
                      {msg.recommendations.slice(1, 3).map((rec: any, i: number) => (
                        <Button
                          key={i}
                          variant="outline"
                          size="sm"
                          className={`text-xs h-7 rounded-full transition-all ${
                            currentRecIndex === (i + 1) && data.recommendations === msg.recommendations
                              ? "bg-white text-black hover:bg-white/90 border-white"
                              : "bg-transparent hover:bg-white/10 text-white/80 hover:text-white border-white/20"
                          }`}
                          onClick={() => handleRecommendationClick(msg.recommendations!, i + 1)}
                        >
                          {rec.name}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-3 mt-2 animate-in fade-in duration-300">
                <div className="w-8 h-8 flex-shrink-0 rounded-full bg-white/5 flex items-center justify-center">
                   <Bot className="h-4 w-4 text-white/40 animate-pulse" />
                </div>
                <div className="flex flex-col justify-center">
                   <span className="text-sm font-medium text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-300 to-blue-400 bg-[length:200%_auto] animate-shimmer tracking-wide">
                      {loadingMessages[loadingStep]}
                   </span>
                </div>
              </div>
            )}
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
          <div className="w-full flex items-center gap-4">
            <h1 className="text-4xl font-light tracking-tight text-white">
              {currentRec.name || "Cargando..."}
            </h1>
            {currentRecIndex > 0 && data.recommendations && data.recommendations.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleRecommendationClick(data.recommendations, 0)}
                className="text-white/60 hover:text-white hover:bg-white/10 text-xs"
              >
                <ArrowLeft className="h-3 w-3 mr-1" />
                Volver a {data.recommendations[0].name}
              </Button>
            )}
          </div>

          {/* Bottom Section - Justification and Map */}
          <div className="flex-1 flex gap-6">
            {/* Left - Justification (takes remaining space) */}
            <div className="flex-1 flex flex-col gap-6">
              {/* Top section - 1/4 */}
              <div className="h-1/4 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-lg overflow-y-auto flex flex-col gap-2">
                <h3 className="text-xs uppercase tracking-wider text-white/60 font-semibold">Overview</h3>
                <p className="text-sm text-white/90 leading-relaxed">
                  {formatMessage(currentRec.overview || "Selecciona un barrio para ver los detalles.")}
                </p>
              </div>

              {/* Bottom section - 3/4 split horizontally with fixed proportions */}
              <div className="flex-1 flex gap-6">
                {/* Left container - 3/4 - 5 clickable sections or expanded content */}
                <div className="w-3/4 backdrop-blur-xl bg-gradient-to-br from-white/10 to-white/5 border border-white/20 rounded-2xl shadow-lg overflow-hidden flex flex-col">
                  {expandedButton === null ? (
                    <>
                      <div className="px-6 py-4 border-b border-white/10 bg-gradient-to-r from-blue-500/10 to-purple-500/10">
                        <h3 className="text-xs uppercase tracking-wider text-white/80 font-semibold">Variables Clave</h3>
                      </div>
                      <div className="flex-1 flex flex-col p-3 space-y-2">
                        {buttonLabels.map((btn: any) => (
                          <button
                            key={btn.id}
                            onClick={() => setExpandedButton(btn.id)}
                            className="group relative flex-1 px-6 py-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/30 transition-all duration-300 text-white/80 hover:text-white text-sm font-medium hover:shadow-lg hover:shadow-blue-500/10 overflow-hidden"
                          >
                            {/* Animated gradient background */}
                            <div className="absolute inset-0 bg-gradient-to-r from-blue-400/0 via-blue-400/10 to-purple-400/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                            
                            {/* Content */}
                            <div className="relative z-10 flex items-center justify-between">
                              <span>{btn.title}</span>
                              <div className="w-1.5 h-1.5 rounded-full bg-white/40 group-hover:bg-blue-400 group-hover:scale-150 transition-all duration-300" />
                            </div>
                          </button>
                        ))}
                      </div>
                    </>
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
                        <p className="text-sm text-white/90 leading-relaxed mb-6">
                          {buttonLabels.find((b: any) => b.id === expandedButton)?.content}
                        </p>

                        {/* Chart Section */}
                        {(() => {
                           const btn = buttonLabels.find((b: any) => b.id === expandedButton);
                           if (!btn?.chartData) return null;
                           
                           const { user_weight, match_score, max_score, neighborhood_value, neighborhood_category, unit, match_explanation } = btn.chartData;
                           const scorePct = max_score > 0 ? (match_score / max_score) * 100 : 0;
                           
                           return (
                             <div className="space-y-4 bg-white/5 p-4 rounded-xl border border-white/10">
                               <h4 className="text-xs uppercase tracking-wider text-white/60 font-semibold">Análisis de Variable</h4>
                               
                               {/* User Importance */}
                               <div>
                                 <div className="flex justify-between text-xs text-white/80 mb-1">
                                   <span>Importancia para ti</span>
                                   <span>{user_weight}/5</span>
                                 </div>
                                 <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                   <div 
                                     className="h-full bg-blue-400 rounded-full" 
                                     style={{ width: `${(user_weight / 5) * 100}%` }}
                                   />
                                 </div>
                               </div>

                               {/* Match Score */}
                               <div>
                                 <div className="flex justify-between text-xs text-white/80 mb-1">
                                   <span>Coincidencia con el barrio</span>
                                   <span>{Math.round(scorePct)}%</span>
                                 </div>
                                 <div className="h-2 bg-white/10 rounded-full overflow-hidden mb-1">
                                   <div 
                                     className="h-full bg-green-400 rounded-full" 
                                     style={{ width: `${scorePct}%` }}
                                   />
                                 </div>
                                 {match_explanation && (
                                    <p className="text-[10px] text-white/50 italic text-right mt-1">{match_explanation}</p>
                                 )}
                               </div>
                               
                               {/* Value Display */}
                               <div className="pt-2 border-t border-white/10 flex justify-between items-center">
                                  <span className="text-xs text-white/60">Valor Real</span>
                                  <div className="text-right">
                                    <span className="block text-sm font-medium text-white">
                                        {neighborhood_value} <span className="text-xs text-white/60">{unit}</span>
                                    </span>
                                    {neighborhood_category && (
                                      <span className="block text-[10px] text-white/50 uppercase">{neighborhood_category}</span>
                                    )}
                                  </div>
                               </div>
                             </div>
                           );
                        })()}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right container - 1/4 - Map Actions */}
                <div className="w-1/4 backdrop-blur-xl bg-gradient-to-br from-white/10 to-white/5 border border-white/20 rounded-2xl shadow-lg overflow-hidden flex flex-col">
                  <div className="px-6 py-4 border-b border-white/10 bg-gradient-to-r from-emerald-500/10 to-teal-500/10">
                    <h3 className="text-xs uppercase tracking-wider text-white/80 font-semibold text-center">Vista Rápida</h3>
                  </div>
                  <div className="flex-1 flex flex-col p-3 space-y-2">
                    {mapActions.map((action: any, idx: number) => (
                      <button
                        key={idx}
                        className={`group relative px-4 py-3 rounded-xl text-xs font-medium transition-all duration-300 overflow-hidden ${
                          activeMapAction === action 
                            ? 'bg-gradient-to-r from-emerald-500/30 to-teal-500/30 border-2 border-emerald-400/50 text-white shadow-lg shadow-emerald-500/20' 
                            : 'bg-white/5 border border-white/10 text-white/80 hover:bg-white/10 hover:border-white/30 hover:text-white hover:shadow-md'
                        }`}
                        onClick={() => handleMapAction(action)}
                      >
                        {/* Animated background on hover */}
                        <div className="absolute inset-0 bg-gradient-to-r from-emerald-400/0 via-emerald-400/10 to-emerald-400/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                        
                        {/* Icon indicator */}
                        <div className="flex items-center justify-center gap-2">
                          <div className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                            activeMapAction === action 
                              ? 'bg-emerald-400 scale-150' 
                              : 'bg-white/40 group-hover:bg-white/70 group-hover:scale-125'
                          }`} />
                          <span className="relative z-10">{action.label}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Slideshow and Map */}
            <div className="w-1/3 flex flex-col gap-6">
              {/* Slideshow Container */}
              <div className="h-1/3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl overflow-hidden shadow-lg flex flex-col relative group">
                {/* Image Area */}
                <div className="flex-1 relative overflow-hidden">
                  <img 
                    src={neighborhoodImages[currentImageIndex].url} 
                    alt="Neighborhood view" 
                    className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                  />
                  
                  {/* Navigation Buttons */}
                  <button 
                    onClick={(e) => { e.stopPropagation(); prevImage(); }}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-1 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); nextImage(); }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </div>
                
                {/* Description Area */}
                <div className="p-3 bg-black/40 border-t border-white/10">
                  <p className="text-xs text-white/90 text-center font-medium">
                    {neighborhoodImages[currentImageIndex].description}
                  </p>
                  {/* Dots indicator */}
                  <div className="flex justify-center gap-1.5 mt-2">
                    {neighborhoodImages.map((_, idx) => (
                      <div 
                        key={idx}
                        className={`w-1.5 h-1.5 rounded-full transition-all ${idx === currentImageIndex ? 'bg-white scale-110' : 'bg-white/30'}`}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Map Container */}
              <div className="flex-1 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl overflow-hidden shadow-lg">
                <MapView 
                  polygonCoordinates={atwaterVillagePolygon} 
                  activeAction={activeMapAction}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Playground;
