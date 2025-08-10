import streamlit as st
from openai import OpenAI
import json

# Chargement des variables d'environnement



def log_web_search(message):
    """Afficher les logs web search dans Streamlit"""
    st.write(f"🔍 **Web Search:** {message}")

class CompanyAnalyzer:
    def __init__(self):
        """Initialisation de l'analyseur d'entreprises"""
        self.api_key = st.secrets('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Clé API OpenAI non configurée")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze_company(self, company_name):
        """Analyse complète en un seul appel API (2015-2025) avec web search uniquement pour 2025"""
        try:
            result = self._analyze_all_in_one(company_name)
            return result
        except Exception as e:
            return self._generate_error_response(company_name)

    def _analyze_all_in_one(self, company_name):
        """Un seul appel: 2015-2024 via connaissances internes, 2025 via web_search_preview"""
        log_web_search(f"Appel unique: 2015-2024 via connaissances, 2025 via web search pour {company_name}")

        system_prompt = f"""Tu es un analyste d'entreprises avec une date de coupure de connaissances en septembre 2024.

Règles d'utilisation des sources:
- Pour 2015 → 2024 inclus: utilise exclusivement tes connaissances internes (pas de recherche web)
- Pour 2025: tu DOIS utiliser l'outil de recherche web (web_search_preview) avec un contexte élevé pour obtenir les dernières données

Contraintes de sortie:
- Retourne UNIQUEMENT du JSON valide, sans texte en dehors du JSON
- Valeurs numériques uniquement pour les métriques quantitatives
- Pas de 'N/A', 'en cours', 0 fictif ou de texte explicatif
- Pas d'underscore dans les nombres (ex: 42_000 est interdit)
"""

        user_prompt = f"""Fournis un JSON unique contenant les données 2015-2025 pour {company_name}.

Exigences de sources:
- Années 2015-2024: connaissance interne
- Année 2025: recherche web obligatoire (web_search_preview) uniquement pour cette année

Format JSON requis (toutes les clés OBLIGATOIRES) :
{{
  "general_info": {{
    "company_name": "{company_name}",
    "industry": "Secteur d'activité",
    "founded_year": "Année de création",
    "headquarters": "Siège social",
    "description": "Description détaillée"
  }},
  "revenue_data": {{
    "2015": nombre_en_milliards, "2016": nombre_en_milliards, "2017": nombre_en_milliards,
    "2018": nombre_en_milliards, "2019": nombre_en_milliards, "2020": nombre_en_milliards,
    "2021": nombre_en_milliards, "2022": nombre_en_milliards, "2023": nombre_en_milliards,
    "2024": nombre_en_milliards, "2025": nombre_en_milliards
  }},
  "profit_data": {{
    "2015": nombre_en_milliards, "2016": nombre_en_milliards, "2017": nombre_en_milliards,
    "2018": nombre_en_milliards, "2019": nombre_en_milliards, "2020": nombre_en_milliards,
    "2021": nombre_en_milliards, "2022": nombre_en_milliards, "2023": nombre_en_milliards,
    "2024": nombre_en_milliards, "2025": nombre_en_milliards
  }},
  "employees_data": {{
    "2015": entier, "2016": entier, "2017": entier, "2018": entier, "2019": entier,
    "2020": entier, "2021": entier, "2022": entier, "2023": entier, "2024": entier, "2025": entier
  }},
  "co2_emissions": {{
    "2015": nombre, "2016": nombre, "2017": nombre, "2018": nombre, "2019": nombre,
    "2020": nombre, "2021": nombre, "2022": nombre, "2023": nombre, "2024": nombre, "2025": nombre
  }},
  "renewable_energy": {{
    "2015": pourcentage, "2016": pourcentage, "2017": pourcentage, "2018": pourcentage, "2019": pourcentage,
    "2020": pourcentage, "2021": pourcentage, "2022": pourcentage, "2023": pourcentage, "2024": pourcentage, "2025": pourcentage
  }},
  "esg_scores": {{
    "2015": score_0_100, "2016": score_0_100, "2017": score_0_100, "2018": score_0_100, "2019": score_0_100,
    "2020": score_0_100, "2021": score_0_100, "2022": score_0_100, "2023": score_0_100, "2024": score_0_100, "2025": score_0_100
  }},
  "recent_news": ["Actualité 1", "Actualité 2", "Actualité 3"],
  "sustainability_updates": {{
    "new_initiatives": "...",
    "carbon_progress": "...",
    "renewable_projects": "...",
    "sustainability_target_2030": "...",
    "achievement_sustainability_target_2025": "...",
    "latest_annual_report_url": "https://...",
    "latest_sustainability_report_url": "https://..."
  }}
}}

Contraintes strictes:
- Le JSON doit être valide sans balises markdown
- Utilise le point comme séparateur décimal
- Pas d'underscores dans les nombres
- Si 2025 n'est pas disponible après recherche, tu peux estimer de façon réaliste mais indique que c'est estimé dans recent_news.
"""

        try:
            log_web_search(f"📡 Appel API (unique) avec web search 2025 pour {company_name}")

            response = self.client.responses.create(
                model="gpt-5-mini",
                tools=[{"type": "web_search_preview", "search_context_size": "high"}],
                input=system_prompt + "\n" + user_prompt,
            )

            log_web_search(f"✅ Réponse reçue pour {company_name}")
            content = response.output_text
            log_web_search(f"📄 Contenu réponse: {content[:200]}...")

            parsed_data = self._parse_json_response(content)

            if parsed_data is None or parsed_data == {}:
                return self._get_fallback_recent_data(company_name)

            # S'assurer que le nom d'entreprise est présent au niveau racine pour l'UI
            if "company_name" not in parsed_data:
                parsed_data["company_name"] = company_name

            return parsed_data

        except Exception as e:
            log_web_search(f"❌ Erreur appel unique: {str(e)}")
            return self._get_fallback_recent_data(company_name)
    
    def _parse_json_response(self, content):
        """Parse la réponse JSON de l'API"""
        
        try:
            
            # Nettoyer le contenu des balises markdown
            original_content = content
            if "```json" in content:
                parts = content.split("```json")
                if len(parts) > 1:
                    content = parts[1].split("```")[0]
            elif "```" in content:
                parts = content.split("```")
                if len(parts) > 1:
                    content = parts[1]
            
            # Nettoyer les caractères indésirables
            content = content.strip()
            
            # Supprimer les underscores dans les nombres (Python style) car non valides en JSON
            import re
            content = re.sub(r'(\d)_(\d)', r'\1\2', content)
            
            # Vérifier si le contenu ressemble à du JSON
            if not content.startswith('{') and not content.startswith('['):
                # Essayer de trouver le début du JSON
                json_start = content.find('{')
                if json_start != -1:
                    content = content[json_start:]
                else:
                    return {}
            
            # Parser le JSON
            parsed_data = json.loads(content)
            
            # Vérifier et nettoyer les certifications
            if "sustainability_info" in parsed_data:
                sustainability = parsed_data["sustainability_info"]
                if "certifications" in sustainability:
                    certs = sustainability["certifications"]
                    if isinstance(certs, str):
                        # Convertir string en liste
                        if ',' in certs:
                            cert_list = [cert.strip() for cert in certs.split(',') if cert.strip()]
                        else:
                            cert_list = [certs.strip()] if certs.strip() else []
                        sustainability["certifications"] = cert_list
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            return {}
        except Exception as e:
            return {}
    
    def _generate_error_response(self, company_name):
        """Génère une réponse d'erreur standardisée"""
        return {
            "company_name": company_name,
            "error": "Erreur lors de l'analyse",
            "general_info": {"company_name": company_name},
            "revenue_data": {},
            "profit_data": {},
            "employees_data": {},
            "co2_emissions": {},
            "renewable_energy": {},
            "esg_scores": {},
            "sustainability_info": {},
            "recent_news": [],
            "sustainability_updates": {}
        }

# Exemple d'utilisation supprimé
