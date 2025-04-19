import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor
import joblib

class SimplifiedProductRecommender:
    def __init__(self, csv_path):
        """Initialize the recommender with product data from a CSV file."""
        # Load data from CSV file
        self.df = pd.read_csv(csv_path)
        
        # Ensure price and rating are numeric
        self.df['price'] = pd.to_numeric(self.df['price'])
        self.df['rating'] = pd.to_numeric(self.df['rating'])
        
        # Create a value score that balances price and rating
        self.df['value_score'] = self.df['rating'] / self.df['price']
        
        # Initialize models
        self.similarity_matrix = None
        self.prediction_model = None
        self.is_trained = False
        
    def train_models(self):
        """Train the similarity model and prediction model for recommendations."""
        # 1. Similarity-based model
        self._train_similarity_model()
        
        # 2. Price-quality prediction model for customer satisfaction
        self._train_prediction_model()
        
        self.is_trained = True
        print("Models trained successfully.")
        
    def _train_similarity_model(self):
        """Train a content-based similarity model."""
        # Create feature matrix for similarity calculation
        # Using category as a one-hot encoded feature
        categories = pd.get_dummies(self.df['category'])
        
        # Create a price range feature (normalized)
        scaler = StandardScaler()
        price_scaled = scaler.fit_transform(self.df[['price']])
        
        # Combine features
        features = np.hstack((categories.values, price_scaled, self.df[['rating']].values))
        
        # Calculate similarity matrix
        self.similarity_matrix = cosine_similarity(features)
        
        # Store category encodings for future use
        self.category_features = categories.columns.tolist()
        self.price_scaler = scaler
        
    def _train_prediction_model(self):
        """Train a model to predict if a customer will like a product based on its attributes."""
        # Features: price, category (one-hot encoded)
        categories = pd.get_dummies(self.df['category'])
        X = pd.concat([self.df[['price']], categories], axis=1)
        
        # Target: rating (we're assuming ratings represent user satisfaction)
        y = self.df['rating']
        
        # Train model
        self.prediction_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.prediction_model.fit(X, y)
        
    def save_models(self, path="product_recommender_models"):
        """Save trained models to disk."""
        import os
        if not os.path.exists(path):
            os.makedirs(path)
            
        # Save similarity matrix
        np.save(f"{path}/similarity_matrix.npy", self.similarity_matrix)
        
        # Save prediction model
        joblib.dump(self.prediction_model, f"{path}/prediction_model.pkl")
        
        # Save scaler
        joblib.dump(self.price_scaler, f"{path}/price_scaler.pkl")
        
        # Save category features
        pd.Series(self.category_features).to_csv(f"{path}/category_features.csv", index=False)
        
        print(f"Models saved to {path}")
        
    def load_models(self, path="product_recommender_models"):
        """Load trained models from disk."""
        import os
        if not os.path.exists(path):
            print("Model path does not exist. Models need to be trained first.")
            return False
            
        # Load similarity matrix
        self.similarity_matrix = np.load(f"{path}/similarity_matrix.npy")
        
        # Load prediction model
        self.prediction_model = joblib.load(f"{path}/prediction_model.pkl")
        
        # Load scaler
        self.price_scaler = joblib.load(f"{path}/price_scaler.pkl")
        
        # Load category features
        self.category_features = pd.read_csv(f"{path}/category_features.csv").iloc[:, 0].tolist()
        
        self.is_trained = True
        print("Models loaded successfully.")
        return True
    
    def get_similar_products(self, product_id, top_n=5):
        """Find the most similar products to the given product."""
        if not self.is_trained:
            print("Models are not trained. Call train_models() first.")
            return None
            
        # Find the product index
        try:
            idx = self.df[self.df['product_id'] == product_id].index[0]
        except IndexError:
            return f"Product {product_id} not found in database."
            
        # Get similarity scores
        similarity_scores = self.similarity_matrix[idx]
        
        # Get indices of most similar products (excluding the product itself)
        similar_indices = similarity_scores.argsort()[::-1][1:top_n+1]
        
        # Return similar products
        return self.df.iloc[similar_indices]
    
    def predict_user_satisfaction(self, product_id):
        """Predict how likely a user is to be satisfied with a product."""
        if not self.is_trained or self.prediction_model is None:
            print("Prediction model is not trained. Call train_models() first.")
            return None
            
        # Find the product
        try:
            product = self.df[self.df['product_id'] == product_id].iloc[0]
        except IndexError:
            return f"Product {product_id} not found in database."
            
        # Prepare features
        category_one_hot = pd.DataFrame(columns=self.category_features)
        category_one_hot.loc[0] = 0
        category_one_hot[product['category']] = 1
        
        X = pd.concat([pd.DataFrame({'price': [product['price']]}), category_one_hot], axis=1)
        
        # Predict satisfaction (rating)
        predicted_rating = self.prediction_model.predict(X)[0]
        
        return predicted_rating
    
    def recommend_alternatives(self, product_id, top_n=3, method='basic'):
        """
        Recommend cheaper alternatives with good ratings for a given product.
        
        Args:
            product_id: The ID of the scanned product
            top_n: Number of recommendations to return
            method: Recommendation method ('basic' or 'similar')
            
        Returns:
            DataFrame with recommended alternatives
        """
        # Find the product
        try:
            target_product = self.df[self.df['product_id'] == product_id].iloc[0]
        except IndexError:
            return f"Product {product_id} not found in database."
        
        if method == 'basic':
            # Use the basic method based on category
            category = target_product['category']
            category_products = self.df[self.df['category'] == category].copy()
            
            # Filter for cheaper products
            cheaper_products = category_products[
                (category_products['price'] < target_product['price']) &
                (category_products['product_id'] != product_id)
            ]
            
            if cheaper_products.empty:
                return f"No cheaper alternatives found for {target_product['product_name']}."
            
            # Sort by value score
            cheaper_products = cheaper_products.sort_values('value_score', ascending=False)
            recommendations = cheaper_products.head(top_n).copy()
            
        elif method == 'similar' and self.is_trained:
            # Use similarity-based recommendations
            similar_products = self.get_similar_products(product_id, top_n=10)
            
            if isinstance(similar_products, str):
                return similar_products
                
            # Filter for cheaper products
            cheaper_similar = similar_products[
                similar_products['price'] < target_product['price']
            ]
            
            if cheaper_similar.empty:
                return f"No cheaper similar alternatives found for {target_product['product_name']}."
                
            recommendations = cheaper_similar.head(top_n).copy()
            
        else:
            return "Invalid method or models not trained. Choose 'basic' or 'similar'."
        
        # Calculate savings and value improvement
        recommendations['price_savings'] = target_product['price'] - recommendations['price']
        recommendations['price_savings_pct'] = (recommendations['price_savings'] / target_product['price'] * 100).round(1)
        recommendations['rating_diff'] = (recommendations['rating'] - target_product['rating']).round(1)
        
        # Add predicted user satisfaction if available
        if self.is_trained and self.prediction_model is not None:
            recommendations['predicted_rating'] = recommendations['product_id'].apply(self.predict_user_satisfaction)
        
        # Format the output for better readability
        result_cols = ['product_id', 'product_name', 'price', 'rating', 
                      'price_savings', 'price_savings_pct', 'rating_diff']
        
        if 'predicted_rating' in recommendations.columns:
            result_cols.append('predicted_rating')
            
        recommendations = recommendations[result_cols]
        
        return {
            'original_product': {
                'product_id': target_product['product_id'],
                'product_name': target_product['product_name'],
                'category': target_product['category'],
                'price': target_product['price'],
                'rating': target_product['rating']
            },
            'recommendations': recommendations.to_dict('records')
        }
    
    def scan_product(self, product_id, method='basic'):
        """Simulate scanning a product and getting recommendations."""
        recommendations = self.recommend_alternatives(product_id, method=method)
        
        if isinstance(recommendations, str):
            return recommendations
        
        original = recommendations['original_product']
        recs = recommendations['recommendations']
        
        print(f"Scanned Product: {original['product_name']} (₹{float(original['price']):.2f}, Rating: {original['rating']})")
        print(f"Category: {original['category']}")
        print(f"Recommendation Method: {method}")
        print("\nRecommended Alternatives:")
        
        for i, rec in enumerate(recs, 1):
            price_diff = float(rec['price_savings'])
            price_diff_pct = float(rec['price_savings_pct'])
            rating_diff = float(rec['rating_diff'])
            
            rating_indicator = "↑" if rating_diff > 0 else "↓"
            if rating_diff == 0:
                rating_indicator = "="
                
            print(f"{i}. {rec['product_name']} - ₹{float(rec['price']):.2f} (Save ₹{price_diff:.2f}, {price_diff_pct}%)")
            print(f"   Rating: {rec['rating']} {rating_indicator}")
            
            if 'predicted_rating' in rec:
                pred_rating = float(rec['predicted_rating'])
                print(f"   Predicted Satisfaction: {pred_rating:.1f}/5.0")
                
            print()
            
        return recommendations

# Example usage
if __name__ == "__main__":
    csv_path = "category.csv"  # Replace with the path to your actual CSV file
    
    # Create the simplified recommender
    recommender = SimplifiedProductRecommender(csv_path)
    
    # Train the models
    recommender.train_models()
    
    # Save models for future use
    recommender.save_models()
    
    # Or load pre-trained models
    recommender.load_models()
    
    # Example recommendations with different methods
    print("BASIC RECOMMENDATIONS:")
    recommender.scan_product('HO_7443', method='basic')
    
    print("\nSIMILARITY-BASED RECOMMENDATIONS:")
    recommender.scan_product('HO_7443', method='similar')