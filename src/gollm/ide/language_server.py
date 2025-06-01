import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Diagnostic:
    range: Dict[str, Any]
    severity: int  # 1=Error, 2=Warning, 3=Info, 4=Hint
    message: str
    source: str = "gollm"

class GollmLanguageServer:
    """Language Server Protocol implementation for goLLM"""
    
    def __init__(self, gollm_core):
        self.gollm_core = gollm_core
        self.documents: Dict[str, str] = {}
        self.diagnostics: Dict[str, List[Diagnostic]] = {}
    
    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """LSP initialize request"""
        return {
            "capabilities": {
                "textDocumentSync": {
                    "openClose": True,
                    "change": 1,  # Full document sync
                    "save": {"includeText": True}
                },
                "diagnosticProvider": True,
                "codeActionProvider": True,
                "documentFormattingProvider": True,
                "completionProvider": {
                    "triggerCharacters": ["."]
                }
            },
            "serverInfo": {
                "name": "gollm-language-server",
                "version": "0.1.0"
            }
        }
    
    async def did_open(self, params: Dict[str, Any]):
        """Document opened"""
        uri = params["textDocument"]["uri"]
        text = params["textDocument"]["text"]
        
        self.documents[uri] = text
        await self._validate_document(uri, text)
    
    async def did_change(self, params: Dict[str, Any]):
        """Document changed"""
        uri = params["textDocument"]["uri"]
        changes = params["contentChanges"]
        
        # Full document sync
        if changes:
            text = changes[0]["text"]
            self.documents[uri] = text
            await self._validate_document(uri, text)
    
    async def did_save(self, params: Dict[str, Any]):
        """Document saved"""
        uri = params["textDocument"]["uri"]
        text = params.get("text")
        
        if text:
            self.documents[uri] = text
        
        await self._validate_document(uri, self.documents.get(uri, ""))
    
    async def _validate_document(self, uri: str, text: str):
        """Waliduje dokument i wysyła diagnostyki"""
        try:
            # Zapisz do tymczasowego pliku
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(text)
                temp_file = f.name
            
            # Waliduj z goLLM
            result = self.gollm_core.validate_file(temp_file)
            
            # Konwertuj naruszenia na diagnostyki
            diagnostics = []
            for violation in result.get('violations', []):
                diagnostic = Diagnostic(
                    range={
                        "start": {"line": violation.line_number - 1, "character": 0},
                        "end": {"line": violation.line_number - 1, "character": 100}
                    },
                    severity=self._get_severity(violation.severity),
                    message=f"{violation.type}: {violation.message}"
                )
                diagnostics.append(diagnostic)
            
            self.diagnostics[uri] = diagnostics
            
            # Wyślij diagnostyki (w prawdziwej implementacji)
            await self._publish_diagnostics(uri, diagnostics)
            
            # Cleanup
            import os
            os.unlink(temp_file)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
    
    def _get_severity(self, severity: str) -> int:
        """Konwertuje severity goLLM na LSP"""
        severity_map = {
            "error": 1,
            "warning": 2,
            "info": 3,
            "hint": 4
        }
        return severity_map.get(severity, 1)
    
    async def _publish_diagnostics(self, uri: str, diagnostics: List[Diagnostic]):
        """Publikuje diagnostyki (placeholder dla prawdziwej implementacji)"""
        # W prawdziwej implementacji tutaj byłoby wysłanie przez JSON-RPC
        logger.info(f"Publishing {len(diagnostics)} diagnostics for {uri}")
    
    async def code_action(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Dostarcza code actions (quick fixes)"""
        uri = params["textDocument"]["uri"]
        diagnostics_in_range = []
        
        # Znajdź diagnostyki w zakresie
        for diagnostic in self.diagnostics.get(uri, []):
            diagnostics_in_range.append(diagnostic)
        
        actions = []
        for diagnostic in diagnostics_in_range:
            if "print statement" in diagnostic.message.lower():
                actions.append({
                    "title": "Replace with logging",
                    "kind": "quickfix",
                    "edit": {
                        "changes": {
                            uri: [{
                                "range": diagnostic.range,
                                "newText": "logger.info(...)"
                            }]
                        }
                    }
                })
        
        return actions
