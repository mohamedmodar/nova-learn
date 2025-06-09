import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import sys
import os
import importlib.util
import tensorflow as tf
import numpy as np

# Add parent directory for package import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

import config
import utils

# Import TwoTowerRecommender from file with parentheses
spec = importlib.util.spec_from_file_location("two_tower_cf", "two_recomendation(CF).py")
two_tower_cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(two_tower_cf)
TwoTowerRecommender = two_tower_cf.TwoTowerRecommender
filter_positive_interactions = two_tower_cf.filter_positive_interactions

class RecommenderTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Course Recommender Test Interface")
        self.root.geometry("1200x800")
        
        # Initialize data
        self.load_data()
        
        # Create main container
        self.main_container = ttk.Frame(root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create model section
        self.create_model_section()
        
        # Create user selection section
        self.create_user_section()
        
        # Create interactions section
        self.create_interactions_section()
        
        # Create recommendations section
        self.create_recommendations_section()
        
        # Create rating section
        self.create_rating_section()
        
        # Initialize recommender
        self.recommender = None
        
    def load_data(self):
        """Load course and interaction data"""
        print("Loading course data...")
        self.courses_df = utils.load_course_data(config.COURSE_DATA_PATH)
        if self.courses_df is None or self.courses_df.empty:
            raise ValueError("Failed to load course data")
            
        print("Loading interaction data...")
        self.interactions_df = pd.read_csv(config.INTERACTION_DATA_PATH, encoding='utf-8')
        if self.interactions_df.empty:
            raise ValueError("Interaction data is empty")
            
        # Get unique user IDs
        self.user_ids = sorted(self.interactions_df['user_id'].unique())
        
    def create_model_section(self):
        """Create model training section"""
        model_frame = ttk.LabelFrame(self.main_container, text="Model Training", padding="5")
        model_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(model_frame, text="Initialize Model", 
                  command=self.initialize_model).grid(row=0, column=0, padx=5)
        ttk.Button(model_frame, text="Train Model", 
                  command=self.train_model).grid(row=0, column=1, padx=5)
        ttk.Button(model_frame, text="Load Saved Model", 
                  command=self.load_saved_model).grid(row=0, column=2, padx=5)
        
        # Add status label
        self.model_status = ttk.Label(model_frame, text="Model Status: Not Initialized")
        self.model_status.grid(row=0, column=3, padx=5)
        
    def create_user_section(self):
        """Create user selection section"""
        user_frame = ttk.LabelFrame(self.main_container, text="User Selection", padding="5")
        user_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(user_frame, text="Select User ID:").grid(row=0, column=0, padx=5)
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(user_frame, textvariable=self.user_var, values=self.user_ids)
        self.user_combo.grid(row=0, column=1, padx=5)
        self.user_combo.bind('<<ComboboxSelected>>', self.on_user_selected)
        
        ttk.Button(user_frame, text="Load User Data", 
                  command=self.load_user_data).grid(row=0, column=2, padx=5)
        
    def create_interactions_section(self):
        """Create interactions display section"""
        interactions_frame = ttk.LabelFrame(self.main_container, text="User Interactions", padding="5")
        interactions_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Create treeview for interactions
        self.interactions_tree = ttk.Treeview(interactions_frame, 
                                            columns=('item_id', 'title', 'rating'), 
                                            show='headings')
        self.interactions_tree.heading('item_id', text='Course ID')
        self.interactions_tree.heading('title', text='Title')
        self.interactions_tree.heading('rating', text='Rating')
        self.interactions_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(interactions_frame, orient=tk.VERTICAL, 
                                 command=self.interactions_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.interactions_tree.configure(yscrollcommand=scrollbar.set)
        
    def create_recommendations_section(self):
        """Create recommendations display section"""
        recs_frame = ttk.LabelFrame(self.main_container, text="Recommendations", padding="5")
        recs_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Create treeview for recommendations
        self.recs_tree = ttk.Treeview(recs_frame, 
                                     columns=('title', 'similarity', 'rating', 'level', 'skills'),
                                     show='headings')
        self.recs_tree.heading('title', text='Title')
        self.recs_tree.heading('similarity', text='Similarity')
        self.recs_tree.heading('rating', text='Rating')
        self.recs_tree.heading('level', text='Level')
        self.recs_tree.heading('skills', text='Skills')
        self.recs_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(recs_frame, orient=tk.VERTICAL, 
                                 command=self.recs_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.recs_tree.configure(yscrollcommand=scrollbar.set)
        
        # Add refresh button
        ttk.Button(recs_frame, text="Refresh Recommendations", 
                  command=self.refresh_recommendations).grid(row=1, column=0, pady=5)
        
    def create_rating_section(self):
        """Create rating input section"""
        rating_frame = ttk.LabelFrame(self.main_container, text="Rate a Course", padding="5")
        rating_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(rating_frame, text="Course ID:").grid(row=0, column=0, padx=5)
        self.course_var = tk.StringVar()
        self.course_combo = ttk.Combobox(rating_frame, textvariable=self.course_var)
        self.course_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(rating_frame, text="Rating (1-5):").grid(row=0, column=2, padx=5)
        self.rating_var = tk.StringVar()
        self.rating_combo = ttk.Combobox(rating_frame, textvariable=self.rating_var, 
                                       values=['1', '2', '3', '4', '5'])
        self.rating_combo.grid(row=0, column=3, padx=5)
        
        ttk.Button(rating_frame, text="Submit Rating", 
                  command=self.submit_rating).grid(row=0, column=4, padx=5)
        
    def initialize_model(self):
        """Initialize the recommender model"""
        try:
            self.recommender = TwoTowerRecommender(
                courses_df=self.courses_df,
                user_interactions_df=self.interactions_df,
                model_weights_path=config.TWO_TOWER_MODEL_WEIGHTS_PATH
            )
            self.recommender.compile_model()
            self.model_status.config(text="Model Status: Initialized")
            messagebox.showinfo("Success", "Model initialized successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize model: {str(e)}")
            
    def train_model(self):
        """Train the recommender model"""
        if self.recommender is None:
            messagebox.showerror("Error", "Please initialize the model first")
            return
            
        try:
            # Prepare data
            train_dataset, test_dataset = self.recommender.prepare_data_for_training()
            
            # Train model
            history = self.recommender.train_model(train_dataset, test_dataset)
            
            # Save model weights
            self.recommender.save_model_weights()
            
            self.model_status.config(text="Model Status: Trained")
            messagebox.showinfo("Success", "Model trained successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to train model: {str(e)}")
            
    def load_saved_model(self):
        """Load saved model weights"""
        try:
            if self.recommender is None:
                self.initialize_model()
                
            if self.recommender.load_model_weights():
                self.model_status.config(text="Model Status: Loaded")
                messagebox.showinfo("Success", "Model loaded successfully")
            else:
                messagebox.showerror("Error", "Failed to load model weights")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")
            
    def on_user_selected(self, event):
        """Handle user selection"""
        self.load_user_data()
        
    def load_user_data(self):
        """Load data for selected user"""
        user_id = self.user_var.get()
        if not user_id:
            return
            
        if self.recommender is None:
            messagebox.showerror("Error", "Please initialize the model first")
            return
        
        # Load user interactions
        user_interactions = self.interactions_df[self.interactions_df['user_id'] == user_id]
        self.interactions_tree.delete(*self.interactions_tree.get_children())
        
        for _, row in user_interactions.iterrows():
            course_info = self.courses_df[self.courses_df['item_id'] == row['item_id']].iloc[0]
            self.interactions_tree.insert('', 'end', values=(
                row['item_id'],
                course_info['title'],
                row['rating']
            ))
        
        # Update course combo box
        self.course_combo['values'] = sorted(self.courses_df['item_id'].unique())
        
        # Get recommendations
        self.refresh_recommendations()
        
    def refresh_recommendations(self):
        """Refresh recommendations for current user"""
        user_id = self.user_var.get()
        if not user_id or self.recommender is None:
            return
            
        try:
            # Get recommendations
            recommendations = self.recommender.get_recommendations(user_id, top_k=10)
            
            # Clear current recommendations
            self.recs_tree.delete(*self.recs_tree.get_children())
            
            # Add new recommendations
            for _, row in recommendations.iterrows():
                self.recs_tree.insert('', 'end', values=(
                    row['title'],
                    f"{row['similarity_score']:.4f}",
                    row.get('adjusted_rating', 'N/A'),
                    row.get('level', 'N/A'),
                    ', '.join(row.get('skills_list', [])) if isinstance(row.get('skills_list'), list) else 'N/A'
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get recommendations: {str(e)}")
            
    def submit_rating(self):
        """Submit a new rating"""
        user_id = self.user_var.get()
        course_id = self.course_var.get()
        rating = self.rating_var.get()
        
        if not all([user_id, course_id, rating]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        try:
            rating = float(rating)
            if not (1 <= rating <= 5):
                raise ValueError("Rating must be between 1 and 5")
                
            # Add new interaction
            new_interaction = pd.DataFrame({
                'user_id': [user_id],
                'item_id': [course_id],
                'rating': [rating]
            })
            self.interactions_df = pd.concat([self.interactions_df, new_interaction], ignore_index=True)
            
            # Save updated interactions
            self.interactions_df.to_csv(config.INTERACTION_DATA_PATH, index=False)
            
            # Refresh display
            self.load_user_data()
            messagebox.showinfo("Success", "Rating submitted successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))

def main():
    root = tk.Tk()
    app = RecommenderTestGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 