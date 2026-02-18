"""
Data Preprocessing Module for API Anomaly Detection
====================================================
Handles data loading, cleaning, normalization, and train/test splitting.

Features:
- CSV data loading with validation
- Null value handling
- Feature normalization using StandardScaler
- Stratified train/test split (80/20)
- Data shuffling for randomization

Author: Research Team
Date: February 2026
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Tuple, Dict


class DataPreprocessor:
    """Handles all data preprocessing operations"""
    
    def __init__(self, dataset_path: str = 'api_telemetry_dataset.csv'):
        """
        Initialize preprocessor
        
        Args:
            dataset_path: Path to raw CSV dataset
        """
        self.dataset_path = dataset_path
        self.scaler = StandardScaler()
        self.feature_columns = [
            'avg_response_time',
            'request_count',
            'error_rate',
            'five_xx_rate',
            'four_xx_rate',
            'payload_avg_size',
            'unique_ip_count',
            'cpu_usage',
            'memory_usage'
        ]
    
    def load_data(self) -> pd.DataFrame:
        """
        Load dataset from CSV
        
        Returns:
            DataFrame with loaded data
        """
        print("📂 Loading dataset...")
        
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        
        df = pd.read_csv(self.dataset_path)
        print(f"   Loaded {len(df)} samples from {self.dataset_path}")
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dataset: remove nulls, handle outliers
        
        Args:
            df: Raw dataframe
        
        Returns:
            Cleaned dataframe
        """
        print("\n🧹 Cleaning data...")
        
        initial_count = len(df)
        
        # Check for null values
        null_counts = df[self.feature_columns].isnull().sum()
        if null_counts.any():
            print(f"   Found null values:")
            for col, count in null_counts[null_counts > 0].items():
                print(f"     {col}: {count} nulls")
        
        # Remove rows with null values
        df_clean = df.dropna(subset=self.feature_columns)
        removed = initial_count - len(df_clean)
        
        if removed > 0:
            print(f"   Removed {removed} rows with null values")
        else:
            print(f"   No null values found ✓")
        
        # Remove invalid values (negative metrics where not allowed)
        df_clean = df_clean[df_clean['avg_response_time'] >= 0]
        df_clean = df_clean[df_clean['request_count'] >= 0]
        df_clean = df_clean[df_clean['error_rate'] >= 0]
        df_clean = df_clean[df_clean['payload_avg_size'] >= 0]
        
        final_count = len(df_clean)
        total_removed = initial_count - final_count
        
        print(f"   Final count: {final_count} samples ({total_removed} removed)")
        
        return df_clean
    
    def normalize_features(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Normalize features using StandardScaler
        
        Args:
            X_train: Training features
            X_test: Testing features
        
        Returns:
            Tuple of (normalized X_train, normalized X_test)
        """
        print("\n📏 Normalizing features using StandardScaler...")
        
        # Fit scaler on training data only (avoid data leakage)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print(f"   Training set shape: {X_train_scaled.shape}")
        print(f"   Testing set shape: {X_test_scaled.shape}")
        print(f"   Feature means (after scaling): {X_train_scaled.mean(axis=0).round(4)}")
        print(f"   Feature stds (after scaling): {X_train_scaled.std(axis=0).round(4)}")
        
        return X_train_scaled, X_test_scaled
    
    def split_data(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Split data into train and test sets with stratification
        
        Args:
            df: Cleaned dataframe
            test_size: Proportion of test set (default 0.2 = 20%)
            random_state: Random seed for reproducibility
        
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        print(f"\n✂️  Splitting data (train/test = {int((1-test_size)*100)}/{int(test_size*100)})...")
        
        # Extract features and labels
        X = df[self.feature_columns].values
        y = df['label'].values
        
        # Stratified split to preserve class distribution
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,  # Maintain anomaly/normal ratio
            shuffle=True
        )
        
        print(f"   Training set: {len(X_train)} samples")
        print(f"     Normal: {(y_train == 0).sum()} ({(y_train == 0).sum()/len(y_train)*100:.2f}%)")
        print(f"     Anomaly: {(y_train == 1).sum()} ({(y_train == 1).sum()/len(y_train)*100:.2f}%)")
        
        print(f"   Testing set: {len(X_test)} samples")
        print(f"     Normal: {(y_test == 0).sum()} ({(y_test == 0).sum()/len(y_test)*100:.2f}%)")
        print(f"     Anomaly: {(y_test == 1).sum()} ({(y_test == 1).sum()/len(y_test)*100:.2f}%)")
        
        return X_train, X_test, y_train, y_test
    
    def save_scaler(self, output_path: str = 'models/scaler.pkl'):
        """
        Save fitted scaler for production use
        
        Args:
            output_path: Path to save scaler
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        joblib.dump(self.scaler, output_path)
        print(f"\n💾 Scaler saved to: {output_path}")
    
    def preprocess_pipeline(
        self,
        save_scaler: bool = True,
        scaler_path: str = 'models/scaler.pkl'
    ) -> Dict[str, np.ndarray]:
        """
        Complete preprocessing pipeline
        
        Args:
            save_scaler: Whether to save the fitted scaler
            scaler_path: Path to save scaler
        
        Returns:
            Dictionary with preprocessed data splits
        """
        print("="*70)
        print("🔬 DATA PREPROCESSING PIPELINE")
        print("="*70)
        
        # Step 1: Load data
        df = self.load_data()
        
        # Step 2: Clean data
        df_clean = self.clean_data(df)
        
        # Step 3: Split data
        X_train, X_test, y_train, y_test = self.split_data(df_clean)
        
        # Step 4: Normalize features
        X_train_scaled, X_test_scaled = self.normalize_features(X_train, X_test)
        
        # Step 5: Save scaler
        if save_scaler:
            self.save_scaler(scaler_path)
        
        print("\n" + "="*70)
        print("✅ PREPROCESSING COMPLETE")
        print("="*70)
        
        return {
            'X_train': X_train_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train,
            'y_test': y_test,
            'feature_names': self.feature_columns
        }
    
    def get_feature_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate feature statistics for analysis
        
        Args:
            df: Dataframe to analyze
        
        Returns:
            DataFrame with statistics
        """
        stats = df[self.feature_columns].describe()
        return stats


def main():
    """Main execution function"""
    # Initialize preprocessor
    preprocessor = DataPreprocessor(dataset_path='api_telemetry_dataset.csv')
    
    # Run preprocessing pipeline
    data = preprocessor.preprocess_pipeline(
        save_scaler=True,
        scaler_path='models/scaler.pkl'
    )
    
    # Save preprocessed data for training
    print("\n💾 Saving preprocessed data...")
    os.makedirs('models', exist_ok=True)
    
    np.save('models/X_train.npy', data['X_train'])
    np.save('models/X_test.npy', data['X_test'])
    np.save('models/y_train.npy', data['y_train'])
    np.save('models/y_test.npy', data['y_test'])
    
    print("   Saved:")
    print("     - models/X_train.npy")
    print("     - models/X_test.npy")
    print("     - models/y_train.npy")
    print("     - models/y_test.npy")
    print("     - models/scaler.pkl")
    
    print("\n✨ Preprocessing complete!")
    print("\nNext step: Run train_models.py to train ML models")


if __name__ == '__main__':
    main()
