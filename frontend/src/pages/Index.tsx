import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowRight } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");

  const handleSubmit = () => {
    if (prompt.trim()) {
      navigate("/playground", { state: { prompt } });
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-background">
      {/* Video Background */}
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

      {/* Content */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4">
        {/* Logo */}
        <div className="mb-12">
          <h1 className="text-5xl font-light tracking-tight text-white">
            compass
          </h1>
        </div>

        {/* Main Input */}
        <div className="w-full max-w-2xl">
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-6 shadow-2xl">
            <div className="relative">
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleSubmit();
                  }
                }}
                placeholder="Descriu la teva situació..."
                className="min-h-[120px] bg-white/5 backdrop-blur-sm border border-white/10 text-white placeholder:text-white/50 resize-none text-base focus-visible:ring-1 focus-visible:ring-white/30 pr-14"
              />
              
              <Button
                onClick={handleSubmit}
                disabled={!prompt.trim()}
                size="icon"
                className="absolute bottom-3 right-3 bg-white/20 hover:bg-white/30 text-white border-0 rounded-full h-10 w-10 backdrop-blur-sm transition-all"
              >
                <ArrowRight className="h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* Helper text */}
          <p className="mt-4 text-center text-sm text-white/70">
            Prem ⌘ + Enter per enviar
          </p>
        </div>

        {/* Example prompts */}
        <div className="mt-12 max-w-2xl w-full">
          <p className="text-white/60 text-xs mb-3 text-center">
            Exemples:
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {[
              "Busco un barri familiar amb parcs i escoles",
              "M'agrada l'art i la cultura urbana",
              "Necessito estar a prop del centre"
            ].map((example) => (
              <button
                key={example}
                onClick={() => setPrompt(example)}
                className="backdrop-blur-md bg-white/10 hover:bg-white/20 border border-white/20 text-white/90 text-xs px-4 py-2 rounded-full transition-all"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
