#!/usr/bin/env python3
"""
A0 Poster Visualization Generator
Generates high-resolution charts from all_issues_for_test.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300  # High resolution for printing
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'sans-serif'

def load_data(filepath='all_issues_for_test.csv'):
    """Load and return the issues dataset"""
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} issues")
    return df

def create_status_pie_chart(df, output_file='status_distribution.png'):
    """Create a pie chart showing issue status distribution"""
    print("Creating status distribution chart...")
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    status_counts = df['status'].value_counts()
    colors = sns.color_palette('Set2', len(status_counts))
    
    wedges, texts, autotexts = ax.pie(
        status_counts.values,
        labels=status_counts.index,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        textprops={'fontsize': 14, 'weight': 'bold'}
    )
    
    ax.set_title('Issue Status Distribution', fontsize=18, weight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def create_top_authors_chart(df, top_n=15, output_file='top_authors.png'):
    """Create a bar chart showing top authors by number of issues"""
    print(f"Creating top {top_n} authors chart...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    author_counts = df['author'].value_counts().head(top_n)
    
    bars = ax.barh(range(len(author_counts)), author_counts.values)
    ax.set_yticks(range(len(author_counts)))
    ax.set_yticklabels(author_counts.index)
    ax.set_xlabel('Number of Issues', fontsize=14, weight='bold')
    ax.set_title(f'Top {top_n} Contributors by Issue Count', fontsize=18, weight='bold', pad=20)
    
    # Color bars with gradient
    colors = plt.cm.viridis(range(len(author_counts)))
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    # Add value labels
    for i, v in enumerate(author_counts.values):
        ax.text(v + 0.5, i, str(v), va='center', fontsize=10)
    
    ax.invert_yaxis()  # Highest at top
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def create_summary_stats(df, output_file='summary_stats.png'):
    """Create a visual summary of key statistics"""
    print("Creating summary statistics visual...")
    
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.axis('off')
    
    # Calculate statistics
    total_issues = len(df)
    unique_authors = df['author'].nunique()
    closed_issues = len(df[df['status'] == 'Closed'])
    open_issues = len(df[df['status'] != 'Closed'])
    
    # Create stat boxes
    stats = [
        ('Total Issues', total_issues, '#3498db'),
        ('Unique Authors', unique_authors, '#2ecc71'),
        ('Closed Issues', closed_issues, '#27ae60'),
        ('Open Issues', open_issues, '#e74c3c'),
    ]
    
    x_positions = [0.15, 0.40, 0.65, 0.90]
    
    for (label, value, color), x_pos in zip(stats, x_positions):
        # Draw rectangle
        rect = plt.Rectangle((x_pos - 0.1, 0.3), 0.2, 0.4, 
                            facecolor=color, alpha=0.3, 
                            edgecolor=color, linewidth=3)
        ax.add_patch(rect)
        
        # Add text
        ax.text(x_pos, 0.6, str(value), 
               ha='center', va='center', 
               fontsize=32, weight='bold', color=color)
        ax.text(x_pos, 0.35, label, 
               ha='center', va='center', 
               fontsize=12, weight='bold')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_file}")
    plt.close()

def create_subject_word_frequency(df, top_n=20, output_file='common_words.png'):
    """Create a bar chart of most common words in issue subjects"""
    print("Analyzing common words in subjects...")
    
    # Extract all words from subjects
    all_words = []
    stopwords = {'a', 'an', 'the', 'to', 'in', 'for', 'of', 'and', 'or', 'is', 'it', 
                 'on', 'with', 'as', 'be', 'at', 'by', 'from', 'not', 'are', 'that'}
    
    for subject in df['subject'].dropna():
        words = str(subject).lower().split()
        all_words.extend([w for w in words if len(w) > 3 and w not in stopwords])
    
    word_counts = Counter(all_words).most_common(top_n)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    words, counts = zip(*word_counts)
    
    bars = ax.barh(range(len(words)), counts)
    ax.set_yticks(range(len(words)))
    ax.set_yticklabels(words)
    ax.set_xlabel('Frequency', fontsize=14, weight='bold')
    ax.set_title(f'Top {top_n} Keywords in Issue Subjects', fontsize=18, weight='bold', pad=20)
    
    # Color bars
    colors = plt.cm.plasma(range(len(words)))
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    # Add value labels
    for i, v in enumerate(counts):
        ax.text(v + 0.5, i, str(v), va='center', fontsize=10)
    
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def create_relationship_analysis(df, output_file='relationship_stats.png'):
    """Analyze and visualize issue relationships"""
    print("Analyzing issue relationships...")
    
    # Count issues with relationships
    has_relationships = df['related issues'].notna().sum()
    no_relationships = df['related issues'].isna().sum()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie chart of relationship presence
    ax1.pie(
        [has_relationships, no_relationships],
        labels=['Has Relations', 'No Relations'],
        autopct='%1.1f%%',
        colors=['#3498db', '#95a5a6'],
        startangle=90,
        textprops={'fontsize': 12, 'weight': 'bold'}
    )
    ax1.set_title('Issues with Related Issues', fontsize=16, weight='bold')
    
    # Count relationship types
    relationship_types = []
    for relations in df['related issues'].dropna():
        if isinstance(relations, str):
            # Extract relationship types (e.g., "Is duplicate of", "Blocks")
            parts = relations.split(',')
            for part in parts:
                rel_type = part.split('#')[0].strip()
                if rel_type:
                    relationship_types.append(rel_type)
    
    if relationship_types:
        rel_counts = Counter(relationship_types).most_common(10)
        rel_names, rel_values = zip(*rel_counts)
        
        bars = ax2.barh(range(len(rel_names)), rel_values)
        ax2.set_yticks(range(len(rel_names)))
        ax2.set_yticklabels(rel_names, fontsize=10)
        ax2.set_xlabel('Count', fontsize=12, weight='bold')
        ax2.set_title('Relationship Types', fontsize=16, weight='bold')
        
        # Color bars
        colors = plt.cm.Set3(range(len(rel_names)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax2.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def create_all_visualizations(csv_file='all_issues_for_test.csv'):
    """Generate all visualizations"""
    print("\n" + "="*60)
    print("A0 Poster Visualization Generator")
    print("="*60 + "\n")
    
    # Load data
    df = load_data(csv_file)
    
    print(f"\nDataset Preview:")
    print(f"Columns: {', '.join(df.columns.tolist())}")
    print(f"\nGenerating visualizations...\n")
    
    # Generate all charts
    create_summary_stats(df)
    create_status_pie_chart(df)
    create_top_authors_chart(df)
    create_subject_word_frequency(df)
    create_relationship_analysis(df)
    
    print("\n" + "="*60)
    print("✓ All visualizations generated successfully!")
    print("="*60)
    print("\nGenerated files:")
    print("  - summary_stats.png")
    print("  - status_distribution.png")
    print("  - top_authors.png")
    print("  - common_words.png")
    print("  - relationship_stats.png")
    print("\nThese images are print-ready at 300 DPI.")
    print("Import them into your poster design software.")
    print("="*60 + "\n")

if __name__ == "__main__":
    create_all_visualizations()
