import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
from recommender_interface_advanced_v6 import get_hybrid_recommendations_advanced

class RecommenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Course Recommender System")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Query input
        ttk.Label(main_frame, text="Search Query:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.query_entry = ttk.Entry(main_frame, width=50)
        self.query_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Level selection
        ttk.Label(main_frame, text="Level:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.level_var = tk.StringVar(value="All Levels")
        level_combo = ttk.Combobox(main_frame, textvariable=self.level_var)
        level_combo['values'] = ('All Levels', 'Beginner', 'Intermediate', 'Advanced')
        level_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Skills input
        ttk.Label(main_frame, text="Skills (comma-separated):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.skills_entry = ttk.Entry(main_frame, width=50)
        self.skills_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Duration preference
        ttk.Label(main_frame, text="Duration:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.StringVar(value="any")
        duration_combo = ttk.Combobox(main_frame, textvariable=self.duration_var)
        duration_combo['values'] = ('any', 'short', 'medium', 'long')
        duration_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Model selection
        ttk.Label(main_frame, text="Model:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="hybrid_tfidf_sbert")
        model_combo = ttk.Combobox(main_frame, textvariable=self.model_var)
        model_combo['values'] = ('hybrid_tfidf_sbert', 'tfidf', 'sbert', 'two_tower')
        model_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Search button
        search_button = ttk.Button(main_frame, text="Search", command=self.search)
        search_button.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Results area
        ttk.Label(main_frame, text="Results:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.results_text = scrolledtext.ScrolledText(main_frame, width=80, height=20)
        self.results_text.grid(row=7, column=0, columnspan=3, pady=5)
        
    def search(self):
        # Get input values
        query = self.query_entry.get()
        level = self.level_var.get()
        skills = [s.strip() for s in self.skills_entry.get().split(',')] if self.skills_entry.get() else None
        duration = self.duration_var.get()
        model_type = self.model_var.get()
        
        # Get recommendations
        results = get_hybrid_recommendations_advanced(
            query_text=query,
            level=level,
            skills=skills,
            duration_pref=duration if duration != 'any' else None,
            model_type=model_type
        )
        
        # Display results
        self.results_text.delete(1.0, tk.END)
        if results.empty:
            self.results_text.insert(tk.END, "No recommendations found.")
        else:
            for _, row in results.iterrows():
                self.results_text.insert(tk.END, f"Title: {row['title']}\n")
                self.results_text.insert(tk.END, f"Provider: {row['provider']}\n")
                self.results_text.insert(tk.END, f"Level: {row['level']}\n")
                self.results_text.insert(tk.END, f"Skills: {row['skills_list']}\n")
                self.results_text.insert(tk.END, f"Rating: {row['adjusted_rating']}\n")
                self.results_text.insert(tk.END, f"Duration: {row['duration']}\n")
                if 'two_tower_similarity_score' in row and not pd.isna(row['two_tower_similarity_score']):
                    self.results_text.insert(tk.END, f"Two-Tower Score: {row['two_tower_similarity_score']:.4f}\n")
                elif 'sbert_similarity_score' in row and not pd.isna(row['sbert_similarity_score']):
                    self.results_text.insert(tk.END, f"SBERT Score: {row['sbert_similarity_score']:.4f}\n")
                elif 'content_score' in row and not pd.isna(row['content_score']):
                    self.results_text.insert(tk.END, f"Content Score: {row['content_score']:.4f}\n")
                self.results_text.insert(tk.END, f"URL: {row['url']}\n")
                self.results_text.insert(tk.END, "-" * 50 + "\n")

def main():
    root = tk.Tk()
    app = RecommenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 