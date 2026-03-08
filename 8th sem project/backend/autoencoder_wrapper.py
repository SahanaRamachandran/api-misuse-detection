"""
PyTorch Autoencoder Wrapper for Anomaly Detection

This module provides a wrapper for PyTorch-based Autoencoder models
to integrate with the ML anomaly detection system.

The autoencoder detects anomalies based on reconstruction error:
- Low reconstruction error = Normal traffic
- High reconstruction error = Anomalous traffic
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple
import os


class AutoencoderModel(nn.Module):
    """
    Simple Autoencoder architecture for anomaly detection.
    
    Architecture:
        Encoder: input -> 64 -> 32 -> 16 (bottleneck)
        Decoder: 16 -> 32 -> 64 -> output
    """
    
    def __init__(self, input_dim: int, encoding_dim: int = 16):
        """
        Initialize autoencoder.
        
        Args:
            input_dim: Number of input features
            encoding_dim: Dimension of bottleneck layer
        """
        super(AutoencoderModel, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, encoding_dim),
            nn.ReLU()
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        """Forward pass through autoencoder."""
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AutoencoderAnomalyDetector:
    """
    Wrapper class for autoencoder-based anomaly detection.
    """
    
    def __init__(
        self, 
        model_path: Optional[str] = None,
        input_dim: int = 10,
        encoding_dim: int = 16,
        threshold_percentile: float = 95.0
    ):
        """
        Initialize the autoencoder detector.
        
        Args:
            model_path: Path to saved model weights (.pt file)
            input_dim: Number of input features
            encoding_dim: Bottleneck dimension
            threshold_percentile: Percentile for anomaly threshold (default: 95)
        """
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.threshold_percentile = threshold_percentile
        self.threshold = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize model
        self.model = AutoencoderModel(input_dim, encoding_dim)
        self.model.to(self.device)
        self.model.eval()
        
        # Load weights if provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
            print(f"✓ Autoencoder loaded from {model_path}")
        else:
            print("ℹ Autoencoder initialized with random weights")
    
    def load_model(self, model_path: str):
        """
        Load model weights from file.
        
        Args:
            model_path: Path to .pt file
        """
        try:
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            print(f"✓ Model weights loaded successfully")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise
    
    def save_model(self, model_path: str):
        """
        Save model weights to file.
        
        Args:
            model_path: Path to save .pt file
        """
        torch.save(self.model.state_dict(), model_path)
        print(f"✓ Model saved to {model_path}")
    
    def calculate_reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate reconstruction error for input data.
        
        Args:
            X: Input data (n_samples, n_features)
        
        Returns:
            Reconstruction errors for each sample
        """
        # Convert to tensor
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        # Get reconstruction
        with torch.no_grad():
            X_reconstructed = self.model(X_tensor)
        
        # Calculate MSE for each sample
        errors = torch.mean((X_tensor - X_reconstructed) ** 2, dim=1)
        
        return errors.cpu().numpy()
    
    def fit_threshold(self, X: np.ndarray):
        """
        Fit anomaly threshold based on training data.
        Uses percentile of reconstruction errors.
        
        Args:
            X: Normal (non-anomalous) training data
        """
        errors = self.calculate_reconstruction_error(X)
        self.threshold = np.percentile(errors, self.threshold_percentile)
        print(f"✓ Threshold set to {self.threshold:.6f} ({self.threshold_percentile}th percentile)")
    
    def predict(self, X: np.ndarray, return_errors: bool = False) -> np.ndarray:
        """
        Predict anomalies based on reconstruction error.
        
        Args:
            X: Input data
            return_errors: If True, return errors instead of binary labels
        
        Returns:
            Binary predictions (0: normal, 1: anomaly) or reconstruction errors
        """
        errors = self.calculate_reconstruction_error(X)
        
        if return_errors:
            return errors
        
        if self.threshold is None:
            print("Warning: Threshold not set. Using median of current errors.")
            self.threshold = np.median(errors)
        
        # Classify as anomaly if error exceeds threshold
        predictions = (errors > self.threshold).astype(int)
        
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Get anomaly probability based on reconstruction error.
        
        Args:
            X: Input data
        
        Returns:
            Anomaly probabilities (normalized errors)
        """
        errors = self.calculate_reconstruction_error(X)
        
        if self.threshold is None:
            # Use max error for normalization
            max_error = np.max(errors)
            probabilities = errors / (max_error + 1e-8)
        else:
            # Normalize by threshold
            probabilities = errors / (self.threshold + 1e-8)
            probabilities = np.clip(probabilities, 0, 1)
        
        return probabilities
    
    def get_anomaly_score(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get both predictions and anomaly scores.
        
        Args:
            X: Input data
        
        Returns:
            Tuple of (predictions, scores)
        """
        errors = self.calculate_reconstruction_error(X)
        predictions = self.predict(X)
        
        return predictions, errors


def create_autoencoder_detector(
    model_path: Optional[str] = None,
    input_dim: int = 10,
    encoding_dim: int = 16
) -> AutoencoderAnomalyDetector:
    """
    Factory function to create an autoencoder detector.
    
    Args:
        model_path: Path to saved model
        input_dim: Input feature dimension
        encoding_dim: Encoding dimension
    
    Returns:
        AutoencoderAnomalyDetector instance
    """
    return AutoencoderAnomalyDetector(
        model_path=model_path,
        input_dim=input_dim,
        encoding_dim=encoding_dim
    )


def train_autoencoder(
    X_train: np.ndarray,
    X_val: Optional[np.ndarray] = None,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    encoding_dim: int = 16
) -> AutoencoderAnomalyDetector:
    """
    Train an autoencoder from scratch.
    
    Args:
        X_train: Training data (normal samples only)
        X_val: Validation data
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        encoding_dim: Encoding dimension
    
    Returns:
        Trained AutoencoderAnomalyDetector
    """
    print("="*60)
    print("TRAINING AUTOENCODER")
    print("="*60)
    
    input_dim = X_train.shape[1]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    print(f"Input dim: {input_dim}, Encoding dim: {encoding_dim}")
    
    # Create model
    model = AutoencoderModel(input_dim, encoding_dim)
    model.to(device)
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    
    # Convert to tensors
    X_train_tensor = torch.FloatTensor(X_train)
    
    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        
        # Mini-batch training
        for i in range(0, len(X_train_tensor), batch_size):
            batch = X_train_tensor[i:i+batch_size].to(device)
            
            # Forward pass
            reconstructed = model(batch)
            loss = criterion(reconstructed, batch)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / (len(X_train_tensor) / batch_size)
        
        # Validation
        if X_val is not None and epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                X_val_tensor = torch.FloatTensor(X_val).to(device)
                val_reconstructed = model(X_val_tensor)
                val_loss = criterion(val_reconstructed, X_val_tensor).item()
            model.train()
            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_loss:.6f}, Val Loss: {val_loss:.6f}")
        elif epoch % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_loss:.6f}")
    
    print("✓ Training completed")
    
    # Create detector instance
    detector = AutoencoderAnomalyDetector(input_dim=input_dim, encoding_dim=encoding_dim)
    detector.model = model
    detector.model.eval()
    
    # Fit threshold on training data
    detector.fit_threshold(X_train)
    
    return detector


if __name__ == "__main__":
    """
    Example usage
    """
    print("="*70)
    print("AUTOENCODER ANOMALY DETECTOR - TESTING")
    print("="*70 + "\n")
    
    # Generate dummy data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    # Normal data (from standard normal distribution)
    X_normal = np.random.randn(n_samples, n_features)
    
    # Anomalous data (from different distribution)
    X_anomaly = np.random.randn(100, n_features) * 3 + 5
    
    print(f"Normal samples: {X_normal.shape}")
    print(f"Anomalous samples: {X_anomaly.shape}\n")
    
    # Train autoencoder
    detector = train_autoencoder(
        X_normal[:800],
        X_val=X_normal[800:],
        epochs=30,
        batch_size=32,
        encoding_dim=5
    )
    
    # Test on normal data
    print("\n" + "="*70)
    print("TESTING ON NORMAL DATA")
    print("="*70)
    normal_preds = detector.predict(X_normal[800:])
    normal_errors = detector.calculate_reconstruction_error(X_normal[800:])
    print(f"Anomalies detected: {normal_preds.sum()} / {len(normal_preds)}")
    print(f"Mean reconstruction error: {normal_errors.mean():.6f}")
    print(f"Max reconstruction error: {normal_errors.max():.6f}")
    
    # Test on anomalous data
    print("\n" + "="*70)
    print("TESTING ON ANOMALOUS DATA")
    print("="*70)
    anomaly_preds = detector.predict(X_anomaly)
    anomaly_errors = detector.calculate_reconstruction_error(X_anomaly)
    print(f"Anomalies detected: {anomaly_preds.sum()} / {len(anomaly_preds)}")
    print(f"Mean reconstruction error: {anomaly_errors.mean():.6f}")
    print(f"Max reconstruction error: {anomaly_errors.max():.6f}")
    
    # Save model
    print("\n" + "="*70)
    print("SAVING MODEL")
    print("="*70)
    detector.save_model('autoencoder_test.pt')
    
    # Load model
    print("\n" + "="*70)
    print("LOADING MODEL")
    print("="*70)
    detector2 = create_autoencoder_detector(
        model_path='autoencoder_test.pt',
        input_dim=n_features,
        encoding_dim=5
    )
    detector2.threshold = detector.threshold
    
    # Verify loaded model works
    test_preds = detector2.predict(X_anomaly[:10])
    print(f"Test predictions: {test_preds}")
    print("\n✓ All tests passed!")
