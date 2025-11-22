import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Send, ChevronLeft } from "lucide-react";
import MapView from "@/components/MapView";

const Playground = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const initialPrompt = location.state?.prompt || "";
  
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([
    { role: 'assistant', content: 'Hola! Basándome en tu descripción, te voy a mostrar los mejores barrios para ti. ¿Qué más te gustaría saber?' }
  ]);
  const [input, setInput] = useState("");
  const [expandedButton, setExpandedButton] = useState<number | null>(null);

  const buttonLabels = [
    { id: 1, title: "Opción 1", content: "Contenido detallado de la opción 1..." },
    { id: 2, title: "Opción 2", content: "Contenido detallado de la opción 2..." },
    { id: 3, title: "Opción 3", content: "Contenido detallado de la opción 3..." },
    { id: 4, title: "Opción 4", content: "Contenido detallado de la opción 4..." },
    { id: 5, title: "Opción 5", content: "Contenido detallado de la opción 5..." },
  ];

  // Atwater Village polygon
  const atwaterVillagePolygon = "POLYGON ((-118.30068619528 34.0373138507143, -118.303884196041 34.037204851199, -118.300287171334 34.0372359462978, -118.297604625712 34.0372591365581, -118.296712194924 34.0372668512001, -118.296295194457 34.0372348512573, -118.29636119452 34.036894851016, -118.291561193707 34.0368418515945, -118.291550192661 34.0255018502656, -118.291552596393 34.0255018543774, -118.308899196446 34.025557849759, -118.309000196885 34.0374328504795, -118.30801419718 34.0374008510931, -118.30068619528 34.0373138507143))";

  const handleSend = () => {
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    setInput("");
    
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Entiendo. Déjame actualizar el mapa con tus preferencias...' 
      }]);
    }, 1000);
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
        <div className="w-1/4 h-full backdrop-blur-xl bg-white/10 border-r border-white/20 flex flex-col shadow-2xl">
          {/* Header */}
          <div className="p-4 border-b border-white/10 flex items-center gap-3">
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => navigate("/")}
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h2 className="font-light text-white">compass</h2>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-white/30 backdrop-blur-sm text-white'
                      : 'bg-white/20 backdrop-blur-sm text-white'
                  }`}
                >
                  <p className="text-sm">{msg.content}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/10">
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
                className="min-h-[44px] max-h-[120px] resize-none bg-white/10 backdrop-blur-sm border-white/10 text-white placeholder:text-white/50 focus-visible:ring-white/30"
              />
              <Button 
                onClick={handleSend}
                size="icon"
                disabled={!input.trim()}
                className="bg-white/30 hover:bg-white/40 text-white"
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
              Atwater Village
            </h1>
          </div>

          {/* Bottom Section - Justification and Map */}
          <div className="flex-1 flex gap-6">
            {/* Left - Justification (takes remaining space) */}
            <div className="flex-1 flex flex-col gap-6">
              {/* Top section - 1/4 */}
              <div className="h-1/4 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6 shadow-lg">
                <p className="text-sm text-white/90 leading-relaxed">
                  Overview I love semen oh yes
                </p>
              </div>

              {/* Bottom section - 3/4 split horizontally with fixed proportions */}
              <div className="flex-1 flex gap-6">
                {/* Left container - 3/4 - 5 clickable sections or expanded content */}
                <div className="w-3/4 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-lg overflow-hidden">
                  {expandedButton === null ? (
                    <div className="h-full flex flex-col">
                      {buttonLabels.map((btn) => (
                        <button
                          key={btn.id}
                          onClick={() => setExpandedButton(btn.id)}
                          className="flex-1 border-b border-white/10 last:border-b-0 hover:bg-white/5 transition-colors flex items-center justify-center text-white/90 text-sm"
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
                          {buttonLabels.find(b => b.id === expandedButton)?.title}
                        </h3>
                        <p className="text-sm text-white/90 leading-relaxed">
                          {buttonLabels.find(b => b.id === expandedButton)?.content}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Right container - 1/4 - 5 vertical buttons */}
                <div className="w-1/4 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-lg overflow-hidden flex flex-col">
                  {[1, 2, 3, 4, 5].map((num) => (
                    <button
                      key={num}
                      className="flex-1 border-b border-white/10 last:border-b-0 hover:bg-white/5 transition-all flex items-center justify-center text-white/90 text-base font-light hover:font-normal"
                    >
                      Botón {num}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right - Map */}
            <div className="w-1/3 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl overflow-hidden shadow-lg">
              <MapView polygonCoordinates={atwaterVillagePolygon} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Playground;
