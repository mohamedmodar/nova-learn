import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
from recommender_interface_advanced_v6 import get_hybrid_recommendations_advanced

class RecommenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Enhanced Course Recommender System")
        self.root.geometry("1000x700")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic Search Tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="🔍 Basic Search")
        
        # Advanced Settings Tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="⚙️ Advanced Settings")
        
        # Setup Basic Search Tab
        self.setup_basic_tab(basic_frame)
        
        # Setup Advanced Settings Tab
        self.setup_advanced_tab(advanced_frame)
        
        # Results area (spans both tabs)
        results_frame = ttk.Frame(root)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Search button
        search_button = ttk.Button(results_frame, text="🔍 Search Recommendations", command=self.search)
        search_button.pack(pady=5)
        
        # Status bar for feedback
        self.status_var = tk.StringVar(value="Ready to search...")
        status_label = ttk.Label(results_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.pack(fill=tk.X, pady=2)
        
        # Results area
        ttk.Label(results_frame, text="📚 Recommendations:").pack(anchor=tk.W, pady=(5,0))
        self.results_text = scrolledtext.ScrolledText(results_frame, width=100, height=25, font=('Consolas', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def setup_basic_tab(self, frame):
        # Main container
        main_container = ttk.Frame(frame, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # Query input
        ttk.Label(main_container, text="🔍 Search Query:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.query_entry = ttk.Entry(main_container, width=60, font=('Arial', 10))
        self.query_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(main_container, text="e.g., 'machine learning for beginners'", foreground='gray').grid(row=row, column=3, sticky=tk.W, padx=5)
        row += 1
        
        # Level selection
        ttk.Label(main_container, text="📈 Experience Level:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.level_var = tk.StringVar(value="All Levels")
        level_combo = ttk.Combobox(main_container, textvariable=self.level_var, font=('Arial', 10))
        level_combo['values'] = ('All Levels', 'Beginner', 'Intermediate', 'Advanced')
        level_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Skills input
        ttk.Label(main_container, text="💼 Skills (comma-separated):", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.skills_entry = ttk.Entry(main_container, width=60, font=('Arial', 10))
        self.skills_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(main_container, text="e.g., 'python, data analysis, statistics'", foreground='gray').grid(row=row, column=3, sticky=tk.W, padx=5)
        row += 1
        
        # Duration preference
        ttk.Label(main_container, text="⏱️ Duration Preference:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.duration_var = tk.StringVar(value="any")
        duration_combo = ttk.Combobox(main_container, textvariable=self.duration_var, font=('Arial', 10))
        duration_combo['values'] = ('any', 'short', 'medium', 'long')
        duration_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(main_container, text="short: ≤10h, medium: 10-50h, long: >50h", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Model selection
        ttk.Label(main_container, text="🤖 AI Model:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.model_var = tk.StringVar(value="hybrid")
        model_combo = ttk.Combobox(main_container, textvariable=self.model_var, font=('Arial', 10))
        model_combo['values'] = ('hybrid', 'tfidf', 'sbert', 'two_tower')
        model_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Label(main_container, text="hybrid: combines all models", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        
    def setup_advanced_tab(self, frame):
        # Main container
        main_container = ttk.Frame(frame, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # AI Enhancement Features
        ttk.Label(main_container, text="🧠 AI Enhancement Features", font=('Arial', 12, 'bold')).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(10,5), padx=5)
        row += 1
        
        # Enable diversity
        self.diversity_var = tk.BooleanVar(value=True)
        diversity_check = ttk.Checkbutton(main_container, text="🌈 Enable Diversity (avoid too similar courses)", 
                                        variable=self.diversity_var)
        diversity_check.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2, padx=20)
        row += 1
        
        # Enable fuzzy skills
        self.fuzzy_skills_var = tk.BooleanVar(value=True)
        fuzzy_check = ttk.Checkbutton(main_container, text="🔗 Enable Semantic Skill Matching (e.g., 'ML' matches 'Machine Learning')", 
                                    variable=self.fuzzy_skills_var)
        fuzzy_check.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2, padx=20)
        row += 1
        
        # Enable personalization
        self.personalization_var = tk.BooleanVar(value=True)
        personalization_check = ttk.Checkbutton(main_container, text="👤 Enable Intent-Based Personalization (adapts to your learning goals)", 
                                               variable=self.personalization_var)
        personalization_check.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2, padx=20)
        row += 1
        
        # Number of results
        ttk.Label(main_container, text="📊 Number of Results:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,5), padx=5)
        self.num_results_var = tk.IntVar(value=5)
        results_spin = ttk.Spinbox(main_container, from_=1, to=20, textvariable=self.num_results_var, 
                                 width=10)
        results_spin.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        
    def search(self):
        try:
            self.status_var.set("🔄 Searching for recommendations...")
            self.root.update()
            
            # Get input values
            query = self.query_entry.get().strip()
            level = self.level_var.get()
            skills_input = self.skills_entry.get().strip()
            skills = [s.strip().lower() for s in skills_input.split(',')] if skills_input else None
            duration = self.duration_var.get()
            model_type = self.model_var.get()
            
            # Advanced settings
            enable_diversity = self.diversity_var.get()
            enable_fuzzy_skills = self.fuzzy_skills_var.get()
            enable_personalization = self.personalization_var.get()
            num_results = self.num_results_var.get()
            
            print(f"Search parameters: query='{query}', skills={skills}, level={level}")
            print(f"Advanced: diversity={enable_diversity}, fuzzy={enable_fuzzy_skills}, personalization={enable_personalization}")
            
            # Get recommendations with all enhancements
            results = get_hybrid_recommendations_advanced(
                query_text=query if query else None,
                level=level if level != 'All Levels' else None,
                skills=skills,
                duration_pref=duration if duration != 'any' else None,
                model_type=model_type,
                top_n=num_results,
                enable_diversity=enable_diversity,
                enable_fuzzy_skills=enable_fuzzy_skills,
                enable_personalization=enable_personalization
            )
            
            # Display results
            self.display_results(results, query, skills, level)
            
        except Exception as e:
            self.status_var.set(f"❌ Error: {str(e)}")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"An error occurred: {str(e)}")
            print(f"Error in search: {e}")
            
    def display_results(self, results, query, skills, level):
        self.results_text.delete(1.0, tk.END)
        
        if results.empty:
            self.status_var.set("❌ No recommendations found")
            self.results_text.insert(tk.END, "🚫 No recommendations found.\n\nTry:\n")
            self.results_text.insert(tk.END, "• Broadening your search terms\n")
            self.results_text.insert(tk.END, "• Enabling semantic skill matching\n")
            self.results_text.insert(tk.END, "• Changing experience level to 'All Levels'\n")
        else:
            self.status_var.set(f"✅ Found {len(results)} recommendations")
            
            # Header
            self.results_text.insert(tk.END, f"🎯 SEARCH RESULTS ({len(results)} courses found)\n")
            self.results_text.insert(tk.END, "=" * 80 + "\n\n")
            
            for i, (_, row) in enumerate(results.iterrows(), 1):
                # Course header
                self.results_text.insert(tk.END, f"📚 {i}. {row['title']}\n")
                self.results_text.insert(tk.END, f"🏢 Provider: {row['provider'] if pd.notna(row['provider']) else 'N/A'}\n")
                self.results_text.insert(tk.END, f"📈 Level: {row['level'] if pd.notna(row['level']) else 'N/A'}\n")
                
                # Skills with emoji
                if 'skills_list' in row and row['skills_list'] and isinstance(row['skills_list'], list):
                    skills_str = ", ".join(row['skills_list'][:5])  # Limit display
                    if len(row['skills_list']) > 5:
                        skills_str += f" (+{len(row['skills_list'])-5} more)"
                    self.results_text.insert(tk.END, f"💼 Skills: {skills_str}\n")
                
                # Course details
                rating = row['adjusted_rating']
                if pd.notna(rating) and isinstance(rating, (int, float)):
                    self.results_text.insert(tk.END, f"⭐ Rating: {rating:.2f}\n")
                else:
                    self.results_text.insert(tk.END, f"⭐ Rating: N/A\n")
                
                duration = row['duration']
                if pd.notna(duration):
                    self.results_text.insert(tk.END, f"⏱️ Duration: {duration} hours\n")
                else:
                    self.results_text.insert(tk.END, f"⏱️ Duration: N/A\n")
                
                # Difficulty score if available
                if 'difficulty_score' in row and pd.notna(row['difficulty_score']):
                    difficulty = row['difficulty_score']
                    difficulty_emoji = "🟢" if difficulty <= 2 else "🟡" if difficulty <= 3.5 else "🔴"
                    self.results_text.insert(tk.END, f"🎯 Difficulty: {difficulty_emoji} {difficulty:.1f}/5.0\n")
                
                # AI Scores
                scores = []
                for score_col, score_label in [('tfidf_score', 'TF-IDF'), ('sbert_score', 'SBERT'), 
                                              ('two_tower_score', 'Two-Tower'), ('combined_score', 'Combined')]:
                    if score_col in row and pd.notna(row[score_col]):
                        score_val = row[score_col]
                        if isinstance(score_val, (int, float)) and score_val > 0:
                            scores.append(f"{score_label}: {score_val:.3f}")
                
                if scores:
                    score_line = "🤖 AI Scores: " + " | ".join(scores)
                    self.results_text.insert(tk.END, score_line + "\n")
                
                # Description (truncated)
                if 'description' in row and pd.notna(row['description']):
                    desc = str(row['description'])[:200]
                    if len(str(row['description'])) > 200:
                        desc += "..."
                    self.results_text.insert(tk.END, f"📝 Description: {desc}\n")
                
                # URL
                self.results_text.insert(tk.END, f"🔗 URL: {row['url'] if pd.notna(row['url']) else 'N/A'}\n")
                self.results_text.insert(tk.END, "\n" + "-" * 80 + "\n\n")

def main():
    root = tk.Tk()
    app = RecommenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 