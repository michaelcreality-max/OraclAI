"""
Multi-Domain Training Pipeline for REAL Local LLM
Trains separate models for Code, STEM, Finance, Website, General
"""

import numpy as np
import pickle
import os
from typing import List, Dict, Tuple
from datetime import datetime
from real_local_llm import RealLocalLLM, LLMConfig
from training_data_comprehensive import (
    get_all_training_data, 
    DomainTrainingData, 
    TrainingExample
)


class DomainLLMTrainer:
    """Train domain-specific LLM models"""
    
    def __init__(self, domain: str, training_data: DomainTrainingData):
        self.domain = domain
        self.training_data = training_data
        self.model = None
        self.training_history = []
        
        # Domain-specific model configs
        self.configs = {
            "code": LLMConfig(
                vocab_size=1500,  # More tokens for code
                embedding_dim=128,
                hidden_dim=256,
                num_layers=4,
                num_heads=8,
                max_seq_length=256
            ),
            "stem": LLMConfig(
                vocab_size=1200,
                embedding_dim=96,
                hidden_dim=192,
                num_layers=3,
                num_heads=6,
                max_seq_length=192
            ),
            "finance": LLMConfig(
                vocab_size=1000,
                embedding_dim=80,
                hidden_dim=160,
                num_layers=3,
                num_heads=5,
                max_seq_length=160
            ),
            "website": LLMConfig(
                vocab_size=1200,
                embedding_dim=96,
                hidden_dim=192,
                num_layers=3,
                num_heads=6,
                max_seq_length=200
            ),
            "general": LLMConfig(
                vocab_size=1000,
                embedding_dim=64,
                hidden_dim=128,
                num_layers=2,
                num_heads=4,
                max_seq_length=128
            )
        }
    
    def initialize_model(self):
        """Initialize model with domain-specific config"""
        config = self.configs.get(self.domain, self.configs["general"])
        self.model = RealLocalLLM(config)
        print(f"🤖 Initialized {self.domain} model: {self.model._count_parameters():,} parameters")
    
    def train(self, epochs: int = 50, learning_rate: float = 0.001) -> Dict:
        """Train the model on domain data"""
        if not self.model:
            self.initialize_model()
        
        train_data, val_data = self.training_data.split()
        
        print(f"\n📚 Training {self.domain.upper()} model...")
        print(f"   Training examples: {len(train_data)}")
        print(f"   Validation examples: {len(val_data)}")
        print(f"   Epochs: {epochs}")
        
        best_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(epochs):
            # Training
            epoch_losses = []
            for example in train_data:
                loss = self.model.train_step(
                    example.input_text,
                    example.output_text,
                    learning_rate=learning_rate
                )
                epoch_losses.append(loss)
            
            avg_loss = np.mean(epoch_losses)
            
            # Validation every 5 epochs
            if epoch % 5 == 0:
                val_losses = []
                for example in val_data:
                    loss = self.model.train_step(
                        example.input_text,
                        example.output_text,
                        learning_rate=0  # No update, just evaluate
                    )
                    val_losses.append(loss)
                
                val_loss = np.mean(val_losses)
                
                # Early stopping check
                if val_loss < best_loss:
                    best_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                self.training_history.append({
                    "epoch": epoch,
                    "train_loss": avg_loss,
                    "val_loss": val_loss
                })
                
                print(f"   Epoch {epoch}: train_loss={avg_loss:.4f}, val_loss={val_loss:.4f}")
                
                if patience_counter >= patience:
                    print(f"   ⏹️  Early stopping at epoch {epoch}")
                    break
        
        return {
            "domain": self.domain,
            "final_train_loss": avg_loss,
            "best_val_loss": best_loss,
            "epochs_trained": len(self.training_history),
            "parameters": self.model._count_parameters()
        }
    
    def save(self, path: str):
        """Save trained model"""
        model_path = f"{path}/{self.domain}_llm.pkl"
        self.model.save(model_path)
        
        # Save training history
        history_path = f"{path}/{self.domain}_history.pkl"
        with open(history_path, 'wb') as f:
            pickle.dump(self.training_history, f)
        
        print(f"💾 Saved {self.domain} model to {model_path}")
    
    def test_generation(self, prompts: List[str]) -> List[Dict]:
        """Test model generation quality"""
        results = []
        for prompt in prompts:
            output = self.model.generate(prompt, max_length=50)
            results.append({
                "prompt": prompt,
                "output": output,
                "domain": self.domain
            })
        return results


class MultiDomainLLMSystem:
    """System managing all domain-specific LLMs"""
    
    def __init__(self, models_dir: str = "trained_models"):
        self.models_dir = models_dir
        self.domain_models = {}
        self.training_results = {}
        
        os.makedirs(models_dir, exist_ok=True)
    
    def train_all_domains(self) -> Dict:
        """Train models for all domains"""
        print("=" * 70)
        print("🚀 MULTI-DOMAIN LLM TRAINING SYSTEM")
        print("=" * 70)
        
        # Get all training data
        all_data = get_all_training_data()
        
        for domain, training_data in all_data.items():
            print(f"\n{'='*70}")
            print(f"🎯 Training {domain.upper()} Domain")
            print(f"{'='*70}")
            
            # Initialize trainer
            trainer = DomainLLMTrainer(domain, training_data)
            
            # Train
            result = trainer.train(epochs=30, learning_rate=0.001)
            self.training_results[domain] = result
            
            # Save model
            trainer.save(self.models_dir)
            self.domain_models[domain] = trainer
            
            print(f"✅ {domain.upper()} training complete!")
        
        return self.training_results
    
    def generate(self, prompt: str, domain: str = None) -> str:
        """Generate using appropriate domain model"""
        # Auto-detect domain if not specified
        if not domain:
            domain = self._detect_domain(prompt)
        
        # Use general model if domain not found
        if domain not in self.domain_models:
            domain = "general"
        
        model = self.domain_models[domain].model
        return model.generate(prompt, max_length=60, temperature=0.8)
    
    def _detect_domain(self, prompt: str) -> str:
        """Auto-detect domain from prompt"""
        prompt_lower = prompt.lower()
        
        # Domain keywords
        domain_keywords = {
            "code": ["code", "function", "class", "python", "javascript", "html", "css", "sql", "programming", "algorithm"],
            "stem": ["math", "physics", "chemistry", "calculus", "derivative", "integral", "equation", "formula", "calculate"],
            "finance": ["stock", "invest", "portfolio", "dividend", "pe ratio", "finance", "money", "trading", "analysis"],
            "website": ["website", "web", "html", "css", "responsive", "layout", "navigation", "hero", "footer", "component"]
        }
        
        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            scores[domain] = score
        
        # Return domain with highest score, or general
        best_domain = max(scores, key=scores.get)
        return best_domain if scores[best_domain] > 0 else "general"
    
    def comprehensive_test(self) -> Dict:
        """Test all domain models"""
        print("\n" + "=" * 70)
        print("🧪 COMPREHENSIVE TESTING")
        print("=" * 70)
        
        test_prompts = {
            "code": [
                "create python function",
                "javascript promise example"
            ],
            "stem": [
                "explain quadratic formula",
                "derivative of x squared"
            ],
            "finance": [
                "calculate pe ratio",
                "what is compound interest"
            ],
            "website": [
                "create hero section",
                "responsive navigation"
            ],
            "general": [
                "hello how are you",
                "what is blockchain"
            ]
        }
        
        results = {}
        for domain, prompts in test_prompts.items():
            print(f"\n📝 Testing {domain.upper()}:")
            domain_results = []
            
            if domain in self.domain_models:
                for prompt in prompts:
                    output = self.generate(prompt, domain)
                    domain_results.append({
                        "prompt": prompt,
                        "output": output[:80] + "..."
                    })
                    print(f"   Prompt: {prompt[:40]}...")
                    print(f"   Output: {output[:60]}...")
            else:
                print(f"   ⚠️  Model not found")
            
            results[domain] = domain_results
        
        return results
    
    def get_summary(self) -> Dict:
        """Get training summary"""
        total_params = sum(
            result["parameters"] 
            for result in self.training_results.values()
        )
        
        return {
            "domains_trained": len(self.training_results),
            "total_parameters": total_params,
            "models_directory": self.models_dir,
            "training_results": self.training_results
        }


def main():
    """Main training and testing pipeline"""
    # Initialize system
    system = MultiDomainLLMSystem(models_dir="trained_models")
    
    # Train all domains
    results = system.train_all_domains()
    
    # Comprehensive testing
    test_results = system.comprehensive_test()
    
    # Summary
    summary = system.get_summary()
    
    print("\n" + "=" * 70)
    print("📊 TRAINING SUMMARY")
    print("=" * 70)
    print(f"Domains trained: {summary['domains_trained']}")
    print(f"Total parameters: {summary['total_parameters']:,}")
    
    for domain, result in results.items():
        print(f"\n{domain.upper()}:")
        print(f"  Parameters: {result['parameters']:,}")
        print(f"  Final loss: {result['final_train_loss']:.4f}")
        print(f"  Epochs: {result['epochs_trained']}")
    
    print("\n" + "=" * 70)
    print("✅ ALL MODELS TRAINED AND TESTED!")
    print("=" * 70)
    print(f"💾 Models saved to: {summary['models_directory']}/")
    print("\nModels available:")
    for domain in results.keys():
        print(f"  - {domain}_llm.pkl")
    
    return system, results, test_results


if __name__ == "__main__":
    system, results, tests = main()
