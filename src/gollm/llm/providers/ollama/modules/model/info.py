"""Model information module for Ollama adapter."""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger('gollm.ollama.model')

@dataclass
class ModelInfo:
    """Stores and processes information about an Ollama model."""
    
    name: str
    size: int = 0
    modified_at: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> 'ModelInfo':
        """Create a ModelInfo instance from an API response.
        
        Args:
            response: API response dictionary
            
        Returns:
            ModelInfo instance
        """
        # Extract basic info
        name = response.get('name', 'unknown')
        size = response.get('size', 0)
        modified_at = response.get('modified_at', '')
        
        # Extract parameters
        parameters = response.get('parameters', {})
        
        # Extract metadata
        metadata = {
            k: v for k, v in response.items() 
            if k not in ['name', 'size', 'modified_at', 'parameters']
        }
        
        return cls(
            name=name,
            size=size,
            modified_at=modified_at,
            parameters=parameters,
            metadata=metadata
        )
    
    def get_size_mb(self) -> float:
        """Get the model size in megabytes.
        
        Returns:
            Size in MB
        """
        return self.size / (1024 * 1024)
    
    def get_size_gb(self) -> float:
        """Get the model size in gigabytes.
        
        Returns:
            Size in GB
        """
        return self.size / (1024 * 1024 * 1024)
    
    def get_size_category(self) -> str:
        """Get the size category of the model.
        
        Returns:
            Size category string ('small', 'medium', 'large', 'very large')
        """
        size_gb = self.get_size_gb()
        
        if size_gb < 2:
            return 'small'
        elif size_gb < 10:
            return 'medium'
        elif size_gb < 30:
            return 'large'
        else:
            return 'very large'
    
    def get_parameter_count(self) -> Optional[int]:
        """Estimate the parameter count based on model name or metadata.
        
        Returns:
            Estimated parameter count or None if unknown
        """
        # Try to extract from name (e.g., llama2:7b)
        name_lower = self.name.lower()
        
        # Common parameter counts in model names
        param_indicators = [
            ('70b', 70_000_000_000),
            ('65b', 65_000_000_000),
            ('34b', 34_000_000_000),
            ('33b', 33_000_000_000),
            ('30b', 30_000_000_000),
            ('13b', 13_000_000_000),
            ('14b', 14_000_000_000),
            ('7b', 7_000_000_000),
            ('8b', 8_000_000_000),
            ('3b', 3_000_000_000),
            ('4b', 4_000_000_000),
            ('2b', 2_000_000_000),
            ('1.3b', 1_300_000_000),
            ('1b', 1_000_000_000),
        ]
        
        for indicator, count in param_indicators:
            if indicator in name_lower:
                return count
        
        # Check metadata
        if 'parameter_count' in self.metadata:
            return self.metadata['parameter_count']
            
        return None
    
    def get_recommended_parameters(self) -> Dict[str, Any]:
        """Get recommended parameters for this model.
        
        Returns:
            Dictionary of recommended parameters
        """
        # Start with default parameters
        recommended = {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1,
        }
        
        # Update with model-specific parameters if available
        if self.parameters:
            recommended.update(self.parameters)
            
        # Adjust based on model name
        name_lower = self.name.lower()
        
        # Coding models often benefit from lower temperature
        if any(code_model in name_lower for code_model in ["code", "codellama", "starcoder", "wizard-code"]):
            recommended["temperature"] = min(recommended.get("temperature", 0.7), 0.2)
            
        # Instruct models may need different settings
        if "instruct" in name_lower:
            recommended["instruct"] = True
            
        return recommended
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model info to a dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'size': self.size,
            'size_mb': self.get_size_mb(),
            'size_gb': self.get_size_gb(),
            'size_category': self.get_size_category(),
            'modified_at': self.modified_at,
            'parameters': self.parameters,
            'parameter_count': self.get_parameter_count(),
            'recommended_parameters': self.get_recommended_parameters(),
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """String representation of the model info.
        
        Returns:
            String representation
        """
        size_str = f"{self.get_size_gb():.2f} GB" if self.size > 0 else "Unknown size"
        param_count = self.get_parameter_count()
        param_str = f"{param_count/1_000_000_000:.1f}B params" if param_count else "Unknown params"
        
        return f"Model: {self.name} ({size_str}, {param_str})"
