# Learning Platform Recommender System

A sophisticated recommender system for learning platforms that combines content-based filtering and two-tower neural network approaches to provide personalized course recommendations.

## Features

- Content-based filtering using TF-IDF and SBERT embeddings
- Two-tower neural network model for personalized recommendations
- Hybrid recommendation approach combining multiple strategies
- Advanced evaluation metrics and analysis
- GUI interface for easy interaction
- Cold-start handling strategies
- Comprehensive evaluation metrics including:
  - Provider diversity analysis
  - Similarity score comparisons
  - Overlap ratio analysis
  - Visual evaluation metrics

## Project Structure

### Core Components
- `adapted_two_tower_model.py`: Implementation of the two-tower neural network model
- `evaluate_two_tower.py`: Evaluation scripts with comprehensive metrics
- `recommender_interface_advanced_v6.py`: Core recommendation logic and interface
- `hybrid_recommender_logic.py`: Implementation of hybrid recommendation approach
- `sbert_recommender_component.py`: SBERT-based content filtering component
- `recommender_gui.py`: GUI interface for the recommender system

### Model Files
- `two_tower.weights.h5`: Pre-trained two-tower model weights
- `tfidf_vectorizer.pkl`: TF-IDF vectorizer for content-based filtering
- `tfidf_matrix.pkl`: Pre-computed TF-IDF matrix
- `course_sbert_embeddings.pkl`: Pre-computed SBERT embeddings
- `training_history.pkl`: Training history for the model

### Evaluation Results
- `evaluation_metrics.png`: Visualization of model performance metrics
- `two_tower_evaluation_results.csv`: Detailed evaluation results

### Data
- `cleaned_courses_with_enhanced_skills.csv`: Processed course data

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure all model files are present in the project directory:
- `two_tower.weights.h5`
- `tfidf_vectorizer.pkl`
- `tfidf_matrix.pkl`
- `course_sbert_embeddings.pkl`
- `training_history.pkl`

3. Run the GUI:
```bash
python recommender_gui.py
```

## Data Structure

The system uses processed course data from `cleaned_courses_with_enhanced_skills.csv`, which contains:
- Course titles and descriptions
- Enhanced skill tags
- Course metadata
- User interaction data

## Model Architecture

The recommender system uses a hybrid approach combining:
1. Content-based filtering using TF-IDF and SBERT embeddings
2. Two-tower neural network for personalized recommendations
3. Hybrid logic to combine and rank recommendations

## Evaluation Results

The system has been evaluated across multiple categories including Programming Languages, Data Science & AI, Web Development, Cloud & DevOps, Mobile Development, Database, and Security. Key metrics include:

- Average overlap ratio: 7.14%
- Average Two-Tower similarity score: 0.4560
- Average SBERT similarity score: 0.7398
- Average Two-Tower provider diversity: 1.75
- Average SBERT provider diversity: 1.32

The Two-Tower model shows better provider diversity while SBERT maintains higher similarity scores, providing complementary recommendations.

## Running Evaluations

To run the evaluation script:
```bash
python evaluate_two_tower.py
```

This will:
1. Generate comprehensive evaluation metrics
2. Create visualization plots in `evaluation_metrics.png`
3. Save detailed results to `two_tower_evaluation_results.csv`

## License

This project is licensed under the MIT License - see the LICENSE file for details. 