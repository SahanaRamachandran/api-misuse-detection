"""
Export Script for CSIC Autoencoder Model

This script provides utilities to export and convert the CSIC autoencoder model.
Supports both TensorFlow (from notebook) and PyTorch (for ml_anomaly_detection).

Note: The original notebook uses TensorFlow/Keras.
This script can work with TensorFlow models or help convert to PyTorch.
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

# Set paths
SCRIPT_DIR = Path(__file__).parent
MODELS_DIR = SCRIPT_DIR / 'models' / 'CSIC'
DATASET_PATH = SCRIPT_DIR / 'datasets' / 'processed' / 'csic_database.csv'

# Create models directory if it doesn't exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("CSIC Autoencoder Model Export Script")
print("="*70)


def load_and_prepare_data(dataset_path):
    """Load and prepare CSIC dataset for autoencoder."""
    print(f"\nLoading dataset from: {dataset_path}")
    
    if not dataset_path.exists():
        print(f"Warning: Dataset not found at {dataset_path}")
        return None, None
    
    df = pd.read_csv(dataset_path)
    print(f"Dataset loaded: {len(df)} samples")
    
    # Fill NaN values
    df = df.fillna("")
    
    # Combine text columns
    text_columns = [
        'Method', 'User-Agent', 'Pragma', 'Cache-Control',
        'Accept', 'Accept-encoding', 'Accept-charset',
        'language', 'host', 'cookie', 'content-type',
        'connection', 'lenght', 'content', 'URL'
    ]
    
    existing_cols = [col for col in text_columns if col in df.columns]
    df['combined_text'] = df[existing_cols].astype(str).agg(' '.join, axis=1)
    
    texts = df['combined_text']
    
    print(f"Text features prepared")
    return texts, df


def create_features_and_scaler(texts):
    """Create TF-IDF features and scaler."""
    print("\n" + "="*70)
    print("CREATING FEATURES")
    print("="*70)
    
    # Create TF-IDF features
    print("\nCreating TF-IDF features...")
    vectorizer = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2),
        stop_words='english'
    )
    
    X_tfidf = vectorizer.fit_transform(texts)
    print(f"TF-IDF features created: {X_tfidf.shape}")
    
    # Convert to dense array
    X_dense = X_tfidf.toarray()
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_dense)
    print(f"Features scaled: {X_scaled.shape}")
    
    return X_scaled, vectorizer, scaler


def train_pytorch_autoencoder(X_scaled):
    """Train PyTorch autoencoder (compatible with ml_anomaly_detection)."""
    print("\n" + "="*70)
    print("TRAINING PYTORCH AUTOENCODER")
    print("="*70)
    
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError:
        print("Error: PyTorch not installed")
        return None
    
    # Split data
    X_train, X_test = train_test_split(X_scaled, test_size=0.2, random_state=42)
    
    input_dim = X_scaled.shape[1]
    encoding_dim = 32
    
    print(f"\nArchitecture:")
    print(f"  Input dim: {input_dim}")
    print(f"  Encoding dim: {encoding_dim}")
    
    # Define model
    class Autoencoder(nn.Module):
        def __init__(self, input_dim, encoding_dim=32):
            super(Autoencoder, self).__init__()
            
            # Encoder
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, encoding_dim),
                nn.ReLU()
            )
            
            # Decoder
            self.decoder = nn.Sequential(
                nn.Linear(encoding_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 128),
                nn.ReLU(),
                nn.Linear(128, input_dim),
                nn.Sigmoid()
            )
        
        def forward(self, x):
            encoded = self.encoder(x)
            decoded = self.decoder(encoded)
            return decoded
    
    # Create model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Autoencoder(input_dim, encoding_dim).to(device)
    
    print(f"Device: {device}")
    
    # Training setup
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Prepare data
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.FloatTensor(X_train)
    )
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    
    # Training loop
    print("\nTraining...")
    epochs = 20
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)
            
            # Forward pass
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        
        if (epoch + 1) % 5 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")
    
    print("✓ Training complete")
    
    # Test reconstruction
    model.eval()
    with torch.no_grad():
        X_test_tensor = torch.FloatTensor(X_test[:100]).to(device)
        reconstructed = model(X_test_tensor)
        test_loss = criterion(reconstructed, X_test_tensor).item()
        print(f"\nTest reconstruction loss: {test_loss:.6f}")
    
    return model


def export_pytorch_model(model, vectorizer, scaler):
    """Export PyTorch autoencoder model."""
    print("\n" + "="*70)
    print("EXPORTING PYTORCH MODEL")
    print("="*70)
    
    import torch
    
    # Export model weights
    model_path = MODELS_DIR / 'autoencoder_model.pt'
    torch.save(model.state_dict(), model_path)
    print(f"✓ PyTorch model saved to: {model_path}")
    
    # Export vectorizer
    vectorizer_path = MODELS_DIR / 'autoencoder_vectorizer.pkl'
    joblib.dump(vectorizer, vectorizer_path)
    print(f"✓ Vectorizer saved to: {vectorizer_path}")
    
    # Export scaler
    scaler_path = MODELS_DIR / 'autoencoder_scaler.pkl'
    joblib.dump(scaler, scaler_path)
    print(f"✓ Scaler saved to: {scaler_path}")
    
    # Create metadata
    metadata = {
        'model_type': 'PyTorch Autoencoder',
        'dataset': 'CSIC 2010',
        'input_dim': 3000,
        'encoding_dim': 32,
        'architecture': 'input->128->64->32->64->128->output',
        'export_date': pd.Timestamp.now().isoformat()
    }
    
    metadata_path = MODELS_DIR / 'autoencoder_metadata.pkl'
    joblib.dump(metadata, metadata_path)
    print(f"✓ Metadata saved to: {metadata_path}")
    
    print("\n" + "="*70)
    print("EXPORT COMPLETE")
    print("="*70)


def create_placeholder_model():
    """Create a placeholder autoencoder model for testing."""
    print("\n" + "="*70)
    print("CREATING PLACEHOLDER MODEL")
    print("="*70)
    print("\nNo dataset available. Creating placeholder model...")
    
    try:
        import torch
        import torch.nn as nn
        
        # Create dummy model
        class DummyAutoencoder(nn.Module):
            def __init__(self, input_dim=3000, encoding_dim=32):
                super(DummyAutoencoder, self).__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(input_dim, 128),
                    nn.ReLU(),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Linear(64, encoding_dim),
                    nn.ReLU()
                )
                self.decoder = nn.Sequential(
                    nn.Linear(encoding_dim, 64),
                    nn.ReLU(),
                    nn.Linear(64, 128),
                    nn.ReLU(),
                    nn.Linear(128, input_dim),
                    nn.Sigmoid()
                )
            
            def forward(self, x):
                return self.decoder(self.encoder(x))
        
        model = DummyAutoencoder()
        
        # Save placeholder
        model_path = MODELS_DIR / 'autoencoder_model_placeholder.pt'
        torch.save(model.state_dict(), model_path)
        print(f"✓ Placeholder model saved to: {model_path}")
        print("\nNote: This is an untrained model for structure reference only.")
        print("Train with real data for production use.")
        
    except ImportError:
        print("PyTorch not available. Skipping placeholder creation.")


def main():
    """Main export workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export CSIC Autoencoder model')
    parser.add_argument('--dataset', type=str, default=None,
                       help='Path to CSIC CSV dataset')
    parser.add_argument('--placeholder', action='store_true',
                       help='Create placeholder model structure')
    
    args = parser.parse_args()
    
    if args.placeholder:
        create_placeholder_model()
        return 0
    
    # Use custom dataset path if provided
    dataset_path = Path(args.dataset) if args.dataset else DATASET_PATH
    
    # Load data
    texts, df = load_and_prepare_data(dataset_path)
    
    if texts is None:
        print("\nDataset not found. Creating placeholder model instead...")
        create_placeholder_model()
        print("\nTo train a real model:")
        print(f"  1. Place CSIC dataset CSV at: {DATASET_PATH}")
        print(f"  2. Or specify path: python export_autoencoder.py --dataset /path/to/csic.csv")
        return 0
    
    # Create features
    X_scaled, vectorizer, scaler = create_features_and_scaler(texts)
    
    # Train PyTorch autoencoder
    model = train_pytorch_autoencoder(X_scaled)
    
    if model is None:
        print("\nError: Could not train model")
        return 1
    
    # Export model
    export_pytorch_model(model, vectorizer, scaler)
    
    print("\n✓ All steps completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
