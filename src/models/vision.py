import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import sys
import os

MODEL_ID = "openai/clip-vit-large-patch14"

class LuxuryVisionAI:
    def __init__(self):
        print(f"👁️ Inicializando Motor Visual ({MODEL_ID})...")
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"   🚀 Hardware: {self.device.upper()}")
            
            # Carga segura del modelo
            self.model = CLIPModel.from_pretrained(MODEL_ID, use_safetensors=True).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(MODEL_ID, use_safetensors=True)
            
            # BASE DE CONOCIMIENTO (Marcas y sus Modelos Icónicos)
            self.KNOWLEDGE_BASE = {
                "Dior": ["Lady Dior", "Saddle Bag", "Book Tote", "30 Montaigne", "Bobby", "Caro"],
                "Hermès": ["Birkin", "Kelly", "Constance", "Evelyne", "Picotin", "Lindy", "Garden Party"],
                "Chanel": ["Classic Flap", "Boy Bag", "2.55 Reissue", "Chanel 19", "Gabrielle", "WOC", "Deauville"],
                "Louis Vuitton": ["Neverfull", "Speedy", "Alma", "Pochette Metis", "Onthego", "Capucines", "Multi Pochette", "Keepall"],
                "Prada": ["Galleria", "Re-Edition 2005", "Cleo", "Cahier", "Double Bag", "Symbole"],
                "Gucci": ["GG Marmont", "Dionysus", "Jackie 1961", "Horsebit 1955", "Diana", "Soho Disco"],
                "Fendi": ["Baguette", "Peekaboo", "First", "Sunshine", "Mon Tresor"],
                "Loewe": ["Puzzle", "Hammock", "Gate", "Flamenco", "Basket"],
                "Bottega Veneta": ["Cassette", "The Pouch", "Jodie", "Arco", "Andiamo"],
                "Celine": ["Triomphe", "Belt Bag", "Luggage", "Ava", "Classic Box"]
            }
            print("   ✅ Motor Visual listo.")
        except Exception as e:
            print(f"   ❌ Error motor: {e}")
            sys.exit(1)

    def analyze_image(self, image_path):
        # Valor por defecto si todo falla
        default_error = {"Error": "Error desconocido", "Confianza_Global": 0.0}
        
        if not os.path.exists(image_path): 
            return {"Error": "No file found", "Confianza_Global": 0.0}

        try:
            # 1. CARGA SEGURA
            image = Image.open(image_path)
            if image.mode != "RGB": image = image.convert("RGB")
            
            results = {}

            # 2. DETECCIÓN DE MARCA
            brands = list(self.KNOWLEDGE_BASE.keys())
            brand_prompts = [f"a photo of a {b} bag" for b in brands]
            
            brand_probs = self._get_probabilities(image, brand_prompts)
            top_brand_idx = brand_probs.argmax().item()
            confidence_brand = brand_probs[0][top_brand_idx].item()
            
            top_brand = brands[top_brand_idx]
            results['Marca'] = top_brand
            
            # Debug: Guardar las top 3 marcas que la IA ha considerado
            top3_v, top3_i = brand_probs[0].topk(3)
            results['Debug_Marcas'] = [f"{brands[i]} ({v.item():.1%})" for i, v in zip(top3_i, top3_v)]

            # 3. DETECCIÓN DE MODELO
            if top_brand in self.KNOWLEDGE_BASE:
                models = self.KNOWLEDGE_BASE[top_brand]
                model_prompts = [f"a photo of a {m} bag" for m in models]
                
                model_probs = self._get_probabilities(image, model_prompts)
                top_model_idx = model_probs.argmax().item()
                confidence_model = model_probs[0][top_model_idx].item()
                
                results['Modelo'] = models[top_model_idx]
            else:
                results['Modelo'] = "Genérico"
                confidence_model = 0.5 # Valor neutro

            # 4. COLOR
            colors = ["Black", "Beige", "Red", "Blue", "Pink", "White", "Green", "Brown", "Grey", "Gold", "Silver"]
            c_prompts = [f"a {c.lower()} bag" for c in colors]
            c_probs = self._get_probabilities(image, c_prompts)
            results['Color'] = colors[c_probs.argmax().item()]

            # 5. ESTADO
            states = ["New / Mint", "Excellent", "Used / Worn"]
            s_prompts = [f"a handbag in {s.lower()} condition" for s in states]
            s_probs = self._get_probabilities(image, s_prompts)
            results['Estado_Visual'] = states[s_probs.argmax().item()]
            
            # --- CÁLCULO FINAL DE CONFIANZA (FLOAT PURO) ---
            # Promedio entre lo seguro que está de la marca y del modelo
            final_conf = (confidence_brand + confidence_model) / 2
            
            # Guardamos AMBOS formatos: Float para lógica, String para UI
            results['Confianza_Global'] = final_conf 
            results['Confianza_Texto'] = f"{final_conf:.1%}"
            
            # Copiar modelo a tipo para compatibilidad
            results['Tipo'] = results['Modelo']
            
            return results
            
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return {"Error": f"Fallo interno: {str(e)}", "Confianza_Global": 0.0}

    def _get_probabilities(self, image, prompts):
        """Devuelve el tensor de probabilidades completo."""
        inputs = self.processor(text=prompts, images=image, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.logits_per_image.softmax(dim=1)

if __name__ == "__main__":
    # Test simple
    ai = LuxuryVisionAI()
    print("Motor cargado.")