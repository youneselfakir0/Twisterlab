import subprocess
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OpenClawResponse:
    """Structure typ?e pour les r?ponses OpenClaw"""
    text: str
    raw_data: Dict[str, Any]
    success: bool
    execution_time: float
    
    @property
    def has_error(self) -> bool:
        return not self.success or 'error' in self.raw_data


class OpenClawTool:
    """
    Interface Python pour OpenClaw CLI.
    Permet l'int?gration dans des workflows TwisterLab/n8n.
    """
    
    def __init__(
        self, 
        session_id: str = "twisterlab_default",
        timeout: int = 120,
        cli_path: str = "npx"
    ):
        """
        Args:
            session_id: Identifiant de session (maintient cookies/contexte)
            timeout: Timeout en secondes pour les commandes
            cli_path: Chemin vers npx (npx.cmd sous Windows)
        """
        self.session_id = session_id
        self.timeout = timeout
        self.cli_path = cli_path
        self._validate_openclaw()
    
    def _validate_openclaw(self):
        """V?rifie qu'OpenClaw est accessible"""
        try:
            result = subprocess.run(
                [self.cli_path, "openclaw", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("OpenClaw CLI non accessible")
            logger.info(f"OpenClaw CLI valid?: {result.stdout.strip()}")
        except Exception as e:
            raise RuntimeError(f"Impossible de valider OpenClaw: {e}")
    
    def execute(
        self, 
        message: str,
        session_id: Optional[str] = None,
        additional_args: Optional[List[str]] = None
    ) -> OpenClawResponse:
        """
        Ex?cute une commande via OpenClaw Agent
        
        Args:
            message: Instruction pour l'agent IA
            session_id: Override du session_id par d?faut
            additional_args: Arguments CLI suppl?mentaires
            
        Returns:
            OpenClawResponse avec r?sultat structur?
        """
        start_time = time.time()
        sid = session_id or self.session_id
        
        command = [
            self.cli_path, "openclaw", "agent",
            "--session-id", sid,
            "--message", message,
            "--json"
        ]
        
        if additional_args:
            command.extend(additional_args)
        
        logger.info(f"[OpenClaw] Session: {sid} | Message: {message[:80]}...")
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            parsed = json.loads(result.stdout.strip())
            
            response = OpenClawResponse(
                text=parsed.get('text', ''),
                raw_data=parsed,
                success=True,
                execution_time=execution_time
            )
            
            logger.info(f"[OpenClaw] ? R?ponse re?ue en {execution_time:.2f}s")
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"[OpenClaw] ? Timeout apr?s {self.timeout}s")
            return OpenClawResponse(
                text="",
                raw_data={"error": "timeout"},
                success=False,
                execution_time=self.timeout
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[OpenClaw] ? Erreur (code {e.returncode}): {e.stderr}")
            return OpenClawResponse(
                text="",
                raw_data={"error": e.stderr, "returncode": e.returncode},
                success=False,
                execution_time=time.time() - start_time
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"[OpenClaw] ? JSON invalide: {e}")
            return OpenClawResponse(
                text=result.stdout if 'result' in locals() else "",
                raw_data={"error": "invalid_json", "raw": result.stdout if 'result' in locals() else ""},
                success=False,
                execution_time=time.time() - start_time
            )
    
    def instagram_post(
        self, 
        image_path: str, 
        caption: str,
        session_id: str = "instagram_publisher"
    ) -> OpenClawResponse:
        """
        Use case sp?cifique: Publication Instagram
        """
        image_path = Path(image_path).resolve()
        if not image_path.exists():
            return OpenClawResponse(
                text="",
                raw_data={"error": f"Image non trouv?e: {image_path}"},
                success=False,
                execution_time=0
            )
        
        prompt = f"""Objectif : Publier une photo sur Instagram de mani?re autonome.

CONTEXTE IMPORTANT : 
- Tu dois conserver cette session Instagram. Si tu n'es pas connect?, connecte-toi.
- L'image se trouve localement ? ce chemin absolu : '{image_path}'
- Le texte de publication (caption) est : '{caption}'

INSTRUCTIONS PAS ? PAS :
1. Va sur https://www.instagram.com/
2. Assure-toi d'?tre connect?.
3. Trouve et clique sur le bouton "Cr?er" (Create) ou l'ic?ne "[+]" dans le menu lat?ral.
4. Une modale s'ouvre. Au lieu de cliquer sur "S?lectionner sur l'ordinateur" (ce qui ouvrirait une bo?te de dialogue Windows inaccessible), cherche l'?l?ment `<input type="file" accept="image/jpeg,image/png...">` cach? dans la page et injecte directement le chemin de l'image "{image_path}" dessus. 
5. Si cela ne fonctionne pas, trouve un moyen d'attacher l'image.
6. Clique sur "Suivant" (Next) jusqu'? atteindre l'?cran de la l?gende.
7. Tape la l?gende (caption) textuelle fournie ci-dessus.
8. Clique sur "Partager" (Share) et attends la confirmation "Ta publication a ?t? partag?e."
9. Renvoie un r?sum? du succ?s et le lien de la page d'accueil.
"""
        
        return self.execute(prompt, session_id=session_id)
    
    def linkedin_post(
        self, 
        text: str,
        image_path: Optional[str] = None,
        session_id: str = "linkedin_publisher"
    ) -> OpenClawResponse:
        """Use case LinkedIn"""
        prompt = f"Connecte-toi ? LinkedIn et publie le texte suivant:\n{text}"
        
        if image_path:
            image_path = Path(image_path).resolve()
            if image_path.exists():
                prompt += f"\nAjoute aussi l'image situ?e ? {image_path}"
        
        return self.execute(prompt, session_id=session_id)
    
    def web_scrape(
        self, 
        url: str, 
        extraction_prompt: str,
        session_id: str = "web_scraper"
    ) -> OpenClawResponse:
        """Scraping web avec extraction intelligente"""
        prompt = f"""Visite {url} et extrait les informations suivantes:
{extraction_prompt}

Retourne les donn?es sous format structur?."""
        
        return self.execute(prompt, session_id=session_id)
