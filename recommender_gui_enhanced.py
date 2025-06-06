import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
from recommender_interface_advanced_v6 import get_hybrid_recommendations_advanced

class EnhancedRecommenderGUI:
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
        notebook.add(advanced_frame, text="⚙️ Advanced AI Features")
        
        # Setup tabs
        self.setup_basic_tab(basic_frame)
        self.setup_advanced_tab(advanced_frame)
        
        # Results area
        results_frame = ttk.Frame(root)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Search button with style
        search_button = ttk.Button(results_frame, text="🔍 Search Recommendations", command=self.search)
        search_button.pack(pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to search...")
        status_label = ttk.Label(results_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.pack(fill=tk.X, pady=2)
        
        # Results area
        ttk.Label(results_frame, text="📚 Recommendations:").pack(anchor=tk.W, pady=(5,0))
        self.results_text = scrolledtext.ScrolledText(results_frame, width=100, height=25, font=('Consolas', 9))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def setup_basic_tab(self, frame):
        main_container = ttk.Frame(frame, padding="15")
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
        ttk.Label(main_container, text="hybrid: combines all models intelligently", foreground='gray').grid(row=row, column=2, sticky=tk.W, padx=5)
        
    def setup_advanced_tab(self, frame):
        main_container = ttk.Frame(frame, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # AI Enhancement Features Section
        enhancement_frame = ttk.LabelFrame(main_container, text="🧠 AI Enhancement Features", padding="10")
        enhancement_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Enable diversity
        self.diversity_var = tk.BooleanVar(value=True)
        diversity_check = ttk.Checkbutton(enhancement_frame, text="🌈 Enable Diversity (avoid too similar courses)", 
                                        variable=self.diversity_var, font=('Arial', 10))
        diversity_check.pack(anchor=tk.W, pady=2)
        
        # Enable fuzzy skills
        self.fuzzy_skills_var = tk.BooleanVar(value=True)
        fuzzy_check = ttk.Checkbutton(enhancement_frame, text="🔗 Enable Semantic Skill Matching (e.g., 'ML' matches 'Machine Learning')", 
                                    variable=self.fuzzy_skills_var, font=('Arial', 10))
        fuzzy_check.pack(anchor=tk.W, pady=2)
        
        # Enable personalization
        self.personalization_var = tk.BooleanVar(value=True)
        personalization_check = ttk.Checkbutton(enhancement_frame, text="👤 Enable Intent-Based Personalization (adapts to your learning goals)", 
                                               variable=self.personalization_var, font=('Arial', 10))
        personalization_check.pack(anchor=tk.W, pady=2)
        
        row += 1
        
        # Search Configuration Section
        config_frame = ttk.LabelFrame(main_container, text="⚙️ Search Configuration", padding="10")
        config_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Number of results
        results_frame = ttk.Frame(config_frame)
        results_frame.pack(fill=tk.X, pady=2)
        ttk.Label(results_frame, text="📊 Number of Results:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.num_results_var = tk.IntVar(value=5)
        results_spin = ttk.Spinbox(results_frame, from_=1, to=20, textvariable=self.num_results_var, 
                                 width=10, font=('Arial', 10))
        results_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        row += 1
        
        # Feature Explanation Section
        explanation_frame = ttk.LabelFrame(main_container, text="ℹ️ What These Features Do", padding="10")
        explanation_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        explanations = [
            "🌈 Diversity: Ensures recommendations aren't too similar to each other",
            "🔗 Semantic Matching: Understands that 'Python' and 'Python Programming' are the same",
            "👤 Personalization: Analyzes your query to understand your learning goals and urgency",
            "🤖 Hybrid Model: Combines TF-IDF, SBERT, and Two-Tower models with adaptive weighting"
        ]
        
        for explanation in explanations:
            ttk.Label(explanation_frame, text=explanation, font=('Arial', 9), foreground='darkblue').pack(anchor=tk.W, pady=1)
        
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
            
            print(f"🔍 Search: query='{query}', skills={skills}, level={level}")
            print(f"🎛️ Advanced: diversity={enable_diversity}, fuzzy={enable_fuzzy_skills}, personalization={enable_personalization}")
            
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
            self.results_text.insert(tk.END, "🚫 No recommendations found.\n\n")
            self.results_text.insert(tk.END, "💡 Try these suggestions:\n")
            self.results_text.insert(tk.END, "• Broaden your search terms\n")
            self.results_text.insert(tk.END, "• Enable semantic skill matching in Advanced tab\n")
            self.results_text.insert(tk.END, "• Change experience level to 'All Levels'\n")
            self.results_text.insert(tk.END, "• Try different keywords\n")
        else:
            self.status_var.set(f"✅ Found {len(results)} high-quality recommendations")
            
            # Header with AI features info
            features_used = []
            if self.diversity_var.get():
                features_used.append("Diversity")
            if self.fuzzy_skills_var.get():
                features_used.append("Semantic Matching")
            if self.personalization_var.get():
                features_used.append("Personalization")
            
            self.results_text.insert(tk.END, f"🎯 ENHANCED SEARCH RESULTS ({len(results)} courses)\n")
            self.results_text.insert(tk.END, f"🤖 AI Features: {', '.join(features_used)}\n")
            self.results_text.insert(tk.END, "=" * 80 + "\n\n")
            
            for i, (_, row) in enumerate(results.iterrows(), 1):
                # Course header with enhanced display
                self.results_text.insert(tk.END, f"📚 {i}. {row['title']}\n")
                self.results_text.insert(tk.END, f"🏢 Provider: {row['provider'] if pd.notna(row['provider']) else 'N/A'}\n")
                self.results_text.insert(tk.END, f"📈 Level: {row['level'] if pd.notna(row['level']) else 'N/A'}\n")
                
                # Enhanced skills display
                if 'skills_list' in row and row['skills_list'] and isinstance(row['skills_list'], list):
                    skills_str = ", ".join(row['skills_list'][:5])
                    if len(row['skills_list']) > 5:
                        skills_str += f" (+{len(row['skills_list'])-5} more)"
                    self.results_text.insert(tk.END, f"💼 Skills: {skills_str}\n")
                
                # Course quality indicators
                self.results_text.insert(tk.END, f"⭐ Rating: {row['adjusted_rating']:.2f if pd.notna(row['adjusted_rating']) else 'N/A'}\n")
                self.results_text.insert(tk.END, f"⏱️ Duration: {row['duration'] if pd.notna(row['duration']) else 'N/A'} hours\n")
                
                # NEW: Difficulty indicator
                if 'difficulty_score' in row and pd.notna(row['difficulty_score']):
                    difficulty = row['difficulty_score']
                    if difficulty <= 2:
                        difficulty_emoji = "🟢 Easy"
                    elif difficulty <= 3.5:
                        difficulty_emoji = "🟡 Medium"
                    else:
                        difficulty_emoji = "🔴 Advanced"
                    self.results_text.insert(tk.END, f"🎯 Difficulty: {difficulty_emoji} ({difficulty:.1f}/5.0)\n")
                
                # Enhanced AI scoring display
                score_info = []
                if 'tfidf_score' in row and pd.notna(row['tfidf_score']) and row['tfidf_score'] > 0:
                    score_info.append(f"TF-IDF: {row['tfidf_score']:.3f}")
                if 'sbert_score' in row and pd.notna(row['sbert_score']) and row['sbert_score'] > 0:
                    score_info.append(f"SBERT: {row['sbert_score']:.3f}")
                if 'two_tower_score' in row and pd.notna(row['two_tower_score']) and row['two_tower_score'] > 0:
                    score_info.append(f"Two-Tower: {row['two_tower_score']:.3f}")
                if 'combined_score' in row and pd.notna(row['combined_score']) and row['combined_score'] > 0:
                    score_info.append(f"Combined: {row['combined_score']:.3f}")
                
                if score_info:
                    self.results_text.insert(tk.END, f"🤖 AI Scores: {' | '.join(score_info)}\n")
                
                # Description (smart truncation)
                if 'description' in row and pd.notna(row['description']):
                    desc = str(row['description'])
                    if len(desc) > 200:
                        desc = desc[:200] + "..."
                    self.results_text.insert(tk.END, f"📝 Description: {desc}\n")
                
                # URL
                self.results_text.insert(tk.END, f"🔗 URL: {row['url'] if pd.notna(row['url']) else 'N/A'}\n")
                self.results_text.insert(tk.END, "\n" + "-" * 80 + "\n\n")

def main():
    root = tk.Tk()
    app = EnhancedRecommenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 