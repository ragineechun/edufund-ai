# models/semantic_search.py - FIXED VERSION
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re
import json

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

class SemanticSearchEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.scholarship_vectors = None
        self.scholarship_texts = []
        self.scholarship_ids = []
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for semantic search"""
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Tokenize
        try:
            tokens = nltk.word_tokenize(text)
        except:
            tokens = text.split()
        
        # Remove stopwords and lemmatize
        tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        return ' '.join(tokens)
    
    def index_scholarships(self, scholarships: list):
        """Index scholarships for semantic search"""
        if not scholarships:
            print("No scholarships to index")
            return
        
        # Prepare text corpus from scholarships
        texts = []
        ids = []
        
        for s in scholarships:
            # Safely get each field, convert None to empty string
            name = s.get('name') or ''
            provider = s.get('provider') or ''
            description = s.get('description') or ''
            eligible_courses = s.get('eligible_courses') or ''
            other_requirements = s.get('other_requirements') or ''
            
            # Convert lists to strings if needed
            if isinstance(eligible_courses, list):
                eligible_courses = ' '.join(str(c) for c in eligible_courses)
            if isinstance(other_requirements, list):
                other_requirements = ' '.join(str(r) for r in other_requirements)
            
            # Combine all relevant fields
            text_parts = [
                str(name),
                str(provider),
                str(description),
                str(eligible_courses),
                str(other_requirements)
            ]
            
            # Filter out empty strings and join
            text_parts = [part for part in text_parts if part and part.strip()]
            
            if not text_parts:
                # If all fields are empty, use a placeholder
                text_parts = [f"Scholarship {s.get('id', 'unknown')}"]
            
            combined_text = ' '.join(text_parts)
            processed_text = self.preprocess_text(combined_text)
            
            texts.append(processed_text)
            ids.append(s.get('id'))
        
        # Create TF-IDF vectors
        if texts:
            self.scholarship_vectors = self.vectorizer.fit_transform(texts)
            self.scholarship_texts = texts
            self.scholarship_ids = ids
            print(f"✅ Indexed {len(scholarships)} scholarships for semantic search")
        else:
            print("⚠️ No valid text to index")
    
    def search(self, query: str, top_k: int = 10) -> list:
        """Search for scholarships using semantic similarity"""
        if self.scholarship_vectors is None:
            return []
        
        if not query:
            return []
        
        # Process query
        processed_query = self.preprocess_text(query)
        
        if not processed_query:
            return []
        
        # Transform query
        try:
            query_vector = self.vectorizer.transform([processed_query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.scholarship_vectors).flatten()
            
            # Get top-k results
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    results.append({
                        'scholarship_id': self.scholarship_ids[idx],
                        'similarity_score': float(similarities[idx]),
                        'matched_text': self.scholarship_texts[idx][:200]  # Preview
                    })
            
            return results
        except Exception as e:
            print(f"Error in search: {e}")
            return []
    
    def find_similar_scholarships(self, scholarship_id: int, scholarships: list, top_k: int = 5) -> list:
        """Find scholarships similar to a given one"""
        try:
            # First, ensure we have vectors
            if self.scholarship_vectors is None:
                self.index_scholarships(scholarships)
            
            if self.scholarship_vectors is None:
                return []
            
            # Find the index of the given scholarship
            try:
                idx = self.scholarship_ids.index(scholarship_id)
            except ValueError:
                return []
            
            # Calculate similarity scores
            similarity_scores = cosine_similarity(
                self.scholarship_vectors[idx], 
                self.scholarship_vectors
            ).flatten()
            
            # Get top similar (excluding self)
            top_indices = similarity_scores.argsort()[-top_k-1:-1][::-1]
            
            results = []
            for idx in top_indices:
                if idx < len(self.scholarship_ids):
                    results.append({
                        'scholarship_id': self.scholarship_ids[idx],
                        'similarity_score': float(similarity_scores[idx])
                    })
            
            return results
        except Exception as e:
            print(f"Error finding similar scholarships: {e}")
            return []
    
    def get_keywords(self, text: str, top_n: int = 10) -> list:
        """Extract important keywords from text"""
        if not text:
            return []
        
        processed = self.preprocess_text(text)
        if not processed:
            return []
        
        try:
            # Transform to get feature names
            vector = self.vectorizer.transform([processed])
            
            # Get feature names (words)
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get non-zero features
            indices = vector.nonzero()[1]
            
            # Get scores
            scores = vector[0, indices].toarray()[0]
            
            # Sort by score
            keyword_scores = [(feature_names[i], scores[j]) for j, i in enumerate(indices)]
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [kw for kw, _ in keyword_scores[:top_n]]
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []