import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowRight } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");

  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (prompt.trim()) {
      setIsLoading(true);
      try {
      const response = await fetch('http://localhost:5001/api/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        navigate("/playground", { state: { prompt, initialData: data } });
      } catch (error) {
        console.error("Error starting session:", error);
        alert("Error connecting to server: " + error);
      } finally {
        setIsLoading(false);
      }
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
                disabled={!prompt.trim() || isLoading}
                size="icon"
                className="absolute bottom-3 right-3 bg-white/20 hover:bg-white/30 text-white border-0 rounded-full h-10 w-10 backdrop-blur-sm transition-all"
              >
                {isLoading ? (
                  <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <ArrowRight className="h-5 w-5" />
                )}
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
              {
                name: "Daenerys Targaryen",
                text: "Daenerys Targaryen: L'Emprenedora Ètica Fundadora d'una startup sostenible, és nova a la ciutat amb els seus tres \"dracs\" (així li agrada referir-se als seus gossos) Busca un barri amb ànima, ple de negocis locals i amb un fort sentit de comunitat."
              },
              {
                name: "Cersei Lannister",
                text: "Cersei Lannister: La Reina Corporativa Una executiva d'alt nivell que viu pel poder, el prestigi i la privacitat. Per a ella i els seus fills, vol viure aïllada en una bombolla de màxima seguretat, escoles d'elit i botigues de luxe."
              },
              {
                name: "Bran Stark",
                text: "Bran Stark: L'Analista Total Un científic de dades que treballa 100% des de casa. Es mou en cadira de rodes, així que necessita zero barreres arquitectòniques. Busca un lloc tranquil, silenciós i amb la millor fibra òptica per poder treballar sense límits."
              },
              {
                name: "Jon Snow",
                text: "Jon Snow: El Guardià de la Comunitat Treballa als serveis d'emergència i té un sou públic. Busca un barri autèntic, on els veïns es coneguin. Valora allò pràctic, no el luxe, i necessita tenir la natura a prop per desconnectar."
              },
              {
                name: "Arya Stark",
                text: "Arya Stark: La Nòmada Urbana Una freelance independent que valora l'anonimat i la llibertat per sobre de tot. Necessita una \"base\" en una zona densa i moguda, on pugui barrejar-se amb la gent. Transport públic 24/7 per a qualsevol aventura."
              },
              {
                name: "Tyrion Lannister",
                text: "Tyrion Lannister: L'Estratega Urbà Un consultor brillant i molt social. El seu hàbitat és l'epicentre cultural i gastronòmic de la ciutat. Ho vol tot a peu: de la reunió al millor restaurant, i d'allà a un bar sense agafar cap taxi."
              }
            ].map((example) => (
              <button
                key={example.name}
                onClick={() => setPrompt(example.text)}
                className="backdrop-blur-md bg-white/10 hover:bg-white/20 border border-white/20 text-white/90 text-xs px-4 py-2 rounded-full transition-all"
              >
                {example.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
